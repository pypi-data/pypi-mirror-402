#include "etb/cuda/prefix_pruner_kernel.cuh"
#include <vector>

namespace etb {
namespace cuda {

// ============================================================================
// Kernel Implementations
// ============================================================================

/**
 * OPTIMIZED: Now takes pre-computed prefix offsets instead of O(n²) loop.
 * Host should compute prefix_offsets using exclusive_scan(prefix_lengths).
 */
__global__ void prefix_pruner_kernel(
    DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    const uint32_t* prefix_offsets,  // NEW: Pre-computed prefix sum
    const float* scores,
    uint32_t num_prefixes,
    float prune_threshold,
    bool* prune_results
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    const uint32_t lane_id = threadIdx.x % 32;
    
    if (tid >= num_prefixes) return;
    
    // O(1) lookup instead of O(n) loop per thread
    const uint8_t* my_prefix = prefixes + prefix_offsets[tid];
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

/**
 * OPTIMIZED: Uses pre-computed prefix offsets.
 */
__global__ void trie_lookup_kernel(
    const DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    const uint32_t* prefix_offsets,  // NEW: Pre-computed prefix sum
    uint32_t num_prefixes,
    DevicePrefixStatus* statuses,
    float* scores
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (tid >= num_prefixes) return;
    
    // O(1) lookup
    const uint8_t* my_prefix = prefixes + prefix_offsets[tid];
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

/**
 * OPTIMIZED: Warp-cooperative trie insertion with batched allocation.
 * - Uses pre-computed prefix offsets
 * - Warp-level cooperative allocation reduces atomic contention
 * - Coalesced child initialization
 */
__global__ void trie_insert_kernel(
    DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    uint32_t max_trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    const uint32_t* prefix_offsets,  // NEW: Pre-computed prefix sum
    const DevicePrefixStatus* statuses,
    const float* scores,
    uint32_t num_prefixes,
    uint32_t* new_trie_size
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    const uint32_t lane_id = threadIdx.x % 32;
    const uint32_t warp_id = tid / 32;
    
    if (tid >= num_prefixes) return;
    
    // O(1) lookup
    const uint8_t* my_prefix = prefixes + prefix_offsets[tid];
    uint32_t my_length = prefix_lengths[tid];
    DevicePrefixStatus my_status = statuses[tid];
    float my_score = scores[tid];
    
    // Navigate/create path to this prefix
    uint32_t current = 0;  // Root
    
    for (uint32_t i = 0; i < my_length; ++i) {
        uint8_t byte_val = my_prefix[i];
        uint32_t children_offset = prefix_trie[current].children_offset;
        
        // If no children yet, use warp-cooperative allocation
        if (children_offset == 0) {
            // Warp-level: check which lanes need allocation at this node
            unsigned int need_alloc_mask = __ballot_sync(0xFFFFFFFF, 
                prefix_trie[current].children_offset == 0);
            
            // Only first lane in warp that needs allocation does the atomic
            int first_lane = __ffs(need_alloc_mask) - 1;
            uint32_t new_offset = 0;
            
            if (lane_id == first_lane) {
                new_offset = atomicAdd(new_trie_size, 256);
                if (new_offset + 256 <= max_trie_size) {
                    // Try to set children_offset
                    atomicCAS(&prefix_trie[current].children_offset, 0, new_offset);
                }
            }
            
            // Broadcast the result to all lanes
            new_offset = __shfl_sync(0xFFFFFFFF, new_offset, first_lane);
            
            if (new_offset + 256 > max_trie_size) {
                return;  // Out of space
            }
            
            children_offset = prefix_trie[current].children_offset;
            
            // Warp-cooperative child initialization (32 threads init 256 nodes = 8 each)
            if (children_offset == new_offset) {  // We won the CAS
                for (uint32_t c = lane_id; c < 256; c += 32) {
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
            __syncwarp();
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

/**
 * OPTIMIZED: Uses pre-computed prefix offsets.
 */
__global__ void batch_prune_check_kernel(
    const DevicePrefixTrieNode* prefix_trie,
    uint32_t trie_size,
    const uint8_t* prefixes,
    const uint32_t* prefix_lengths,
    const uint32_t* prefix_offsets,  // NEW: Pre-computed prefix sum
    uint32_t num_prefixes,
    bool* should_skip
) {
    const uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (tid >= num_prefixes) return;
    
    // O(1) lookup
    const uint8_t* my_prefix = prefixes + prefix_offsets[tid];
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

/**
 * Helper: Compute exclusive prefix sum on host.
 * This is O(n) and done once on CPU before kernel launch.
 */
static void compute_prefix_offsets(
    const uint32_t* prefix_lengths,
    uint32_t num_prefixes,
    std::vector<uint32_t>& offsets
) {
    offsets.resize(num_prefixes);
    uint32_t sum = 0;
    for (uint32_t i = 0; i < num_prefixes; ++i) {
        offsets[i] = sum;
        sum += prefix_lengths[i];
    }
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
    
    // Download prefix_lengths to compute offsets on host
    std::vector<uint32_t> h_lengths(num_prefixes);
    ETB_CUDA_CHECK(cudaMemcpy(h_lengths.data(), prefix_lengths, 
                              num_prefixes * sizeof(uint32_t), cudaMemcpyDeviceToHost));
    
    // Compute prefix offsets on CPU - O(n) instead of O(n²) on GPU
    std::vector<uint32_t> h_offsets;
    compute_prefix_offsets(h_lengths.data(), num_prefixes, h_offsets);
    
    // Upload offsets to device
    uint32_t* d_offsets;
    ETB_CUDA_CHECK(cudaMalloc(&d_offsets, num_prefixes * sizeof(uint32_t)));
    ETB_CUDA_CHECK(cudaMemcpy(d_offsets, h_offsets.data(), 
                              num_prefixes * sizeof(uint32_t), cudaMemcpyHostToDevice));
    
    int threads = kernel_config_.threads_per_block;
    int blocks = (num_prefixes + threads - 1) / threads;
    
    prefix_pruner_kernel<<<blocks, threads, 0, stream>>>(
        trie, trie_size, prefixes, prefix_lengths, d_offsets, scores,
        num_prefixes, prune_threshold, prune_results
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
    
    // Free temporary offset buffer
    ETB_CUDA_CHECK(cudaFree(d_offsets));
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
    
    // Compute prefix offsets
    std::vector<uint32_t> h_lengths(num_prefixes);
    ETB_CUDA_CHECK(cudaMemcpy(h_lengths.data(), prefix_lengths,
                              num_prefixes * sizeof(uint32_t), cudaMemcpyDeviceToHost));
    
    std::vector<uint32_t> h_offsets;
    compute_prefix_offsets(h_lengths.data(), num_prefixes, h_offsets);
    
    uint32_t* d_offsets;
    ETB_CUDA_CHECK(cudaMalloc(&d_offsets, num_prefixes * sizeof(uint32_t)));
    ETB_CUDA_CHECK(cudaMemcpy(d_offsets, h_offsets.data(),
                              num_prefixes * sizeof(uint32_t), cudaMemcpyHostToDevice));
    
    int threads = kernel_config_.threads_per_block;
    int blocks = (num_prefixes + threads - 1) / threads;
    
    trie_lookup_kernel<<<blocks, threads, 0, stream>>>(
        trie, trie_size, prefixes, prefix_lengths, d_offsets,
        num_prefixes, statuses, scores
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
    ETB_CUDA_CHECK(cudaFree(d_offsets));
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
    
    // Compute prefix offsets
    std::vector<uint32_t> h_lengths(num_prefixes);
    ETB_CUDA_CHECK(cudaMemcpy(h_lengths.data(), prefix_lengths,
                              num_prefixes * sizeof(uint32_t), cudaMemcpyDeviceToHost));
    
    std::vector<uint32_t> h_offsets;
    compute_prefix_offsets(h_lengths.data(), num_prefixes, h_offsets);
    
    uint32_t* d_offsets;
    ETB_CUDA_CHECK(cudaMalloc(&d_offsets, num_prefixes * sizeof(uint32_t)));
    ETB_CUDA_CHECK(cudaMemcpy(d_offsets, h_offsets.data(),
                              num_prefixes * sizeof(uint32_t), cudaMemcpyHostToDevice));
    
    int threads = kernel_config_.threads_per_block;
    int blocks = (num_prefixes + threads - 1) / threads;
    
    batch_prune_check_kernel<<<blocks, threads, 0, stream>>>(
        trie, trie_size, prefixes, prefix_lengths, d_offsets,
        num_prefixes, should_skip
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
    ETB_CUDA_CHECK(cudaFree(d_offsets));
}

} // namespace cuda
} // namespace etb
