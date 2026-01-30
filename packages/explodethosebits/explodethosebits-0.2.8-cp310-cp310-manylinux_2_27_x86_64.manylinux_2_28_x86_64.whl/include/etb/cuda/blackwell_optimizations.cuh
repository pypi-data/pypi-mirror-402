#ifndef ETB_BLACKWELL_OPTIMIZATIONS_CUH
#define ETB_BLACKWELL_OPTIMIZATIONS_CUH

#include "cuda_common.cuh"
#include "arch_optimizations.cuh"

// Note: cooperative_groups.h is not included here to avoid namespace pollution
// with CCCL on MSVC. The cluster functions below are stubbed out.

namespace etb {
namespace cuda {
namespace blackwell {

// ============================================================================
// Blackwell (SM 100) Specific Optimizations
// ============================================================================

/**
 * Blackwell memory hierarchy configuration.
 * Blackwell has improved L2 cache and memory bandwidth.
 */
struct BlackwellMemoryConfig {
    // L2 cache configuration
    static constexpr size_t L2_CACHE_SIZE = 96 * 1024 * 1024;  // 96MB typical
    static constexpr size_t L2_CACHE_LINE = 128;
    
    // Memory bandwidth optimization
    static constexpr int COALESCING_WIDTH = 128;  // bytes
    static constexpr int OPTIMAL_VECTOR_WIDTH = 4; // float4/int4
    
    // Prefetch distances
    static constexpr int PREFETCH_DISTANCE = 4;   // cache lines ahead
};

/**
 * Blackwell-optimized path generator configuration.
 */
struct BlackwellPathGeneratorConfig {
    // Larger thread blocks for better occupancy
    static constexpr int THREADS_PER_BLOCK = 512;
    static constexpr int PATHS_PER_THREAD = 4;
    
    // Work distribution
    static constexpr int WORK_ITEMS_PER_BLOCK = THREADS_PER_BLOCK * PATHS_PER_THREAD;
    
    // Shared memory layout
    static constexpr size_t SHARED_PREFIX_CACHE_SIZE = 32 * 1024;  // 32KB for prefix cache
    static constexpr size_t SHARED_WORK_QUEUE_SIZE = 16 * 1024;    // 16KB for work queue
};

/**
 * Blackwell-optimized heuristics configuration.
 */
struct BlackwellHeuristicsConfig {
    // Histogram configuration
    static constexpr int HISTOGRAM_BANKS = 32;  // Reduce bank conflicts
    static constexpr int HISTOGRAM_SIZE = 256 * HISTOGRAM_BANKS;
    
