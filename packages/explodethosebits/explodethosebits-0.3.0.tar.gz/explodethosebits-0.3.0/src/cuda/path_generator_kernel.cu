#include "etb/cuda/path_generator_kernel.cuh"

namespace etb {
namespace cuda {

// ============================================================================
// Kernel Implementation
// ============================================================================

__global__ void init_work_queue_kernel(
    PathWorkItem* work_queue,
    uint32_t* work_queue_tail,
    uint32_t input_length,
    uint8_t bit_mask
) {
    uint32_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Each thread initializes work items for one starting byte position
    if (tid < input_length) {
        int allowed_bits = count_allowed_bits(bit_mask);
        
        // Create work items for each allowed bit position at this byte
        for (int b = 0; b < allowed_bits; ++b) {
            uint8_t bit_pos = get_nth_allowed_bit(bit_mask, b);
            
            PathWorkItem item;
            item.start_byte = tid;
            item.current_depth = 0;
            item.prefix_length = 0;
            item.current_score = 0.5f;  // Neutral starting score
            
            // Push to global queue
            uint32_t idx = atomicAdd(work_queue_tail, 1);
            if (idx < input_length * 8) {  // Reasonable limit
                work_queue[idx] = item;
            }
        }
    }
}

/**
 * OPTIMIZED path generator kernel with:
 * - Lock-free work stealing using proper CAS semantics
 * - Warp-cooperative path exploration
 * - Better memory coalescing for bit extraction
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
) {
    // Shared memory for cooperative exploration
    __shared__ PathGeneratorSharedMem smem;
    __shared__ uint32_t shared_work_count;
    __shared__ bool block_has_work;
    
    const uint32_t tid = threadIdx.x;
    const uint32_t warp_id = tid / 32;
    const uint32_t lane_id = tid % 32;
    const uint32_t block_id = blockIdx.x;
    
    // Initialize shared memory
    if (tid == 0) {
        smem.local_work_head = 0;
        smem.local_work_tail = 0;
        smem.shared_prefix_length = 0;
        shared_work_count = 0;
        block_has_work = true;
    }
    __syncthreads();
    
    // Work stealing loop with proper lock-free semantics
    while (block_has_work) {
        PathWorkItem current_item;
        bool got_work = false;
        
        // Phase 1: Try local queue first (warp 0 manages this)
        if (warp_id == 0 && lane_id == 0) {
            uint32_t local_head = smem.local_work_head;
            uint32_t local_tail = smem.local_work_tail;
            
            if (local_head < local_tail) {
                current_item = smem.local_work_items[local_head % 32];
                smem.local_work_head = local_head + 1;
                got_work = true;
            }
        }
        
        // Broadcast local work status to warp
        got_work = __shfl_sync(0xFFFFFFFF, got_work ? 1 : 0, 0);
        
        // Phase 2: If no local work, steal from global queue
        if (!got_work) {
            // Lock-free steal: read head, check against tail, CAS to claim
            if (lane_id == 0) {
                uint32_t old_head, current_tail;
                bool success = false;
                
                // Retry loop for CAS
                for (int retry = 0; retry < 3 && !success; ++retry) {
                    old_head = *work_queue_head;
                    current_tail = *work_queue_tail;
                    
                    if (old_head < current_tail) {
                        // Try to claim this slot
                        uint32_t claimed = atomicCAS(work_queue_head, old_head, old_head + 1);
                        if (claimed == old_head) {
                            current_item = work_queue[old_head % config.batch_size];
                            success = true;
                        }
                    } else {
                        break;  // Queue empty
                    }
                }
                got_work = success;
            }
            
            got_work = __shfl_sync(0xFFFFFFFF, got_work ? 1 : 0, 0);
        }
        
        // Sync block to check if anyone has work
        __syncthreads();
        if (tid == 0) {
            // Check if any warp got work
            block_has_work = got_work;
        }
        __syncthreads();
        
        if (!block_has_work) {
            break;  // No more work available
        }
        
        // Broadcast current item to all lanes in warp
        // Use shared memory for cross-warp communication
        if (warp_id == 0) {
            if (lane_id == 0 && got_work) {
                // Store item for other warps to read
                smem.local_work_items[0] = current_item;
            }
            __syncwarp();
            current_item = smem.local_work_items[0];
        }
        __syncthreads();
        
        // All threads now have the same work item
        // Process the work item cooperatively
        uint32_t current_byte = current_item.start_byte + current_item.current_depth;
        
        if (current_byte >= config.input_length) {
            // Path complete - evaluate as candidate
            if (warp_id == 0 && lane_id == 0) {
                if (current_item.prefix_length > 0 && 
                    current_item.current_score > *min_score) {
                    
                    uint32_t cand_idx = atomicAdd(candidate_count, 1);
                    if (cand_idx < config.batch_size) {
                        DeviceCandidate& cand = candidates[cand_idx];
                        cand.data_length = current_item.prefix_length;
                        cand.composite_score = current_item.current_score;
                    }
                }
            }
            continue;
        }
        
        // Check early stopping conditions using warp vote
        bool should_stop = false;
        
        if (current_item.prefix_length >= config.early_stopping.level1_bytes) {
            // Warp-cooperative check for repeated bytes
            uint8_t first_byte = current_item.prefix_bytes[0];
            bool my_match = (lane_id < current_item.prefix_length) ? 
                (current_item.prefix_bytes[lane_id] == first_byte) : true;
            
            unsigned int all_same_mask = __ballot_sync(0xFFFFFFFF, my_match);
            bool all_same = (all_same_mask == 0xFFFFFFFF);
            
            if (all_same || current_item.current_score < config.early_stopping.prune_threshold) {
                should_stop = true;
            }
        }
        
        // Warp vote on termination
        if (warp_vote_terminate(should_stop)) {
            continue;
        }
        
        // Generate child work items - warp-cooperative
        int allowed_bits = count_allowed_bits(config.bit_pruning.bit_mask);
        
        // Coalesced bit extraction: all lanes read the same byte, extract different bits
        uint8_t input_byte = input_data[current_byte];
        
        if (lane_id < static_cast<uint32_t>(allowed_bits)) {
            uint8_t bit_pos = get_nth_allowed_bit(config.bit_pruning.bit_mask, lane_id);
            uint8_t bit_value = (input_byte >> bit_pos) & 1;
            
            // Create child work item
            PathWorkItem child = current_item;
            child.current_depth++;
            
            uint8_t bit_idx = current_item.current_depth % 8;
            child.bit_selections[bit_idx] = bit_value;
            
            if (bit_idx == 7) {
                uint8_t new_byte = reconstruct_byte(child.bit_selections);
                if (child.prefix_length < 16) {
                    child.prefix_bytes[child.prefix_length] = new_byte;
                    child.prefix_length++;
                }
            }
            
            // Push to global queue (local queue is for single-item broadcast)
            push_work(work_queue, work_queue_tail, config.batch_size, child);
        }
        
        __syncwarp();
    }
}

// ============================================================================
// Host-side Launcher Implementation
// ============================================================================

PathGeneratorKernel::PathGeneratorKernel() : configured_(false) {}

PathGeneratorKernel::~PathGeneratorKernel() {}

void PathGeneratorKernel::configure(int device_id) {
    kernel_config_ = get_optimal_config(device_id, 65536, sizeof(PathGeneratorSharedMem));
    configured_ = true;
}

void PathGeneratorKernel::init_work_queue(GPUMemoryManager& mem, uint32_t input_length,
                                           uint8_t bit_mask, cudaStream_t stream) {
    if (!configured_) {
        configure(0);
    }
    
    // Reset work queue pointers
    uint32_t zero = 0;
    ETB_CUDA_CHECK(cudaMemcpy(mem.get_work_queue_head().data(), &zero, 
                              sizeof(uint32_t), cudaMemcpyHostToDevice));
    ETB_CUDA_CHECK(cudaMemcpy(mem.get_work_queue_tail().data(), &zero,
                              sizeof(uint32_t), cudaMemcpyHostToDevice));
    
    // Launch initialization kernel
    int threads = 256;
    int blocks = (input_length + threads - 1) / threads;
    
    init_work_queue_kernel<<<blocks, threads, 0, stream>>>(
        reinterpret_cast<PathWorkItem*>(mem.get_work_queue().data()),
        mem.get_work_queue_tail().data(),
        input_length,
        bit_mask
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

void PathGeneratorKernel::launch(GPUMemoryManager& mem, const PathGeneratorConfig& config,
                                  cudaStream_t stream) {
    if (!configured_) {
        configure(0);
    }
    
    // Calculate grid dimensions
    int threads = kernel_config_.threads_per_block;
    int blocks = kernel_config_.blocks_per_grid;
    size_t shared_mem = sizeof(PathGeneratorSharedMem);
    
    path_generator_kernel<<<blocks, threads, shared_mem, stream>>>(
        mem.get_device_input().data(),
        config,
        reinterpret_cast<PathWorkItem*>(mem.get_work_queue().data()),
        mem.get_work_queue_head().data(),
        mem.get_work_queue_tail().data(),
        mem.get_prefix_trie().data(),
        mem.get_candidate_queue().data(),
        mem.get_candidate_count().data(),
        mem.get_min_score().data()
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

} // namespace cuda
} // namespace etb
