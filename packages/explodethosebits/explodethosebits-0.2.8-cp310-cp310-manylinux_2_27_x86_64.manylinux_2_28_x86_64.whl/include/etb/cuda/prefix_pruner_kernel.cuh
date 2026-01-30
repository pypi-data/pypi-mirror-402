#ifndef ETB_PREFIX_PRUNER_KERNEL_CUH
#define ETB_PREFIX_PRUNER_KERNEL_CUH

#include "cuda_common.cuh"
#include "gpu_memory.cuh"

namespace etb {
namespace cuda {

/**
 * Shared memory structure for prefix pruning operations.
 */
struct PrefixPrunerSharedMem {
    // Warp voting results
    uint32_t warp_votes[8];  // 8 warps per block max
    
    // Prefix being evaluated
    uint8_t current_prefix[16];
    uint32_t prefix_length;
    
    // Trie navigation state
    uint32_t current_node_idx;
    DevicePrefixStatus current_status;
    float current_score;
};

/**
 * Prefix pruner CUDA kernel.
 * 
 * Implements warp-level voting for termination decisions and
 * atomic trie updates for prefix status.
 * 
 * Requirements: 9.8
 * 
 * @param prefix_trie Prefix trie nodes
 * @param trie_size Number of nodes in trie
 * @param prefixes Array of prefixes to evaluate
 * @param prefix_lengths Array of prefix lengths
 * @param scores Array of heuristic scores for each prefix
 * @param num_prefixes Number of prefixes to evaluate
 * @param prune_threshold Score threshold for pruning
 * @param prune_results Output array indicating if each prefix was pruned
 */
__global__ void prefix_pruner_kernel(
    DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    const float* scores,
    uint32_t num_prefixes,
    float prune_threshold,
    bool* prune_results
);

/**
 * Trie lookup kernel.
 * Looks up prefixes in the trie and returns their status.
 * 
 * @param prefix_trie Prefix trie nodes
 * @param trie_size Number of nodes in trie
 * @param prefixes Array of prefixes to look up
 * @param prefix_lengths Array of prefix lengths
 * @param num_prefixes Number of prefixes
 * @param statuses Output array of prefix statuses
 * @param scores Output array of best scores
 */
__global__ void trie_lookup_kernel(
    const DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    uint32_t num_prefixes,
    DevicePrefixStatus* statuses,
    float* scores
);

/**
 * Trie insert/update kernel.
 * Inserts or updates prefixes in the trie.
 * 
 * @param prefix_trie Prefix trie nodes
 * @param trie_size Current number of nodes
 * @param max_trie_size Maximum trie capacity
 * @param prefixes Array of prefixes to insert
 * @param prefix_lengths Array of prefix lengths
 * @param statuses Array of statuses to set
 * @param scores Array of scores to set
 * @param num_prefixes Number of prefixes
 * @param new_trie_size Output: new trie size after insertions
 */
__global__ void trie_insert_kernel(
    DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    uint32_t max_trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    const DevicePrefixStatus* statuses,
    const float* scores,
    uint32_t num_prefixes,
    uint32_t* new_trie_size
);

/**
 * Batch prune check kernel.
 * Checks if prefixes should be pruned based on ancestor status.
 * 
 * @param prefix_trie Prefix trie nodes
 * @param trie_size Number of nodes
 * @param prefixes Array of prefixes to check
 * @param prefix_lengths Array of prefix lengths
 * @param num_prefixes Number of prefixes
 * @param should_skip Output array indicating if prefix should be skipped
 */
__global__ void batch_prune_check_kernel(
    const DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    uint32_t num_prefixes,
    bool* should_skip
);

/**
 * Host-side launcher for prefix pruner kernels.
 */
class PrefixPrunerKernel {
public:
    PrefixPrunerKernel();
    ~PrefixPrunerKernel();
    
    /**
     * Configure the kernel for a specific device.
     * @param device_id CUDA device ID
     */
    void configure(int device_id);
    
    /**
     * Evaluate and prune prefixes.
     * @param trie Device prefix trie
     * @param trie_size Number of trie nodes
     * @param prefixes Device array of prefixes (flattened)
     * @param prefix_lengths Device array of prefix lengths
     * @param scores Device array of heuristic scores
     * @param num_prefixes Number of prefixes
     * @param prune_threshold Score threshold for pruning
     * @param prune_results Device array for results
     * @param stream CUDA stream
     */
    void evaluate_and_prune(DevicePrefixTrieNode* trie, uint32_t trie_size,
                            const uint8_t* prefixes, const uint32_t* prefix_lengths,
                            const float* scores, uint32_t num_prefixes,
                            float prune_threshold, bool* prune_results,
                            cudaStream_t stream = nullptr);
    
    /**
     * Look up prefix statuses.
     * @param trie Device prefix trie
     * @param trie_size Number of trie nodes
     * @param prefixes Device array of prefixes
     * @param prefix_lengths Device array of prefix lengths
     * @param num_prefixes Number of prefixes
     * @param statuses Device array for output statuses
     * @param scores Device array for output scores
     * @param stream CUDA stream
     */
    void lookup(const DevicePrefixTrieNode* trie, uint32_t trie_size,
                const uint8_t* prefixes, const uint32_t* prefix_lengths,
                uint32_t num_prefixes, DevicePrefixStatus* statuses,
                float* scores, cudaStream_t stream = nullptr);
    
