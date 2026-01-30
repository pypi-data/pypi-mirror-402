#include "etb/cuda/gpu_memory.cuh"
#include <cstring>

namespace etb {
namespace cuda {

// Constant memory declarations for signatures
__constant__ DeviceFileSignature d_signatures[MAX_SIGNATURES];
__constant__ DeviceFooterSignature d_footers[MAX_SIGNATURES];
__constant__ uint32_t d_signature_count;
__constant__ uint32_t d_footer_count;

// Static variable to track signature count on host
static uint32_t h_signature_count = 0;
static uint32_t h_footer_count = 0;

// ============================================================================
// GPUMemoryManager Implementation
// ============================================================================

GPUMemoryManager::GPUMemoryManager() : initialized_(false) {}

GPUMemoryManager::GPUMemoryManager(const Config& config) : initialized_(false) {
    initialize(config);
}

GPUMemoryManager::~GPUMemoryManager() {
    release();
}

bool GPUMemoryManager::initialize(const Config& config) {
    if (initialized_) {
        release();
    }
    
    if (!is_cuda_available()) {
        return false;
    }
    
    config_ = config;
    
    try {
        allocate_buffers();
        create_streams();
        initialized_ = true;
        return true;
    } catch (const std::exception&) {
        release();
        return false;
    }
}

void GPUMemoryManager::release() {
    destroy_streams();
    
    pinned_input_.free();
    device_input_.free();
    prefix_trie_.free();
    candidate_queue_.free();
    candidate_count_.free();
    min_score_.free();
    work_queue_.free();
    work_queue_head_.free();
    work_queue_tail_.free();
    histogram_.free();
    
    initialized_ = false;
}

void GPUMemoryManager::allocate_buffers() {
    // Pinned input buffer for fast host-to-device transfers
    pinned_input_.allocate(config_.max_input_size);
    
    // Device input buffer
    device_input_.allocate(config_.max_input_size);
    
    // Prefix trie nodes
    prefix_trie_.allocate(config_.prefix_trie_capacity);
    prefix_trie_.clear();
    
    // Candidate queue
    candidate_queue_.allocate(config_.candidate_queue_capacity);
    candidate_count_.allocate(1);
    min_score_.allocate(1);
    reset_candidate_queue();
    
    // Work queue for path generation
    work_queue_.allocate(config_.work_queue_capacity);
    work_queue_head_.allocate(1);
    work_queue_tail_.allocate(1);
    
    // Histogram for entropy calculation (256 bins per thread block)
    // Allocate enough for multiple concurrent blocks
    histogram_.allocate(256 * 256);  // 256 blocks * 256 bins
    histogram_.clear();
}

void GPUMemoryManager::create_streams() {
    streams_.resize(config_.num_streams);
    for (int i = 0; i < config_.num_streams; ++i) {
        ETB_CUDA_CHECK(cudaStreamCreate(&streams_[i]));
    }
}

void GPUMemoryManager::destroy_streams() {
    for (auto& stream : streams_) {
        if (stream) {
            cudaStreamDestroy(stream);
            stream = nullptr;
        }
    }
    streams_.clear();
}

void GPUMemoryManager::upload_input(const uint8_t* data, size_t length, cudaStream_t stream) {
    if (length > config_.max_input_size) {
        throw std::runtime_error("Input size exceeds maximum buffer size");
    }
    
    // Copy to pinned memory first
    std::memcpy(pinned_input_.data(), data, length);
    
    // Transfer to device
    if (stream) {
        device_input_.copy_from_host_async(pinned_input_, stream);
    } else {
        device_input_.copy_from_host(pinned_input_.data(), length);
    }
}

void GPUMemoryManager::init_prefix_trie(const std::vector<DevicePrefixTrieNode>* initial_nodes) {
    if (initial_nodes && !initial_nodes->empty()) {
        if (initial_nodes->size() > config_.prefix_trie_capacity) {
            throw std::runtime_error("Initial trie nodes exceed capacity");
        }
        prefix_trie_.copy_from_host(*initial_nodes);
    } else {
        prefix_trie_.clear();
    }
}

void GPUMemoryManager::reset_candidate_queue() {
    candidate_queue_.clear();
    
    uint32_t zero = 0;
    ETB_CUDA_CHECK(cudaMemcpy(candidate_count_.data(), &zero, sizeof(uint32_t), 
                              cudaMemcpyHostToDevice));
    
    float initial_min = 0.0f;
    ETB_CUDA_CHECK(cudaMemcpy(min_score_.data(), &initial_min, sizeof(float),
                              cudaMemcpyHostToDevice));
}

size_t GPUMemoryManager::download_candidates(std::vector<DeviceCandidate>& candidates) {
    uint32_t count = 0;
    ETB_CUDA_CHECK(cudaMemcpy(&count, candidate_count_.data(), sizeof(uint32_t),
                              cudaMemcpyDeviceToHost));
    
    if (count == 0) {
        candidates.clear();
        return 0;
    }
    
    if (count > config_.candidate_queue_capacity) {
        count = static_cast<uint32_t>(config_.candidate_queue_capacity);
    }
    
    candidates.resize(count);
    ETB_CUDA_CHECK(cudaMemcpy(candidates.data(), candidate_queue_.data(),
                              count * sizeof(DeviceCandidate), cudaMemcpyDeviceToHost));
    
    return count;
}

cudaStream_t GPUMemoryManager::get_stream(int index) const {
    if (index < 0 || index >= static_cast<int>(streams_.size())) {
        return nullptr;
    }
    return streams_[index];
}

void GPUMemoryManager::synchronize_all() {
    for (auto& stream : streams_) {
        if (stream) {
            ETB_CUDA_CHECK(cudaStreamSynchronize(stream));
        }
    }
}

GPUMemoryManager::MemoryStats GPUMemoryManager::get_memory_stats() const {
    MemoryStats stats;
    
    stats.input_buffer_size = pinned_input_.bytes() + device_input_.bytes();
    stats.trie_size = prefix_trie_.bytes();
    stats.candidate_queue_size = candidate_queue_.bytes() + candidate_count_.bytes() + min_score_.bytes();
    stats.work_queue_size = work_queue_.bytes() + work_queue_head_.bytes() + work_queue_tail_.bytes();
    stats.other_size = histogram_.bytes();
    
    stats.total_allocated = stats.input_buffer_size + stats.trie_size + 
                           stats.candidate_queue_size + stats.work_queue_size + 
                           stats.other_size;
    
    return stats;
}

// ============================================================================
// SignatureConstantMemory Implementation
// ============================================================================

bool SignatureConstantMemory::upload_signatures(const std::vector<DeviceFileSignature>& signatures) {
    if (signatures.size() > MAX_SIGNATURES) {
        return false;
    }
    
    h_signature_count = static_cast<uint32_t>(signatures.size());
    
    // Upload signatures to constant memory
    cudaError_t err = cudaMemcpyToSymbol(d_signatures, signatures.data(),
                                          signatures.size() * sizeof(DeviceFileSignature));
    if (err != cudaSuccess) {
        return false;
    }
    
    // Upload count
    err = cudaMemcpyToSymbol(d_signature_count, &h_signature_count, sizeof(uint32_t));
    return err == cudaSuccess;
}

bool SignatureConstantMemory::upload_footers(const std::vector<DeviceFooterSignature>& footers) {
    if (footers.size() > MAX_SIGNATURES) {
        return false;
    }
    
    h_footer_count = static_cast<uint32_t>(footers.size());
    
    // Upload footers to constant memory
    cudaError_t err = cudaMemcpyToSymbol(d_footers, footers.data(),
                                          footers.size() * sizeof(DeviceFooterSignature));
    if (err != cudaSuccess) {
        return false;
    }
    
    // Upload count
    err = cudaMemcpyToSymbol(d_footer_count, &h_footer_count, sizeof(uint32_t));
    return err == cudaSuccess;
}

uint32_t SignatureConstantMemory::get_signature_count() {
    return h_signature_count;
}

void SignatureConstantMemory::clear() {
    h_signature_count = 0;
    h_footer_count = 0;
    cudaMemcpyToSymbol(d_signature_count, &h_signature_count, sizeof(uint32_t));
    cudaMemcpyToSymbol(d_footer_count, &h_footer_count, sizeof(uint32_t));
}

} // namespace cuda
} // namespace etb
