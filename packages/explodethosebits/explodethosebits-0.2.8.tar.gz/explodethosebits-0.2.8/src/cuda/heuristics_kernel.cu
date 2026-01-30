#include "etb/cuda/heuristics_kernel.cuh"

namespace etb {
namespace cuda {

// ============================================================================
// Kernel Implementations
// ============================================================================

__global__ void heuristics_kernel(
    const uint8_t* data,
    uint32_t length,
    DeviceHeuristicWeights weights,
    DeviceHeuristicResult* result
) {
    __shared__ HeuristicsSharedMem smem;
    
    const int tid = threadIdx.x;
    const int block_size = blockDim.x;
    
    // Initialize shared memory
    if (tid < 256) {
        smem.histogram[tid] = 0;
    }
    if (tid == 0) {
        smem.printable_count = 0;
        smem.control_count = 0;
        smem.null_run_max = 0;
        smem.current_null_run = 0;
        smem.utf8_valid_count = 0;
        smem.utf8_total_count = 0;
    }
    __syncthreads();
    
    // Build histogram and count statistics
    // Each thread processes multiple bytes
    uint32_t local_printable = 0;
    uint32_t local_control = 0;
    uint32_t local_null_run = 0;
    uint32_t local_max_null_run = 0;
    
    for (uint32_t i = tid; i < length; i += block_size) {
        uint8_t byte = data[i];
        
        // Update histogram
        atomicAdd(&smem.histogram[byte], 1);
        
        // Count printable ASCII
        if (is_printable_ascii(byte)) {
            local_printable++;
        }
        
        // Count control characters
        if (is_control_char(byte)) {
            local_control++;
        }
        
        // Track null runs (simplified - per-thread tracking)
        if (byte == 0) {
            local_null_run++;
            if (local_null_run > local_max_null_run) {
                local_max_null_run = local_null_run;
            }
        } else {
            local_null_run = 0;
        }
    }
    
    // Reduce printable count
    atomicAdd(&smem.printable_count, local_printable);
    atomicAdd(&smem.control_count, local_control);
    atomicMax(&smem.null_run_max, local_max_null_run);
    
    __syncthreads();
    
    // Calculate entropy using block reduction
    smem.reduction_scratch[tid] = 0.0f;
    __syncthreads();
    
    float entropy = block_reduce_entropy(smem.reduction_scratch, smem.histogram, 
                                          length, tid, block_size);
    
    // UTF-8 validation (sequential for correctness)
    // Only thread 0 does this to maintain state machine consistency
    if (tid == 0) {
        int utf8_state = 0;
        uint32_t valid_count = 0;
        uint32_t total_count = 0;
        
        for (uint32_t i = 0; i < length; ++i) {
            validate_utf8_byte(data[i], utf8_state, valid_count, total_count);
        }
        
        smem.utf8_valid_count = valid_count;
        smem.utf8_total_count = total_count;
    }
    
    __syncthreads();
    
    // Write results (only thread 0)
    if (tid == 0) {
        result->entropy = entropy;
        result->printable_ratio = length > 0 ? 
            static_cast<float>(smem.printable_count) / static_cast<float>(length) : 0.0f;
        result->control_char_ratio = length > 0 ?
            static_cast<float>(smem.control_count) / static_cast<float>(length) : 0.0f;
        result->max_null_run = smem.null_run_max;
        result->utf8_validity = smem.utf8_total_count > 0 ?
            static_cast<float>(smem.utf8_valid_count) / static_cast<float>(smem.utf8_total_count) : 0.0f;
        
        // Calculate composite score
        result->composite_score = calculate_composite_score(*result, weights, length);
    }
}

__global__ void batch_heuristics_kernel(
    const uint8_t** data_ptrs,
    const uint32_t* lengths,
    uint32_t num_sequences,
    DeviceHeuristicWeights weights,
    DeviceHeuristicResult* results
) {
    // Each block handles one sequence
    const uint32_t seq_idx = blockIdx.x;
    
    if (seq_idx >= num_sequences) return;
    
    const uint8_t* data = data_ptrs[seq_idx];
    uint32_t length = lengths[seq_idx];
    DeviceHeuristicResult* result = &results[seq_idx];
    
    __shared__ HeuristicsSharedMem smem;
    
    const int tid = threadIdx.x;
    const int block_size = blockDim.x;
    
    // Initialize shared memory
    if (tid < 256) {
        smem.histogram[tid] = 0;
    }
    if (tid == 0) {
        smem.printable_count = 0;
        smem.control_count = 0;
        smem.null_run_max = 0;
        smem.utf8_valid_count = 0;
        smem.utf8_total_count = 0;
    }
    __syncthreads();
    
    // Build histogram and count statistics
    uint32_t local_printable = 0;
    uint32_t local_control = 0;
    uint32_t local_null_run = 0;
    uint32_t local_max_null_run = 0;
    
    for (uint32_t i = tid; i < length; i += block_size) {
        uint8_t byte = data[i];
        
        atomicAdd(&smem.histogram[byte], 1);
        
        if (is_printable_ascii(byte)) {
            local_printable++;
        }
        
        if (is_control_char(byte)) {
            local_control++;
        }
        
        if (byte == 0) {
            local_null_run++;
            if (local_null_run > local_max_null_run) {
                local_max_null_run = local_null_run;
            }
        } else {
            local_null_run = 0;
        }
    }
    
    atomicAdd(&smem.printable_count, local_printable);
    atomicAdd(&smem.control_count, local_control);
    atomicMax(&smem.null_run_max, local_max_null_run);
    
    __syncthreads();
    
    // Calculate entropy
    smem.reduction_scratch[tid] = 0.0f;
    __syncthreads();
    
    float entropy = block_reduce_entropy(smem.reduction_scratch, smem.histogram,
                                          length, tid, block_size);
    
    // UTF-8 validation
    if (tid == 0) {
        int utf8_state = 0;
        uint32_t valid_count = 0;
        uint32_t total_count = 0;
        
        for (uint32_t i = 0; i < length; ++i) {
            validate_utf8_byte(data[i], utf8_state, valid_count, total_count);
        }
        
        smem.utf8_valid_count = valid_count;
        smem.utf8_total_count = total_count;
    }
    
    __syncthreads();
    
    // Write results
    if (tid == 0) {
        result->entropy = entropy;
        result->printable_ratio = length > 0 ?
            static_cast<float>(smem.printable_count) / static_cast<float>(length) : 0.0f;
        result->control_char_ratio = length > 0 ?
            static_cast<float>(smem.control_count) / static_cast<float>(length) : 0.0f;
        result->max_null_run = smem.null_run_max;
        result->utf8_validity = smem.utf8_total_count > 0 ?
            static_cast<float>(smem.utf8_valid_count) / static_cast<float>(smem.utf8_total_count) : 0.0f;
        
        result->composite_score = calculate_composite_score(*result, weights, length);
    }
}

__device__ DeviceHeuristicResult evaluate_heuristics_inline(
    const uint8_t* data,
    uint32_t length,
    const DeviceHeuristicWeights& weights
) {
    DeviceHeuristicResult result;
    
    if (length == 0) {
        return result;
    }
    
    // For small data (up to 32 bytes), use warp-level operations
    const int lane_id = threadIdx.x % 32;
    
    // Each lane processes one byte (for length <= 32)
    uint8_t my_byte = (lane_id < length) ? data[lane_id] : 0;
    bool is_valid = lane_id < length;
    
    // Count printable
    bool is_print = is_valid && is_printable_ascii(my_byte);
    uint32_t printable_count = __popc(__ballot_sync(0xFFFFFFFF, is_print));
    
    // Count control chars
    bool is_ctrl = is_valid && is_control_char(my_byte);
    uint32_t control_count = __popc(__ballot_sync(0xFFFFFFFF, is_ctrl));
    
    // Find max null run (simplified for inline)
    bool is_null = is_valid && (my_byte == 0);
    uint32_t null_mask = __ballot_sync(0xFFFFFFFF, is_null);
    
    // Count longest consecutive 1s in null_mask
    uint32_t max_null_run = 0;
    uint32_t current_run = 0;
    for (int i = 0; i < 32 && i < static_cast<int>(length); ++i) {
        if ((null_mask >> i) & 1) {
            current_run++;
            if (current_run > max_null_run) {
                max_null_run = current_run;
            }
        } else {
            current_run = 0;
        }
    }
    
    // Simple entropy estimation for small data
    // Build a mini histogram using warp shuffle
    float entropy = 0.0f;
    for (int bin = 0; bin < 256; ++bin) {
        bool matches = is_valid && (my_byte == bin);
        uint32_t count = __popc(__ballot_sync(0xFFFFFFFF, matches));
        if (count > 0) {
            entropy += entropy_contribution(count, length);
        }
    }
    
    // Broadcast entropy to all lanes
    entropy = __shfl_sync(0xFFFFFFFF, entropy, 0);
    
    result.entropy = entropy;
    result.printable_ratio = static_cast<float>(printable_count) / static_cast<float>(length);
    result.control_char_ratio = static_cast<float>(control_count) / static_cast<float>(length);
    result.max_null_run = max_null_run;
    result.utf8_validity = 0.5f;  // Simplified for inline
    
    result.composite_score = calculate_composite_score(result, weights, length);
    
    return result;
}

// ============================================================================
// Host-side Launcher Implementation
// ============================================================================

HeuristicsKernel::HeuristicsKernel() : configured_(false) {}

HeuristicsKernel::~HeuristicsKernel() {}

void HeuristicsKernel::configure(int device_id) {
    kernel_config_ = get_optimal_config(device_id, 256, sizeof(HeuristicsSharedMem));
    configured_ = true;
}

void HeuristicsKernel::evaluate(const uint8_t* data, uint32_t length,
                                 const DeviceHeuristicWeights& weights,
                                 DeviceHeuristicResult* result,
                                 cudaStream_t stream) {
    if (!configured_) {
        configure(0);
    }
    
    // Single block for single sequence
    int threads = 256;  // Good for histogram operations
    
    heuristics_kernel<<<1, threads, sizeof(HeuristicsSharedMem), stream>>>(
        data, length, weights, result
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

void HeuristicsKernel::evaluate_batch(const uint8_t** data_ptrs, const uint32_t* lengths,
                                       uint32_t num_sequences,
                                       const DeviceHeuristicWeights& weights,
                                       DeviceHeuristicResult* results,
                                       cudaStream_t stream) {
    if (!configured_) {
        configure(0);
    }
    
    // One block per sequence
    int threads = 256;
    int blocks = num_sequences;
    
    batch_heuristics_kernel<<<blocks, threads, sizeof(HeuristicsSharedMem), stream>>>(
        data_ptrs, lengths, num_sequences, weights, results
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

} // namespace cuda
} // namespace etb