    /**
     * Check if prefixes should be skipped due to pruned ancestors.
     * @param trie Device prefix trie
     * @param trie_size Number of trie nodes
     * @param prefixes Device array of prefixes
     * @param prefix_lengths Device array of prefix lengths
     * @param num_prefixes Number of prefixes
     * @param should_skip Device array for output flags
     * @param stream CUDA stream
     */
    void check_pruned(const DevicePrefixTrieNode* trie, uint32_t trie_size,
                      const uint8_t* prefixes, const uint32_t* prefix_lengths,
                      uint32_t num_prefixes, bool* should_skip,
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
 * Navigate trie to find node for a prefix.
 * Returns node index or UINT32_MAX if not found.
 */
__device__ inline uint32_t find_prefix_node(
    const DevicePrefixTrieNode* trie,
    uint32_t trie_size,
    const uint8_t* prefix,
    uint32_t prefix_length
) {
    if (trie_size == 0 || prefix_length == 0) {
        return 0;  // Root node
    }
    
    uint32_t current = 0;  // Start at root
    
    for (uint32_t i = 0; i < prefix_length; ++i) {
        uint8_t byte_val = prefix[i];
        uint32_t children_offset = trie[current].children_offset;
        
        if (children_offset == 0) {
            return UINT32_MAX;  // No children, prefix not found
        }
        
        // Look for child with matching byte value
        bool found = false;
        for (uint32_t c = 0; c < 256 && children_offset + c < trie_size; ++c) {
            uint32_t child_idx = children_offset + c;
            if (child_idx < trie_size && trie[child_idx].reconstructed_byte == byte_val) {
                current = child_idx;
                found = true;
                break;
            }
        }
        
        if (!found) {
            return UINT32_MAX;
        }
    }
    
    return current;
}

/**
 * Check if any ancestor of a prefix is pruned.
 */
__device__ inline bool is_ancestor_pruned(
    const DevicePrefixTrieNode* trie,
    uint32_t trie_size,
    const uint8_t* prefix,
    uint32_t prefix_length
) {
    if (trie_size == 0) return false;
    
    uint32_t current = 0;
    
    for (uint32_t i = 0; i < prefix_length; ++i) {
        // Check current node status
        if (trie[current].status == DevicePrefixStatus::PRUNED) {
            return true;
        }
        
        uint8_t byte_val = prefix[i];
        uint32_t children_offset = trie[current].children_offset;
        
        if (children_offset == 0) {
            return false;  // No more nodes to check
        }
        
        // Find child
        bool found = false;
        for (uint32_t c = 0; c < 256 && children_offset + c < trie_size; ++c) {
            uint32_t child_idx = children_offset + c;
            if (child_idx < trie_size && trie[child_idx].reconstructed_byte == byte_val) {
                current = child_idx;
                found = true;
                break;
            }
        }
        
        if (!found) {
            return false;
        }
    }
    
    // Check final node
    return trie[current].status == DevicePrefixStatus::PRUNED;
}

/**
 * Atomically update node status.
 */
__device__ inline void atomic_update_status(
    DevicePrefixTrieNode* node,
    DevicePrefixStatus new_status
) {
    // Use atomicCAS on the status byte
    uint8_t* status_ptr = reinterpret_cast<uint8_t*>(&node->status);
    uint8_t old_val = *status_ptr;
    uint8_t new_val = static_cast<uint8_t>(new_status);
    
    // Only update if transitioning to a "more final" state
    // UNKNOWN -> VALID or PRUNED is allowed
    // VALID -> PRUNED is allowed
    // PRUNED is final
    if (old_val == static_cast<uint8_t>(DevicePrefixStatus::PRUNED)) {
        return;  // Already pruned, don't change
    }
    
    atomicCAS(reinterpret_cast<unsigned int*>(status_ptr), 
              static_cast<unsigned int>(old_val),
              static_cast<unsigned int>(new_val));
}

/**
 * Atomically update best score (only if new score is higher).
 */
__device__ inline void atomic_update_score(
    DevicePrefixTrieNode* node,
    float new_score
) {
    // Use atomicMax on the score
    // Since atomicMax doesn't work directly on floats, we use a CAS loop
    float* score_ptr = &node->best_score;
    float old_score = *score_ptr;
    
    while (new_score > old_score) {
        float assumed = old_score;
        old_score = __int_as_float(atomicCAS(
            reinterpret_cast<int*>(score_ptr),
            __float_as_int(assumed),
            __float_as_int(new_score)
        ));
        
        if (old_score == assumed) {
            break;  // Successfully updated
        }
    }
}

/**
 * Warp-level vote for pruning decision.
 * Returns true if majority of warp votes to prune.
 */
__device__ inline bool warp_vote_prune(bool should_prune) {
    unsigned int vote = __ballot_sync(0xFFFFFFFF, should_prune);
    return __popc(vote) > 16;  // More than half
}

/**
 * Increment visit count atomically.
 */
__device__ inline void atomic_increment_visit(DevicePrefixTrieNode* node) {
    atomicAdd(&node->visit_count, 1);
}

} // namespace cuda
} // namespace etb

#endif // ETB_PREFIX_PRUNER_KERNEL_CUH
