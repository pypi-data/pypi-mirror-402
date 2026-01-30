#ifndef ETB_ARCH_OPTIMIZATIONS_CUH
#define ETB_ARCH_OPTIMIZATIONS_CUH

#include "cuda_common.cuh"

namespace etb {
namespace cuda {

// ============================================================================
// Architecture Detection and Configuration
// ============================================================================

/**
 * Runtime architecture detection.
 */
struct ArchitectureInfo {
    int sm_version;
    bool is_hopper;         // SM 90
    bool is_blackwell;      // SM 100
    bool has_tensor_cores;
    bool has_async_copy;
    bool has_cluster_launch;
    size_t max_shared_mem;
    int max_threads_per_sm;
    int registers_per_sm;
    
    ArchitectureInfo()
        : sm_version(0), is_hopper(false), is_blackwell(false)
        , has_tensor_cores(false), has_async_copy(false)
        , has_cluster_launch(false), max_shared_mem(0)
        , max_threads_per_sm(0), registers_per_sm(0) {}
};

/**
 * Get architecture information for a device.
 */
ArchitectureInfo get_architecture_info(int device_id = 0);

// ============================================================================
// Hopper (SM 90) Optimizations
// ============================================================================

namespace hopper {

/**
 * Hopper-optimized kernel configuration.
 */
struct HopperConfig {
    // Thread block configuration
    static constexpr int THREADS_PER_BLOCK = 256;
    static constexpr int WARPS_PER_BLOCK = THREADS_PER_BLOCK / 32;
    
    // Shared memory configuration
    static constexpr size_t DEFAULT_SHARED_MEM = 48 * 1024;  // 48KB
    static constexpr size_t MAX_SHARED_MEM = 228 * 1024;     // 228KB with opt-in
    
    // Occupancy targets
    static constexpr int TARGET_BLOCKS_PER_SM = 4;
    static constexpr int REGISTERS_PER_THREAD = 64;
    
    // Memory access patterns
    static constexpr int CACHE_LINE_SIZE = 128;
    static constexpr int SECTOR_SIZE = 32;
};

/**
 * Configure kernel for Hopper architecture.
 * Enables extended shared memory if beneficial.
 */
template<typename KernelFunc>
void configure_hopper_kernel(KernelFunc kernel, size_t shared_mem_required) {
    if (shared_mem_required > HopperConfig::DEFAULT_SHARED_MEM) {
        // Request extended shared memory
        cudaFuncSetAttribute(kernel, 
            cudaFuncAttributeMaxDynamicSharedMemorySize,
            static_cast<int>(HopperConfig::MAX_SHARED_MEM));
    }
    
    // Set preferred cache configuration
    cudaFuncSetCacheConfig(kernel, cudaFuncCachePreferShared);
}

/**
 * Hopper-optimized memory copy using async copy.
 * Uses cp.async for efficient global to shared memory transfers.
 * Note: For variable-size copies, use the templated version or memcpy fallback.
 */
template<size_t BYTES>
__device__ inline void async_copy_global_to_shared_fixed(
    void* shared_dst,
    const void* global_src
) {
#if __CUDA_ARCH__ >= 900
    // Use cp.async for Hopper with compile-time constant size
    static_assert(BYTES == 4 || BYTES == 8 || BYTES == 16, 
                  "cp.async only supports 4, 8, or 16 byte copies");
    asm volatile(
        "cp.async.ca.shared.global [%0], [%1], %2;\n"
        :
        : "r"(static_cast<unsigned int>(__cvta_generic_to_shared(shared_dst))),
          "l"(global_src),
          "n"(BYTES)
    );
#else
    // Fallback for older architectures
    memcpy(shared_dst, global_src, BYTES);
#endif
}

/**
 * Variable-size async copy (uses memcpy fallback for non-constant sizes).
 */
__device__ inline void async_copy_global_to_shared(
    void* shared_dst,
    const void* global_src,
    size_t bytes
) {
    // For variable sizes, use standard memcpy
    // cp.async requires compile-time constant sizes
    memcpy(shared_dst, global_src, bytes);
}

/**
 * Commit async copies and wait.
 */
__device__ inline void async_copy_commit_and_wait() {
#if __CUDA_ARCH__ >= 900
    asm volatile("cp.async.commit_group;\n");
    asm volatile("cp.async.wait_group 0;\n");
#endif
    __syncthreads();
}

/**
 * Hopper-optimized warp-level reduction.
 * Uses warp shuffle with reduced synchronization.
 */
template<typename T>
__device__ inline T hopper_warp_reduce_sum(T val) {
    // Hopper supports efficient warp shuffles
    #pragma unroll
    for (int offset = 16; offset > 0; offset /= 2) {
        val += __shfl_down_sync(0xFFFFFFFF, val, offset);
    }
    return val;
}

/**
 * Hopper-optimized block-level reduction.
 */
template<typename T>
__device__ inline T hopper_block_reduce_sum(T val, T* shared_data) {
    const int tid = threadIdx.x;
    const int lane_id = tid % 32;
    const int warp_id = tid / 32;
    
    // Warp-level reduction
    val = hopper_warp_reduce_sum(val);
    
    // Store warp results
    if (lane_id == 0) {
        shared_data[warp_id] = val;
    }
    __syncthreads();
    
    // Final reduction in first warp
    if (warp_id == 0) {
        val = (tid < HopperConfig::WARPS_PER_BLOCK) ? shared_data[tid] : T(0);
        val = hopper_warp_reduce_sum(val);
    }
    
    return val;
}

} // namespace hopper

// ============================================================================
// Blackwell (SM 100) Optimizations
// ============================================================================

namespace blackwell {

/**
 * Blackwell-optimized kernel configuration.
 */
struct BlackwellConfig {
    // Thread block configuration - Blackwell supports larger blocks
    static constexpr int THREADS_PER_BLOCK = 512;
    static constexpr int WARPS_PER_BLOCK = THREADS_PER_BLOCK / 32;
    
