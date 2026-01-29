#ifndef ETB_PATH_GENERATOR_KERNEL_CUH
#define ETB_PATH_GENERATOR_KERNEL_CUH

#include "cuda_common.cuh"
#include "gpu_memory.cuh"

namespace etb {
namespace cuda {

/**
 * Work item for path generation.
 * Represents a partial path that needs to be explored.
 */
struct PathWorkItem {
    uint32_t start_byte;        // Starting byte index for this work item
    uint32_t current_depth;     // Current depth in the path
    uint8_t prefix_bytes[16];   // Reconstructed bytes so far (max 16 for early stopping)
    uint8_t prefix_length;      // Number of bytes in prefix
    uint8_t bit_selections[16]; // Bit selections made so far
    float current_score;        // Current heuristic score
    
    __host__ __device__ PathWorkItem()
        : start_byte(0), current_depth(0), prefix_length(0), current_score(0.0f) {
        for (int i = 0; i < 16; ++i) {
            prefix_bytes[i] = 0;
            bit_selections[i] = 0;
        }
    }
};

/**
 * Configuration for path generator kernel.
 */
struct PathGeneratorConfig {
    uint32_t input_length;          // Length of input data
    uint32_t max_depth;             // Maximum path depth
    uint32_t batch_size;            // Number of paths to generate per kernel launch
    DeviceBitPruningConfig bit_pruning;
    DeviceEarlyStoppingConfig early_stopping;
    DeviceHeuristicWeights heuristic_weights;
    DeviceScoringWeights scoring_weights;
    
    __host__ __device__ PathGeneratorConfig()
        : input_length(0), max_depth(16), batch_size(65536) {}
};

/**
 * Shared memory structure for path generation.
 * Used for cooperative path exploration within a thread block.
 */
struct PathGeneratorSharedMem {
    // Prefix state shared across warp
    uint8_t shared_prefix[32];
    uint32_t shared_prefix_length;
    
    // Work stealing queue (per-block)
    uint32_t local_work_head;
    uint32_t local_work_tail;
    PathWorkItem local_work_items[32];  // Small local queue
    
    // Reduction scratch space
    float warp_scores[32];
    uint32_t warp_votes[32];
};

/**
 * Path generator CUDA kernel.
 * 
 * Generates paths using work-stealing across thread blocks with
 * warp-level cooperative path exploration.
 * 
 * Requirements: 9.3
 * 
 * @param input_data Input byte array
 * @param config Kernel configuration
 * @param work_queue Global work queue
 * @param work_queue_head Head pointer for work queue
 * @param work_queue_tail Tail pointer for work queue
 * @param prefix_trie Prefix trie for pruning
 * @param candidates Output candidate queue
 * @param candidate_count Number of candidates found
 * @param min_score Minimum score threshold
 */
__global__ void path_generator_kernel(
    const uint8_t* input_data,
    PathGeneratorConfig config,
    PathWorkItem* work_queue,
    uint32_t* work_queue_head,
    uint32_t* work_queue_tail,
    DevicePrefixTrieNode* prefix_trie,
    DeviceCandidate* candidates,
    uint32_t* candidate_count,
    float* min_score
);

/**
 * Initialize work queue with starting positions.
 * 
 * @param work_queue Work queue to initialize
 * @param work_queue_tail Tail pointer
 * @param input_length Length of input data
 * @param bit_mask Bit mask for allowed positions
 */
__global__ void init_work_queue_kernel(
    PathWorkItem* work_queue,
    uint32_t* work_queue_tail,
    uint32_t input_length,
    uint8_t bit_mask
);

/**
 * Host-side launcher for path generator kernel.
 */
class PathGeneratorKernel {
public:
    PathGeneratorKernel();
    ~PathGeneratorKernel();
    
    /**
     * Configure the kernel for a specific device.
     * @param device_id CUDA device ID
     */
    void configure(int device_id);
    
