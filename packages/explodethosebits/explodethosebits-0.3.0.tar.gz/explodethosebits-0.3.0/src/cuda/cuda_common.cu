#include "etb/cuda/cuda_common.cuh"

namespace etb {
namespace cuda {

DeviceInfo get_device_info(int device_id) {
    DeviceInfo info;
    
    int device_count = 0;
    cudaError_t err = cudaGetDeviceCount(&device_count);
    if (err != cudaSuccess || device_count == 0 || device_id >= device_count) {
        return info;
    }
    
    cudaDeviceProp props;
    err = cudaGetDeviceProperties(&props, device_id);
    if (err != cudaSuccess) {
        return info;
    }
    
    info.device_id = device_id;
    info.sm_version = props.major * 10 + props.minor;
    info.total_global_mem = props.totalGlobalMem;
    info.shared_mem_per_block = props.sharedMemPerBlock;
    info.shared_mem_per_multiprocessor = props.sharedMemPerMultiprocessor;
    info.multiprocessor_count = props.multiProcessorCount;
    info.max_threads_per_block = props.maxThreadsPerBlock;
    info.warp_size = props.warpSize;
    info.supports_cooperative_groups = props.cooperativeLaunch != 0;
    
    return info;
}

bool is_cuda_available() {
    int device_count = 0;
    cudaError_t err = cudaGetDeviceCount(&device_count);
    return err == cudaSuccess && device_count > 0;
}

KernelConfig get_optimal_config(int device_id, size_t work_items, size_t shared_mem_required) {
    KernelConfig config;
    
    DeviceInfo info = get_device_info(device_id);
    if (info.device_id < 0) {
        return config;
    }
    
    config.sm_version = info.sm_version;
    
    // Select threads per block based on architecture
    if (info.sm_version >= arch::BLACKWELL_SM) {
        config.threads_per_block = arch::BLACKWELL_THREADS_PER_BLOCK;
        config.shared_mem_size = shared_mem_required > 0 ? 
            shared_mem_required : arch::BLACKWELL_SHARED_MEM_SIZE;
    } else if (info.sm_version >= arch::HOPPER_SM) {
        config.threads_per_block = arch::HOPPER_THREADS_PER_BLOCK;
        config.shared_mem_size = shared_mem_required > 0 ?
            shared_mem_required : arch::HOPPER_SHARED_MEM_SIZE;
    } else {
        // Fallback for older architectures
        config.threads_per_block = 256;
        config.shared_mem_size = shared_mem_required > 0 ?
            shared_mem_required : 48 * 1024;
    }
    
    // Ensure shared memory doesn't exceed device limits
    if (config.shared_mem_size > info.shared_mem_per_block) {
        config.shared_mem_size = info.shared_mem_per_block;
    }
    
    // Calculate blocks needed
    size_t blocks_needed = (work_items + config.threads_per_block - 1) / config.threads_per_block;
    
    // Limit to max grid dimension
    if (blocks_needed > arch::MAX_GRID_DIM) {
        blocks_needed = arch::MAX_GRID_DIM;
    }
    
    // Try to use at least as many blocks as SMs for good occupancy
    if (blocks_needed < static_cast<size_t>(info.multiprocessor_count)) {
        blocks_needed = info.multiprocessor_count;
    }
    
    config.blocks_per_grid = static_cast<int>(blocks_needed);
    
    return config;
}

} // namespace cuda
} // namespace etb