    // Shared memory configuration - Blackwell has more shared memory
    static constexpr size_t DEFAULT_SHARED_MEM = 64 * 1024;  // 64KB
    static constexpr size_t MAX_SHARED_MEM = 256 * 1024;     // 256KB with opt-in
    
    // Occupancy targets
    static constexpr int TARGET_BLOCKS_PER_SM = 2;
    static constexpr int REGISTERS_PER_THREAD = 128;
    
    // Memory access patterns
    static constexpr int CACHE_LINE_SIZE = 128;
    static constexpr int SECTOR_SIZE = 32;
    
    // Blackwell-specific features
    static constexpr bool HAS_ENHANCED_TENSOR_CORES = true;
    static constexpr bool HAS_IMPROVED_L2_CACHE = true;
};

/**
 * Configure kernel for Blackwell architecture.
 */
template<typename KernelFunc>
void configure_blackwell_kernel(KernelFunc kernel, size_t shared_mem_required) {
    if (shared_mem_required > BlackwellConfig::DEFAULT_SHARED_MEM) {
        cudaFuncSetAttribute(kernel,
            cudaFuncAttributeMaxDynamicSharedMemorySize,
            static_cast<int>(BlackwellConfig::MAX_SHARED_MEM));
    }
    
    // Blackwell benefits from L2 cache preference for read-heavy workloads
    cudaFuncSetCacheConfig(kernel, cudaFuncCachePreferL1);
}

/**
 * Blackwell-optimized memory prefetch.
 * Uses improved prefetch instructions.
 */
__device__ inline void prefetch_global(const void* ptr) {
#if __CUDA_ARCH__ >= 1000
    // Blackwell prefetch
    asm volatile("prefetch.global.L2 [%0];\n" : : "l"(ptr));
#elif __CUDA_ARCH__ >= 900
    // Hopper prefetch
    asm volatile("prefetch.global.L2 [%0];\n" : : "l"(ptr));
#endif
}

/**
 * Blackwell-optimized warp reduction with larger register file.
 */
template<typename T>
__device__ inline T blackwell_warp_reduce_sum(T val) {
    #pragma unroll
    for (int offset = 16; offset > 0; offset /= 2) {
        val += __shfl_down_sync(0xFFFFFFFF, val, offset);
    }
    return val;
}

/**
 * Blackwell-optimized block reduction for larger blocks.
 */
template<typename T>
__device__ inline T blackwell_block_reduce_sum(T val, T* shared_data) {
    const int tid = threadIdx.x;
    const int lane_id = tid % 32;
    const int warp_id = tid / 32;
    
    // Warp-level reduction
    val = blackwell_warp_reduce_sum(val);
    
    // Store warp results
    if (lane_id == 0) {
        shared_data[warp_id] = val;
    }
    __syncthreads();
    
    // Final reduction - Blackwell has more warps per block
    if (warp_id == 0) {
        val = (tid < BlackwellConfig::WARPS_PER_BLOCK) ? shared_data[tid] : T(0);
        val = blackwell_warp_reduce_sum(val);
    }
    
    return val;
}

/**
 * Blackwell-optimized histogram using larger shared memory.
 */
__device__ inline void blackwell_histogram_add(uint32_t* histogram, uint8_t value) {
    // Blackwell can handle more concurrent atomics efficiently
    atomicAdd(&histogram[value], 1);
}

} // namespace blackwell

// ============================================================================
// Architecture-Adaptive Kernel Launch
// ============================================================================

/**
 * Adaptive kernel configuration based on detected architecture.
 */
struct AdaptiveKernelConfig {
    int threads_per_block;
    int blocks_per_grid;
    size_t shared_mem_size;
    bool use_async_copy;
    bool use_extended_shared_mem;
    
    AdaptiveKernelConfig()
        : threads_per_block(256), blocks_per_grid(1)
        , shared_mem_size(48 * 1024), use_async_copy(false)
        , use_extended_shared_mem(false) {}
};

/**
 * Get adaptive configuration for current device.
 */
AdaptiveKernelConfig get_adaptive_config(int device_id, size_t work_items, 
                                          size_t shared_mem_required);

/**
 * Architecture-specific kernel launcher.
 */
class AdaptiveKernelLauncher {
public:
    AdaptiveKernelLauncher();
    ~AdaptiveKernelLauncher();
    
    /**
     * Initialize for a specific device.
     */
    void initialize(int device_id);
    
    /**
     * Get the detected architecture.
     */
    const ArchitectureInfo& get_arch_info() const { return arch_info_; }
    
    /**
     * Check if Hopper optimizations should be used.
     */
    bool use_hopper_optimizations() const { return arch_info_.is_hopper; }
    
    /**
     * Check if Blackwell optimizations should be used.
     */
    bool use_blackwell_optimizations() const { return arch_info_.is_blackwell; }
    
    /**
     * Get optimal thread count for current architecture.
     */
    int get_optimal_threads() const;
    
    /**
     * Get optimal shared memory size for current architecture.
     */
    size_t get_optimal_shared_mem() const;

private:
    ArchitectureInfo arch_info_;
    bool initialized_;
};

} // namespace cuda
} // namespace etb

#endif // ETB_ARCH_OPTIMIZATIONS_CUH