    // Parallel reduction
    static constexpr int REDUCTION_THREADS = 512;
    static constexpr int REDUCTION_WARPS = REDUCTION_THREADS / 32;
};

/**
 * Blackwell-optimized vectorized memory load.
 * Uses float4 for coalesced 128-bit loads.
 */
__device__ inline float4 blackwell_load_float4(const float* ptr) {
    return *reinterpret_cast<const float4*>(ptr);
}

__device__ inline uint4 blackwell_load_uint4(const uint32_t* ptr) {
    return *reinterpret_cast<const uint4*>(ptr);
}

/**
 * Blackwell-optimized vectorized memory store.
 */
__device__ inline void blackwell_store_float4(float* ptr, float4 val) {
    *reinterpret_cast<float4*>(ptr) = val;
}

__device__ inline void blackwell_store_uint4(uint32_t* ptr, uint4 val) {
    *reinterpret_cast<uint4*>(ptr) = val;
}

/**
 * Blackwell L2 cache hint for read-only data.
 */
__device__ inline void blackwell_cache_hint_readonly(const void* ptr) {
#if __CUDA_ARCH__ >= 1000
    asm volatile("prefetch.global.L2::evict_last [%0];\n" : : "l"(ptr));
#endif
}

/**
 * Blackwell L2 cache hint for streaming data.
 */
__device__ inline void blackwell_cache_hint_streaming(const void* ptr) {
#if __CUDA_ARCH__ >= 1000
    asm volatile("prefetch.global.L2::evict_first [%0];\n" : : "l"(ptr));
#endif
}

/**
 * Blackwell-optimized histogram with bank conflict avoidance.
 * Uses padding to avoid shared memory bank conflicts.
 */
template<int BANKS = 32>
__device__ inline void blackwell_histogram_add_banked(
    uint32_t* histogram,  // Size should be 256 * BANKS
    uint8_t value,
    int thread_id
) {
    // Each thread uses a different bank based on thread ID
    int bank = thread_id % BANKS;
    atomicAdd(&histogram[value * BANKS + bank], 1);
}

/**
 * Reduce banked histogram to final histogram.
 */
template<int BANKS = 32>
__device__ inline void blackwell_histogram_reduce(
    uint32_t* banked_histogram,  // Input: 256 * BANKS
    uint32_t* final_histogram,   // Output: 256
    int thread_id,
    int block_size
) {
    // Each thread reduces one or more bins
    for (int bin = thread_id; bin < 256; bin += block_size) {
        uint32_t sum = 0;
        for (int bank = 0; bank < BANKS; ++bank) {
            sum += banked_histogram[bin * BANKS + bank];
        }
        final_histogram[bin] = sum;
    }
}

/**
 * Blackwell-optimized parallel entropy calculation.
 * Uses larger thread blocks and vectorized operations.
 */
__device__ inline float blackwell_calculate_entropy(
    const uint32_t* histogram,
    uint32_t total,
    float* scratch,
    int tid,
    int block_size
) {
    // Each thread handles multiple bins
    int bins_per_thread = (256 + block_size - 1) / block_size;
    float local_entropy = 0.0f;
    
    #pragma unroll 4
    for (int i = 0; i < bins_per_thread; ++i) {
        int bin = tid * bins_per_thread + i;
        if (bin < 256) {
            uint32_t count = histogram[bin];
            if (count > 0 && total > 0) {
                float p = static_cast<float>(count) / static_cast<float>(total);
                local_entropy -= p * log2f(p);
            }
        }
    }
    
    // Block reduction
    scratch[tid] = local_entropy;
    __syncthreads();
    
    // Tree reduction with larger stride for 512 threads
    for (int stride = block_size / 2; stride > 0; stride /= 2) {
        if (tid < stride) {
            scratch[tid] += scratch[tid + stride];
        }
        __syncthreads();
    }
    
    return scratch[0];
}

/**
 * Blackwell-optimized signature matching with vectorized comparison.
 */
__device__ inline bool blackwell_signature_match_vectorized(
    const uint8_t* data,
    const uint8_t* signature,
    const uint8_t* mask,
    int length
) {
    // Process 4 bytes at a time when possible
    int vec_length = length / 4;
    int remainder = length % 4;
    
    // Vectorized comparison
    for (int i = 0; i < vec_length; ++i) {
        uint32_t data_vec = *reinterpret_cast<const uint32_t*>(data + i * 4);
        uint32_t sig_vec = *reinterpret_cast<const uint32_t*>(signature + i * 4);
        uint32_t mask_vec = *reinterpret_cast<const uint32_t*>(mask + i * 4);
        
        if ((data_vec & mask_vec) != (sig_vec & mask_vec)) {
            return false;
        }
    }
    
    // Handle remainder
    for (int i = vec_length * 4; i < length; ++i) {
        if ((data[i] & mask[i]) != (signature[i] & mask[i])) {
            return false;
        }
    }
    
    return true;
}

/**
 * Blackwell-optimized work stealing with improved atomics.
 */
__device__ inline bool blackwell_steal_work(
    uint32_t* work_queue,
    uint32_t* head,
    uint32_t* tail,
    uint32_t queue_capacity,
    uint32_t& work_item
) {
    // Use atomic exchange for more efficient stealing
    uint32_t old_head = atomicAdd(head, 1);
    uint32_t current_tail = __ldcg(tail);  // Cache-global load
    
    if (old_head < current_tail) {
        work_item = work_queue[old_head % queue_capacity];
        return true;
    }
    
    // Restore head if no work
    atomicSub(head, 1);
    return false;
}

/**
 * Blackwell-optimized cooperative group operations.
 * Uses thread block clusters when available.
 * Note: These are stubbed out due to CCCL/MSVC compatibility issues.
 * Full implementation would require cooperative_groups.h.
 */
#if __CUDA_ARCH__ >= 1000
__device__ inline void blackwell_cluster_sync() {
    // Stub - would use cooperative_groups cluster sync
    __syncthreads();
}

__device__ inline int blackwell_cluster_thread_rank() {
    // Stub - returns block-local thread rank
    return threadIdx.x + threadIdx.y * blockDim.x + threadIdx.z * blockDim.x * blockDim.y;
}

__device__ inline int blackwell_cluster_size() {
    // Stub - returns block size
    return blockDim.x * blockDim.y * blockDim.z;
}
#endif

/**
 * Configure kernel for Blackwell with cluster launch.
 */
template<typename KernelFunc>
cudaError_t configure_blackwell_cluster_kernel(
    KernelFunc kernel,
    int cluster_size,
    size_t shared_mem_required
) {
    cudaError_t err;
    
    // Set max dynamic shared memory
    if (shared_mem_required > BlackwellConfig::DEFAULT_SHARED_MEM) {
        err = cudaFuncSetAttribute(kernel,
            cudaFuncAttributeMaxDynamicSharedMemorySize,
            static_cast<int>(BlackwellConfig::MAX_SHARED_MEM));
        if (err != cudaSuccess) return err;
    }
    
    // Set cluster dimensions (Blackwell feature)
#if CUDART_VERSION >= 12000
    cudaFuncAttribute attr = cudaFuncAttributeClusterDimMustBeSet;
    err = cudaFuncSetAttribute(kernel, attr, 1);
    if (err != cudaSuccess) return err;
    
    attr = cudaFuncAttributeClusterSchedulingPolicyPreference;
    err = cudaFuncSetAttribute(kernel, attr, 
        cudaClusterSchedulingPolicySpread);
#endif
    
    return cudaSuccess;
}

} // namespace blackwell
} // namespace cuda
} // namespace etb

#endif // ETB_BLACKWELL_OPTIMIZATIONS_CUH
