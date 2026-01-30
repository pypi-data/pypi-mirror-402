#include "etb/cuda/prefix_pruner_kernel.cuh"

namespace etb {
namespace cuda {

// ============================================================================
// Kernel Implementations
// ============================================================================

__global__ void prefix_pruner_kernel(
    DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    const float* scores,
    uint32_t num_prefixes,
    float prune_threshold,
    bool* prune_results
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    const uint32_t lane_id = threadIdx.x % 32;
    
    if (tid >= num_prefixes) return;
    
    // Get this thread's prefix
    uint32_t prefix_offset = 0;
    for (uint32_t i = 0; i < tid; ++i) {
        prefix_offset += prefix_lengths[i];
    }
    
    const uint8_t* my_prefix = prefixes + prefix_offset;
    uint32_t my_length = prefix_lengths[tid];
    float my_score = scores[tid];
    
    // Check if already pruned by ancestor
    if (is_ancestor_pruned(prefix_trie, trie_size, my_prefix, my_length)) {
        prune_results[tid] = true;
        return;
    }
    
    // Find or navigate to the node for this prefix
    uint32_t node_idx = find_prefix_node(prefix_trie, trie_size, my_prefix, my_length);
    
    if (node_idx == UINT32_MAX || node_idx >= trie_size) {
        // Node doesn't exist yet - can't prune what doesn't exist
        prune_results[tid] = false;
        return;
    }
    
    // Determine if this prefix should be pruned
    bool should_prune = my_score < prune_threshold;
    
    // Warp-level voting for consensus (optional - can help reduce noise)
    // For now, we use individual decisions
    
    if (should_prune) {
        // Mark node as pruned
        atomic_update_status(&prefix_trie[node_idx], DevicePrefixStatus::PRUNED);
        prune_results[tid] = true;
    } else {
        // Mark as valid and update score
        atomic_update_status(&prefix_trie[node_idx], DevicePrefixStatus::VALID);
        atomic_update_score(&prefix_trie[node_idx], my_score);
        prune_results[tid] = false;
    }
    
    // Increment visit count
    atomic_increment_visit(&prefix_trie[node_idx]);
}

__global__ void trie_lookup_kernel(
    const DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    uint32_t num_prefixes,
    DevicePrefixStatus* statuses,
    float* scores
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (tid >= num_prefixes) return;
    
    // Calculate prefix offset
    uint32_t prefix_offset = 0;
    for (uint32_t i = 0; i < tid; ++i) {
        prefix_offset += prefix_lengths[i];
    }
    
    const uint8_t* my_prefix = prefixes + prefix_offset;
    uint32_t my_length = prefix_lengths[tid];
    
    // Find node
    uint32_t node_idx = find_prefix_node(prefix_trie, trie_size, my_prefix, my_length);
    
    if (node_idx == UINT32_MAX || node_idx >= trie_size) {
        statuses[tid] = DevicePrefixStatus::UNKNOWN;
        scores[tid] = 0.0f;
    } else {
        statuses[tid] = prefix_trie[node_idx].status;
        scores[tid] = prefix_trie[node_idx].best_score;
    }
}

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
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (tid >= num_prefixes) return;
    
    // Calculate prefix offset
    uint32_t prefix_offset = 0;
    for (uint32_t i = 0; i < tid; ++i) {
        prefix_offset += prefix_lengths[i];
    }
    
    const uint8_t* my_prefix = prefixes + prefix_offset;
    uint32_t my_length = prefix_lengths[tid];
    DevicePrefixStatus my_status = statuses[tid];
    float my_score = scores[tid];
    
    // Navigate/create path to this prefix
    uint32_t current = 0;  // Root
    
