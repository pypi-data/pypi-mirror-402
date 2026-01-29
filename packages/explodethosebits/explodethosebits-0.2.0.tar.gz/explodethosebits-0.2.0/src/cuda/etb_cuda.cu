#include "etb/cuda/etb_cuda.cuh"
#include <chrono>

namespace etb {
namespace cuda {

// ============================================================================
// ETBCudaEngine Implementation
// ============================================================================

ETBCudaEngine::ETBCudaEngine()
    : initialized_(false)
    , device_id_(-1) {}

ETBCudaEngine::~ETBCudaEngine() {
    release();
}

bool ETBCudaEngine::initialize(const Config& config, int device_id) {
    if (initialized_) {
        release();
    }
    
    // Check CUDA availability
    if (!is_cuda_available()) {
        return false;
    }
    
    // Set device
    cudaError_t err = cudaSetDevice(device_id);
    if (err != cudaSuccess) {
        return false;
    }
    
    device_id_ = device_id;
    config_ = config;
    
    // Get architecture info
    arch_info_ = get_architecture_info(device_id);
    
    try {
        // Initialize memory manager
        GPUMemoryManager::Config mem_config;
        mem_config.max_input_size = config.max_input_size;
        mem_config.prefix_trie_capacity = config.prefix_trie_capacity;
        mem_config.candidate_queue_capacity = config.candidate_queue_capacity;
        mem_config.num_streams = config.num_streams;
        
        memory_manager_ = std::make_unique<GPUMemoryManager>(mem_config);
        
        // Initialize kernel launchers
        path_generator_ = std::make_unique<PathGeneratorKernel>();
        heuristics_ = std::make_unique<HeuristicsKernel>();
        signature_matcher_ = std::make_unique<SignatureMatcherKernel>();
        prefix_pruner_ = std::make_unique<PrefixPrunerKernel>();
        
        // Initialize adaptive launcher
        adaptive_launcher_ = std::make_unique<AdaptiveKernelLauncher>();
        adaptive_launcher_->initialize(device_id);
        
        // Configure kernels for current architecture
        configure_kernels();
        
        initialized_ = true;
        return true;
        
    } catch (const std::exception&) {
        release();
        return false;
    }
}

void ETBCudaEngine::release() {
    path_generator_.reset();
    heuristics_.reset();
    signature_matcher_.reset();
    prefix_pruner_.reset();
    adaptive_launcher_.reset();
    memory_manager_.reset();
    
    initialized_ = false;
    device_id_ = -1;
}

void ETBCudaEngine::configure_kernels() {
    path_generator_->configure(device_id_);
    heuristics_->configure(device_id_);
    signature_matcher_->configure(device_id_);
    prefix_pruner_->configure(device_id_);
}

bool ETBCudaEngine::load_signatures(const std::vector<DeviceFileSignature>& signatures) {
    if (!initialized_) {
        return false;
    }
    
    return SignatureConstantMemory::upload_signatures(signatures);
}

ETBCudaEngine::ExtractionResult ETBCudaEngine::extract(const uint8_t* input, size_t length) {
    ExtractionResult result;
    
    if (!initialized_) {
        result.error_message = "Engine not initialized";
        return result;
    }
    
    if (length == 0) {
        result.success = true;
        return result;
    }
    
    if (length > config_.max_input_size) {
        result.error_message = "Input exceeds maximum size";
        return result;
    }
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    try {
        // Upload input to GPU
        cudaStream_t stream = memory_manager_->get_stream(0);
        memory_manager_->upload_input(input, length, stream);
        
        // Reset candidate queue
        memory_manager_->reset_candidate_queue();
        
        // Initialize prefix trie
        memory_manager_->init_prefix_trie();
        
        // Run extraction pipeline
        run_extraction_pipeline(length, stream);
        
        // Synchronize
        ETB_CUDA_CHECK(cudaStreamSynchronize(stream));
        
        // Download results
        std::vector<DeviceCandidate> candidates;
        size_t num_candidates = memory_manager_->download_candidates(candidates);
        
        result.candidates = std::move(candidates);
        result.success = true;
        
    } catch (const std::exception& e) {
        result.error_message = e.what();
        result.success = false;
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
    result.wall_clock_ms = duration.count() / 1000.0f;
    
    return result;
}

void ETBCudaEngine::run_extraction_pipeline(size_t input_length, cudaStream_t stream) {
    // Configure path generator
    PathGeneratorConfig pg_config;
    pg_config.input_length = static_cast<uint32_t>(input_length);
    pg_config.max_depth = config_.early_stopping.level3_bytes;
    pg_config.batch_size = 65536;
    pg_config.bit_pruning = config_.bit_pruning;
    pg_config.early_stopping = config_.early_stopping;
    pg_config.heuristic_weights = config_.heuristic_weights;
    pg_config.scoring_weights = config_.scoring_weights;
    
    // Initialize work queue
    path_generator_->init_work_queue(*memory_manager_, 
                                      static_cast<uint32_t>(input_length),
                                      config_.bit_pruning.bit_mask, stream);
    
    // Launch path generator kernel
    path_generator_->launch(*memory_manager_, pg_config, stream);
}

GPUMemoryManager::MemoryStats ETBCudaEngine::get_memory_stats() const {
    if (memory_manager_) {
        return memory_manager_->get_memory_stats();
    }
    return GPUMemoryManager::MemoryStats();
}

// ============================================================================
// Utility Functions
// ============================================================================

int get_cuda_device_count() {
    int count = 0;
    cudaError_t err = cudaGetDeviceCount(&count);
    if (err != cudaSuccess) {
        return 0;
    }
    return count;
}

DeviceInfo get_cuda_device_info(int device_id) {
    return get_device_info(device_id);
}

int select_best_device() {
    int device_count = get_cuda_device_count();
    if (device_count == 0) {
        return -1;
    }
    
    int best_device = 0;
    int best_sm = 0;
    size_t best_memory = 0;
    
    for (int i = 0; i < device_count; ++i) {
        DeviceInfo info = get_device_info(i);
        
        // Prefer higher SM version
        if (info.sm_version > best_sm) {
            best_device = i;
            best_sm = info.sm_version;
            best_memory = info.total_global_mem;
        } else if (info.sm_version == best_sm && info.total_global_mem > best_memory) {
            // Same SM version, prefer more memory
            best_device = i;
            best_memory = info.total_global_mem;
        }
    }
    
    return best_device;
}

} // namespace cuda
} // namespace etb
