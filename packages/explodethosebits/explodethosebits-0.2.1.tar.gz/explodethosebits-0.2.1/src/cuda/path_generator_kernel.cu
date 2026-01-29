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
    
    const uint32_t tid = threadIdx.x;
    const uint32_t warp_id = tid / 32;
    const uint32_t lane_id = tid % 32;
    const uint32_t block_id = blockIdx.x;
    
    // Initialize shared memory
    if (tid == 0) {
        smem.local_work_head = 0;
        smem.local_work_tail = 0;
        smem.shared_prefix_length = 0;
    }
    __syncthreads();
    
    // Work stealing loop
    bool has_work = true;
    PathWorkItem current_item;
    
    while (has_work) {
        // Try to get work from local queue first
        bool got_local_work = false;
        if (lane_id == 0) {
            uint32_t local_head = atomicAdd(&smem.local_work_head, 1);
            if (local_head < smem.local_work_tail) {
                current_item = smem.local_work_items[local_head % 32];
                got_local_work = true;
            } else {
                atomicSub(&smem.local_work_head, 1);
            }
        }
        
        // Broadcast result to warp
        got_local_work = __shfl_sync(0xFFFFFFFF, got_local_work ? 1 : 0, 0);
        
        if (!got_local_work) {
            // Try to steal from global queue
            if (lane_id == 0) {
                has_work = steal_work(work_queue, work_queue_head, work_queue_tail,
                                      config.batch_size, current_item);
            }
            has_work = __shfl_sync(0xFFFFFFFF, has_work ? 1 : 0, 0);
            
            if (!has_work) {
                break;  // No more work available
            }
        }
        
        // Broadcast current item to all lanes
        // (In practice, we'd use shared memory for this)
        
        // Process the work item
        uint32_t current_byte = current_item.start_byte + current_item.current_depth;
        
        if (current_byte >= config.input_length) {
            // Path complete - evaluate as candidate
            if (current_item.prefix_length > 0 && 
                current_item.current_score > *min_score) {
                
                // Try to add to candidate queue
                uint32_t cand_idx = atomicAdd(candidate_count, 1);
                if (cand_idx < config.batch_size) {
                    DeviceCandidate& cand = candidates[cand_idx];
                    cand.data_length = current_item.prefix_length;
                    cand.composite_score = current_item.current_score;
                    // Note: actual data would need separate allocation
                }
            }
            continue;
        }
        
        // Check early stopping conditions
        bool should_stop = false;
        
        // Level 1: Check at 4 bytes
        if (current_item.prefix_length >= config.early_stopping.level1_bytes) {
            // Check for repeated bytes (all same value)
            bool all_same = true;
            uint8_t first_byte = current_item.prefix_bytes[0];
            for (uint8_t i = 1; i < current_item.prefix_length && all_same; ++i) {
                if (current_item.prefix_bytes[i] != first_byte) {
                    all_same = false;
                }
            }
            
            if (all_same) {
                should_stop = true;
            }
            
            // Check score threshold
            if (current_item.current_score < config.early_stopping.prune_threshold) {
                should_stop = true;
            }
        }
        
        // Warp vote on termination
        if (warp_vote_terminate(should_stop)) {
            continue;  // Skip this path
        }
        
        // Generate child work items for each allowed bit position
        int allowed_bits = count_allowed_bits(config.bit_pruning.bit_mask);
        
        // Each lane handles a different bit position
        if (lane_id < static_cast<uint32_t>(allowed_bits)) {
            uint8_t bit_pos = get_nth_allowed_bit(config.bit_pruning.bit_mask, lane_id);
            uint8_t bit_value = extract_bit(input_data, current_byte, bit_pos);
            
            // Create child work item
            PathWorkItem child = current_item;
            child.current_depth++;
            
            // Update bit selections
            uint8_t bit_idx = current_item.current_depth % 8;
            child.bit_selections[bit_idx] = bit_value;
            
            // If we've collected 8 bits, reconstruct a byte
            if (bit_idx == 7) {
                uint8_t new_byte = reconstruct_byte(child.bit_selections);
                if (child.prefix_length < 16) {
                    child.prefix_bytes[child.prefix_length] = new_byte;
                    child.prefix_length++;
                }
            }
            
            // Push to local queue if space available
            uint32_t local_idx = atomicAdd(&smem.local_work_tail, 1);
            if (local_idx < 32) {
                smem.local_work_items[local_idx] = child;
            } else {
                atomicSub(&smem.local_work_tail, 1);
                // Push to global queue instead
                push_work(work_queue, work_queue_tail, config.batch_size, child);
            }
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
