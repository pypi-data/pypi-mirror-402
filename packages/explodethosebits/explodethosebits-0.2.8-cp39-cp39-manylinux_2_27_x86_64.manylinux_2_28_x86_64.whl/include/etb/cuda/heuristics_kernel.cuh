#ifndef ETB_HEURISTICS_KERNEL_CUH
#define ETB_HEURISTICS_KERNEL_CUH

#include "cuda_common.cuh"
#include "gpu_memory.cuh"

namespace etb {
namespace cuda {

/**
 * Shared memory structure for heuristics calculation.
 * Uses shared memory histogram for efficient entropy calculation.
 */
struct HeuristicsSharedMem {
    // Histogram for byte frequency (256 bins)
    uint32_t histogram[256];
    
    // Reduction scratch space
    float reduction_scratch[256];
    
    // Partial results
    uint32_t printable_count;
    uint32_t control_count;
    uint32_t null_run_max;
    uint32_t current_null_run;
    uint32_t utf8_valid_count;
    uint32_t utf8_total_count;
};

/**
 * Heuristics CUDA kernel.
 * 
 * Calculates Shannon entropy, byte distribution, and other heuristics
 * using shared memory histogram and warp-level reductions.
 * 
 * Requirements: 9.3
 * 
 * @param data Input byte data
 * @param length Length of data
 * @param weights Heuristic weights
 * @param result Output heuristic result
 */
__global__ void heuristics_kernel(
    const uint8_t* data,
    uint32_t length,
    DeviceHeuristicWeights weights,
    DeviceHeuristicResult* result
);

/**
 * Batch heuristics kernel for evaluating multiple byte sequences.
 * 
 * @param data_ptrs Array of pointers to byte sequences
 * @param lengths Array of sequence lengths
 * @param num_sequences Number of sequences to evaluate
 * @param weights Heuristic weights
 * @param results Output array of heuristic results
 */
__global__ void batch_heuristics_kernel(
    const uint8_t** data_ptrs,
    const uint32_t* lengths,
    uint32_t num_sequences,
    DeviceHeuristicWeights weights,
    DeviceHeuristicResult* results
);

/**
 * Inline heuristics evaluation for use within other kernels.
 * Uses warp-level operations for efficiency.
 * 
 * @param data Byte data (in registers or shared memory)
 * @param length Length of data (max 32 for inline evaluation)
 * @param weights Heuristic weights
 * @return Heuristic result
 */
__device__ DeviceHeuristicResult evaluate_heuristics_inline(
    const uint8_t* data,
    uint32_t length,
    const DeviceHeuristicWeights& weights
);

/**
 * Host-side launcher for heuristics kernel.
 */
class HeuristicsKernel {
public:
    HeuristicsKernel();
    ~HeuristicsKernel();
    
    /**
     * Configure the kernel for a specific device.
     * @param device_id CUDA device ID
     */
    void configure(int device_id);
    
    /**
     * Evaluate heuristics for a single byte sequence.
     * @param data Device pointer to byte data
     * @param length Length of data
     * @param weights Heuristic weights
     * @param result Device pointer to result
     * @param stream CUDA stream
     */
    void evaluate(const uint8_t* data, uint32_t length,
                  const DeviceHeuristicWeights& weights,
                  DeviceHeuristicResult* result,
                  cudaStream_t stream = nullptr);
    
    /**
     * Evaluate heuristics for multiple byte sequences.
     * @param data_ptrs Device array of pointers to byte sequences
     * @param lengths Device array of sequence lengths
     * @param num_sequences Number of sequences
     * @param weights Heuristic weights
     * @param results Device array of results
     * @param stream CUDA stream
     */
    void evaluate_batch(const uint8_t** data_ptrs, const uint32_t* lengths,
                        uint32_t num_sequences,
                        const DeviceHeuristicWeights& weights,
                        DeviceHeuristicResult* results,
                        cudaStream_t stream = nullptr);
    