    /**
     * Launch the path generator kernel.
     * @param mem GPU memory manager
     * @param config Kernel configuration
     * @param stream CUDA stream (nullptr for default)
     */
    void launch(GPUMemoryManager& mem, const PathGeneratorConfig& config, 
                cudaStream_t stream = nullptr);
    
    /**
     * Initialize work queue with starting positions.
     * @param mem GPU memory manager
     * @param input_length Length of input data
     * @param bit_mask Bit mask for allowed positions
     * @param stream CUDA stream
     */
    void init_work_queue(GPUMemoryManager& mem, uint32_t input_length,
                         uint8_t bit_mask, cudaStream_t stream = nullptr);
    
    /**
     * Get the kernel configuration.
     */
    const KernelConfig& get_config() const { return kernel_config_; }

private:
    KernelConfig kernel_config_;
    bool configured_;
};

// Device functions for path generation

/**
 * Extract a bit from input data at the given coordinate.
 */
__device__ inline uint8_t extract_bit(const uint8_t* data, uint32_t byte_idx, uint8_t bit_pos) {
    return (data[byte_idx] >> bit_pos) & 1;
}

/**
 * Reconstruct a byte from 8 bit selections.
 */
__device__ inline uint8_t reconstruct_byte(const uint8_t* bits) {
    uint8_t result = 0;
    for (int i = 0; i < 8; ++i) {
        result |= (bits[i] & 1) << i;
    }
    return result;
}

/**
 * Check if a bit position is allowed by the mask.
 */
__device__ inline bool is_bit_allowed(uint8_t bit_pos, uint8_t mask) {
    return (mask >> bit_pos) & 1;
}

/**
 * Count allowed bits in mask.
 */
__device__ inline int count_allowed_bits(uint8_t mask) {
    return __popc(static_cast<unsigned int>(mask));
}

/**
 * Get the nth allowed bit position.
 */
__device__ inline uint8_t get_nth_allowed_bit(uint8_t mask, int n) {
    int count = 0;
    for (uint8_t i = 0; i < 8; ++i) {
        if ((mask >> i) & 1) {
            if (count == n) return i;
            ++count;
        }
    }
    return 0;
}

/**
 * Warp-level vote for early termination.
 * Returns true if majority of warp votes to terminate.
 */
__device__ inline bool warp_vote_terminate(bool should_terminate) {
    unsigned int vote = __ballot_sync(0xFFFFFFFF, should_terminate);
    return __popc(vote) > 16;  // More than half the warp
}

/**
 * Warp-level reduction for finding best score.
 */
__device__ inline float warp_reduce_max(float val) {
    for (int offset = 16; offset > 0; offset /= 2) {
        float other = __shfl_down_sync(0xFFFFFFFF, val, offset);
        val = fmaxf(val, other);
    }
    return __shfl_sync(0xFFFFFFFF, val, 0);
}

/**
 * Atomic work stealing from global queue.
 * Returns true if work was successfully stolen.
 */
__device__ inline bool steal_work(PathWorkItem* work_queue, 
                                   uint32_t* head, uint32_t* tail,
                                   uint32_t queue_capacity,
                                   PathWorkItem& item) {
    uint32_t old_head = atomicAdd(head, 1);
    uint32_t current_tail = *tail;
    
    if (old_head < current_tail) {
        item = work_queue[old_head % queue_capacity];
        return true;
    }
    
    // No work available, restore head
    atomicSub(head, 1);
    return false;
}

/**
 * Push work item to global queue.
 * Returns true if successfully pushed.
 */
__device__ inline bool push_work(PathWorkItem* work_queue,
                                  uint32_t* tail,
                                  uint32_t queue_capacity,
                                  const PathWorkItem& item) {
    uint32_t old_tail = atomicAdd(tail, 1);
    
    if (old_tail < queue_capacity) {
        work_queue[old_tail] = item;
        return true;
    }
    
    // Queue full, restore tail
    atomicSub(tail, 1);
    return false;
}

} // namespace cuda
} // namespace etb

#endif // ETB_PATH_GENERATOR_KERNEL_CUH
