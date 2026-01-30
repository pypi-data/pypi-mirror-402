#ifndef ETB_CUDA_CUH
#define ETB_CUDA_CUH

/**
 * ExplodeThoseBits CUDA Library
 * 
 * Main include header for all CUDA components.
 * 
 * This library provides GPU-accelerated implementations of:
 * - Path generation with work-stealing
 * - Heuristics calculation with shared memory histograms
 * - Signature matching with constant memory broadcast
 * - Prefix pruning with atomic trie updates
 * 
 * Optimized for:
 * - NVIDIA Hopper (SM 90) architecture
 * - NVIDIA Blackwell (SM 100) architecture
 */

// Common definitions and utilities
#include "cuda_common.cuh"

// GPU memory management
#include "gpu_memory.cuh"

// CUDA kernels
#include "path_generator_kernel.cuh"
#include "heuristics_kernel.cuh"
#include "signature_kernel.cuh"
#include "prefix_pruner_kernel.cuh"

// Architecture-specific optimizations
#include "arch_optimizations.cuh"
#include "blackwell_optimizations.cuh"

namespace etb {
namespace cuda {

/**
 * ETB CUDA Engine - Main interface for GPU-accelerated extraction.
 * 
 * Provides a unified interface for all CUDA operations, handling
 * memory management, kernel launches, and result retrieval.
 */
class ETBCudaEngine {
public:
    /**
     * Configuration for the CUDA engine.
     */
    struct Config {
        // Memory configuration
        size_t max_input_size;
        size_t prefix_trie_capacity;
        size_t candidate_queue_capacity;
        
        // Kernel configuration
        int num_streams;
        bool use_async_operations;
        
        // Early stopping configuration
        DeviceEarlyStoppingConfig early_stopping;
        
        // Heuristic weights
        DeviceHeuristicWeights heuristic_weights;
        
        // Scoring weights
        DeviceScoringWeights scoring_weights;
        
        // Bit pruning configuration
        DeviceBitPruningConfig bit_pruning;
        
        Config()
            : max_input_size(1024 * 1024)
            , prefix_trie_capacity(65536)
            , candidate_queue_capacity(1024)
            , num_streams(4)
            , use_async_operations(true) {}
    };
    
    /**
     * Extraction result from GPU processing.
     */
    struct ExtractionResult {
        std::vector<DeviceCandidate> candidates;
        uint64_t paths_evaluated;
        uint64_t paths_pruned;
        float effective_branching_factor;
        float wall_clock_ms;
        float gpu_utilization;
        bool success;
        std::string error_message;
        
        ExtractionResult()
            : paths_evaluated(0), paths_pruned(0)
            , effective_branching_factor(0.0f), wall_clock_ms(0.0f)
            , gpu_utilization(0.0f), success(false) {}
    };
    
    ETBCudaEngine();
    ~ETBCudaEngine();
    
    // Non-copyable
    ETBCudaEngine(const ETBCudaEngine&) = delete;
    ETBCudaEngine& operator=(const ETBCudaEngine&) = delete;
    
    /**
     * Initialize the CUDA engine.
     * @param config Engine configuration
     * @param device_id CUDA device to use (default: 0)
     * @return true if initialization succeeded
     */
    bool initialize(const Config& config, int device_id = 0);
    
    /**
     * Check if the engine is initialized.
     */
    bool is_initialized() const { return initialized_; }
    
    /**
     * Release all GPU resources.
     */
    void release();
    
    /**
     * Load signatures into constant memory.
     * @param signatures Vector of file signatures
     * @return true if upload succeeded
     */
    bool load_signatures(const std::vector<DeviceFileSignature>& signatures);
    
    /**
     * Extract data from input bytes.
     * @param input Input byte data
     * @param length Length of input
     * @return Extraction result
     */
    ExtractionResult extract(const uint8_t* input, size_t length);
    
    /**
     * Get the current configuration.
     */
    const Config& get_config() const { return config_; }
    
    /**
     * Get architecture information for the current device.
     */
    const ArchitectureInfo& get_arch_info() const { return arch_info_; }
    
    /**
     * Get memory statistics.
     */
    GPUMemoryManager::MemoryStats get_memory_stats() const;

private:
    Config config_;
    bool initialized_;
    int device_id_;
    ArchitectureInfo arch_info_;
    
    // GPU memory manager
    std::unique_ptr<GPUMemoryManager> memory_manager_;
    
    // Kernel launchers
    std::unique_ptr<PathGeneratorKernel> path_generator_;
    std::unique_ptr<HeuristicsKernel> heuristics_;
    std::unique_ptr<SignatureMatcherKernel> signature_matcher_;
    std::unique_ptr<PrefixPrunerKernel> prefix_pruner_;
    
    // Adaptive launcher for architecture-specific optimizations
    std::unique_ptr<AdaptiveKernelLauncher> adaptive_launcher_;
    
    // Internal methods
    void configure_kernels();
    void run_extraction_pipeline(size_t input_length, cudaStream_t stream);
};

/**
 * Check if CUDA is available and get device count.
 * @return Number of CUDA devices, or 0 if CUDA is not available
 */
int get_cuda_device_count();

/**
 * Get information about a CUDA device.
 * @param device_id Device ID
 * @return Device information
 */
DeviceInfo get_cuda_device_info(int device_id = 0);

/**
 * Select the best CUDA device for ETB workloads.
 * Prefers Blackwell > Hopper > other architectures.
 * @return Best device ID, or -1 if no suitable device found
 */
int select_best_device();

} // namespace cuda
} // namespace etb

#endif // ETB_CUDA_CUH
