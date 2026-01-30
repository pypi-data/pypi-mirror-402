#include "etb/cuda/arch_optimizations.cuh"

namespace etb {
namespace cuda {

// ============================================================================
// Architecture Detection Implementation
// ============================================================================

ArchitectureInfo get_architecture_info(int device_id) {
    ArchitectureInfo info;
    
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
    
    info.sm_version = props.major * 10 + props.minor;
    info.is_hopper = (info.sm_version >= 90 && info.sm_version < 100);
    info.is_blackwell = (info.sm_version >= 100);
    
    // Feature detection
    info.has_tensor_cores = (info.sm_version >= 70);  // Volta and later
    info.has_async_copy = (info.sm_version >= 80);    // Ampere and later
    info.has_cluster_launch = (info.sm_version >= 90); // Hopper and later
    
    info.max_shared_mem = props.sharedMemPerMultiprocessor;
    info.max_threads_per_sm = props.maxThreadsPerMultiProcessor;
    info.registers_per_sm = props.regsPerMultiprocessor;
    
    return info;
}

// ============================================================================
// Adaptive Configuration Implementation
// ============================================================================

AdaptiveKernelConfig get_adaptive_config(int device_id, size_t work_items,
                                          size_t shared_mem_required) {
    AdaptiveKernelConfig config;
    
    ArchitectureInfo arch = get_architecture_info(device_id);
    
    if (arch.is_blackwell) {
        // Blackwell configuration
        config.threads_per_block = blackwell::BlackwellConfig::THREADS_PER_BLOCK;
        config.shared_mem_size = shared_mem_required > 0 ?
            shared_mem_required : blackwell::BlackwellConfig::DEFAULT_SHARED_MEM;
        config.use_async_copy = true;
        config.use_extended_shared_mem = 
            (shared_mem_required > blackwell::BlackwellConfig::DEFAULT_SHARED_MEM);
            
    } else if (arch.is_hopper) {
        // Hopper configuration
        config.threads_per_block = hopper::HopperConfig::THREADS_PER_BLOCK;
        config.shared_mem_size = shared_mem_required > 0 ?
            shared_mem_required : hopper::HopperConfig::DEFAULT_SHARED_MEM;
        config.use_async_copy = true;
        config.use_extended_shared_mem =
            (shared_mem_required > hopper::HopperConfig::DEFAULT_SHARED_MEM);
            
    } else {
        // Default configuration for older architectures
        config.threads_per_block = 256;
        config.shared_mem_size = shared_mem_required > 0 ?
            shared_mem_required : 48 * 1024;
        config.use_async_copy = (arch.sm_version >= 80);
        config.use_extended_shared_mem = false;
    }
    
    // Calculate blocks needed
    size_t blocks_needed = (work_items + config.threads_per_block - 1) / 
                           config.threads_per_block;
    
    // Limit to reasonable grid size
    if (blocks_needed > arch::MAX_GRID_DIM) {
        blocks_needed = arch::MAX_GRID_DIM;
    }
    
    config.blocks_per_grid = static_cast<int>(blocks_needed);
    
    return config;
}

// ============================================================================
// Adaptive Kernel Launcher Implementation
// ============================================================================

AdaptiveKernelLauncher::AdaptiveKernelLauncher() : initialized_(false) {}

AdaptiveKernelLauncher::~AdaptiveKernelLauncher() {}

void AdaptiveKernelLauncher::initialize(int device_id) {
    arch_info_ = get_architecture_info(device_id);
    initialized_ = true;
}

int AdaptiveKernelLauncher::get_optimal_threads() const {
    if (!initialized_) {
        return 256;  // Default
    }
    
    if (arch_info_.is_blackwell) {
        return blackwell::BlackwellConfig::THREADS_PER_BLOCK;
    } else if (arch_info_.is_hopper) {
        return hopper::HopperConfig::THREADS_PER_BLOCK;
    }
    
    return 256;
}

size_t AdaptiveKernelLauncher::get_optimal_shared_mem() const {
    if (!initialized_) {
        return 48 * 1024;  // Default
    }
    
    if (arch_info_.is_blackwell) {
        return blackwell::BlackwellConfig::DEFAULT_SHARED_MEM;
    } else if (arch_info_.is_hopper) {
        return hopper::HopperConfig::DEFAULT_SHARED_MEM;
    }
    
    return 48 * 1024;
}

} // namespace cuda
} // namespace etb