    for (uint32_t i = 0; i < my_length; ++i) {
        uint8_t byte_val = my_prefix[i];
        uint32_t children_offset = prefix_trie[current].children_offset;
        
        // If no children yet, allocate space
        if (children_offset == 0) {
            // Atomically allocate children block
            uint32_t new_offset = atomicAdd(new_trie_size, 256);
            
            if (new_offset + 256 > max_trie_size) {
                // Out of space
                return;
            }
            
            // Try to set children_offset (may race with other threads)
            atomicCAS(&prefix_trie[current].children_offset, 0, new_offset);
            children_offset = prefix_trie[current].children_offset;
            
            // Initialize new children nodes
            for (uint32_t c = 0; c < 256; ++c) {
                uint32_t child_idx = children_offset + c;
                if (child_idx < max_trie_size) {
                    prefix_trie[child_idx].reconstructed_byte = static_cast<uint8_t>(c);
                    prefix_trie[child_idx].status = DevicePrefixStatus::UNKNOWN;
                    prefix_trie[child_idx].best_score = 0.0f;
                    prefix_trie[child_idx].children_offset = 0;
                    prefix_trie[child_idx].visit_count = 0;
                }
            }
        }
        
        // Navigate to child
        uint32_t child_idx = children_offset + byte_val;
        if (child_idx >= max_trie_size) {
            return;  // Out of bounds
        }
        
        current = child_idx;
    }
    
    // Update the final node
    atomic_update_status(&prefix_trie[current], my_status);
    atomic_update_score(&prefix_trie[current], my_score);
    atomic_increment_visit(&prefix_trie[current]);
}

__global__ void batch_prune_check_kernel(
    const DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    uint32_t num_prefixes,
    bool* should_skip
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (tid >= num_prefixes) return;
    
    // Calculate prefix offset
    uint32_t prefix_offset = 0;
    for (uint32_t i = 0; i < tid; ++i) {
        prefix_offset += prefix_lengths[i];
    }
    
    const uint8_t* my_prefix = prefixes + prefix_offset;
    uint32_t my_length = prefix_lengths[tid];
    
    // Check if any ancestor is pruned
    should_skip[tid] = is_ancestor_pruned(prefix_trie, trie_size, my_prefix, my_length);
}

// ============================================================================
// Host-side Launcher Implementation
// ============================================================================

PrefixPrunerKernel::PrefixPrunerKernel() : configured_(false) {}

PrefixPrunerKernel::~PrefixPrunerKernel() {}

void PrefixPrunerKernel::configure(int device_id) {
    kernel_config_ = get_optimal_config(device_id, 65536, sizeof(PrefixPrunerSharedMem));
    configured_ = true;
}

void PrefixPrunerKernel::evaluate_and_prune(
    DevicePrefixTrieNode* trie, uint32_t trie_size,
    const uint8_t* prefixes, const uint32_t* prefix_lengths,
    const float* scores, uint32_t num_prefixes,
    float prune_threshold, bool* prune_results,
    cudaStream_t stream
) {
    if (!configured_) {
        configure(0);
    }
    
    int threads = kernel_config_.threads_per_block;
    int blocks = (num_prefixes + threads - 1) / threads;
    
    prefix_pruner_kernel<<<blocks, threads, 0, stream>>>(
        trie, trie_size, prefixes, prefix_lengths, scores,
        num_prefixes, prune_threshold, prune_results
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

void PrefixPrunerKernel::lookup(
    const DevicePrefixTrieNode* trie, uint32_t trie_size,
    const uint8_t* prefixes, const uint32_t* prefix_lengths,
    uint32_t num_prefixes, DevicePrefixStatus* statuses,
    float* scores, cudaStream_t stream
) {
    if (!configured_) {
        configure(0);
    }
    
    int threads = kernel_config_.threads_per_block;
    int blocks = (num_prefixes + threads - 1) / threads;
    
    trie_lookup_kernel<<<blocks, threads, 0, stream>>>(
        trie, trie_size, prefixes, prefix_lengths,
        num_prefixes, statuses, scores
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

void PrefixPrunerKernel::check_pruned(
    const DevicePrefixTrieNode* trie, uint32_t trie_size,
    const uint8_t* prefixes, const uint32_t* prefix_lengths,
    uint32_t num_prefixes, bool* should_skip,
    cudaStream_t stream
) {
    if (!configured_) {
        configure(0);
    }
    
    int threads = kernel_config_.threads_per_block;
    int blocks = (num_prefixes + threads - 1) / threads;
    
    batch_prune_check_kernel<<<blocks, threads, 0, stream>>>(
        trie, trie_size, prefixes, prefix_lengths,
        num_prefixes, should_skip
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

} // namespace cuda
} // namespace etb