    /**
     * Get the kernel configuration.
     */
    const KernelConfig& get_config() const { return kernel_config_; }

private:
    KernelConfig kernel_config_;
    bool configured_;
};

// ============================================================================
// Device Functions
// ============================================================================

/**
 * Check if a byte is printable ASCII (0x20-0x7E).
 */
__device__ inline bool is_printable_ascii(uint8_t byte) {
    return byte >= 0x20 && byte <= 0x7E;
}

/**
 * Check if a byte is a control character (0x00-0x1F, excluding 0x09, 0x0A, 0x0D).
 */
__device__ inline bool is_control_char(uint8_t byte) {
    if (byte > 0x1F) return false;
    if (byte == 0x09 || byte == 0x0A || byte == 0x0D) return false;  // Tab, LF, CR
    return true;
}

/**
 * Calculate entropy contribution for a single bin.
 * Returns -p * log2(p) where p = count / total.
 */
__device__ inline float entropy_contribution(uint32_t count, uint32_t total) {
    if (count == 0 || total == 0) return 0.0f;
    float p = static_cast<float>(count) / static_cast<float>(total);
    return -p * log2f(p);
}

/**
 * Warp-level histogram update using atomics.
 */
__device__ inline void warp_histogram_add(uint32_t* histogram, uint8_t value) {
    atomicAdd(&histogram[value], 1);
}

/**
 * Warp-level reduction for summing histogram entropy.
 */
__device__ inline float warp_reduce_entropy(float* scratch, uint32_t* histogram, 
                                             uint32_t total, int lane_id) {
    // Each lane handles 8 histogram bins (256 / 32 = 8)
    float local_entropy = 0.0f;
    for (int i = 0; i < 8; ++i) {
        int bin = lane_id * 8 + i;
        local_entropy += entropy_contribution(histogram[bin], total);
    }
    
    // Warp reduction
    for (int offset = 16; offset > 0; offset /= 2) {
        local_entropy += __shfl_down_sync(0xFFFFFFFF, local_entropy, offset);
    }
    
    return __shfl_sync(0xFFFFFFFF, local_entropy, 0);
}

/**
 * Block-level histogram reduction.
 */
__device__ inline float block_reduce_entropy(float* scratch, uint32_t* histogram,
                                              uint32_t total, int tid, int block_size) {
    // First, each thread handles some bins
    int bins_per_thread = (256 + block_size - 1) / block_size;
    float local_entropy = 0.0f;
    
    for (int i = 0; i < bins_per_thread; ++i) {
        int bin = tid * bins_per_thread + i;
        if (bin < 256) {
            local_entropy += entropy_contribution(histogram[bin], total);
        }
    }
    
    // Store to shared memory
    scratch[tid] = local_entropy;
    __syncthreads();
    
    // Tree reduction
    for (int stride = block_size / 2; stride > 0; stride /= 2) {
        if (tid < stride) {
            scratch[tid] += scratch[tid + stride];
        }
        __syncthreads();
    }
    
    return scratch[0];
}

/**
 * Validate UTF-8 byte sequence.
 * Returns the number of valid UTF-8 code points found.
 */
__device__ inline void validate_utf8_byte(uint8_t byte, int& state, 
                                           uint32_t& valid_count, uint32_t& total_count) {
    // UTF-8 state machine
    // state: 0 = expecting start byte, 1-3 = expecting continuation bytes
    
    if (state == 0) {
        total_count++;
        if ((byte & 0x80) == 0) {
            // ASCII (0xxxxxxx)
            valid_count++;
        } else if ((byte & 0xE0) == 0xC0) {
            // 2-byte sequence start (110xxxxx)
            state = 1;
        } else if ((byte & 0xF0) == 0xE0) {
            // 3-byte sequence start (1110xxxx)
            state = 2;
        } else if ((byte & 0xF8) == 0xF0) {
            // 4-byte sequence start (11110xxx)
            state = 3;
        }
        // Invalid start byte - don't increment valid_count
    } else {
        // Expecting continuation byte (10xxxxxx)
        if ((byte & 0xC0) == 0x80) {
            state--;
            if (state == 0) {
                valid_count++;  // Complete valid sequence
            }
        } else {
            // Invalid continuation - reset state
            state = 0;
            total_count++;  // Count this as a new character
        }
    }
}

/**
 * Calculate composite heuristic score.
 */
__device__ inline float calculate_composite_score(
    const DeviceHeuristicResult& result,
    const DeviceHeuristicWeights& weights,
    uint32_t length
) {
    // Normalize entropy to [0, 1] range (max entropy is 8.0)
    float entropy_score = result.entropy / 8.0f;
    
    // Entropy penalty for very high or very low values
    // Ideal range is roughly 3.5-7.0 for most valid data
    if (result.entropy < 0.5f || result.entropy > 7.8f) {
        entropy_score *= 0.5f;  // Penalize extreme values
    }
    
    // Printable ratio is already [0, 1]
    float printable_score = result.printable_ratio;
    
    // Control char penalty (invert - fewer is better)
    float control_score = 1.0f - result.control_char_ratio;
    
    // Null run penalty
    float null_penalty = 1.0f;
    if (length > 0) {
        float null_ratio = static_cast<float>(result.max_null_run) / static_cast<float>(length);
        null_penalty = 1.0f - fminf(null_ratio * 2.0f, 1.0f);  // Penalize long null runs
    }
    
    // UTF-8 validity is already [0, 1]
    float utf8_score = result.utf8_validity;
    
    // Weighted combination
    float composite = 
        weights.entropy_weight * entropy_score +
        weights.printable_weight * printable_score +
        weights.control_char_weight * control_score +
        weights.null_run_weight * null_penalty +
        weights.utf8_weight * utf8_score;
    
    return fminf(fmaxf(composite, 0.0f), 1.0f);
}

} // namespace cuda
} // namespace etb

#endif // ETB_HEURISTICS_KERNEL_CUH
