#ifndef ETB_GPU_MEMORY_CUH
#define ETB_GPU_MEMORY_CUH

#include "cuda_common.cuh"
#include <memory>
#include <vector>

namespace etb {
namespace cuda {

/**
 * RAII wrapper for pinned (page-locked) host memory.
 * Provides faster host-to-device transfers.
 */
template<typename T>
class PinnedBuffer {
public:
    PinnedBuffer() : data_(nullptr), size_(0), capacity_(0) {}
    
    explicit PinnedBuffer(size_t count) : data_(nullptr), size_(0), capacity_(0) {
        allocate(count);
    }
    
    ~PinnedBuffer() {
        free();
    }
    
    // Non-copyable
    PinnedBuffer(const PinnedBuffer&) = delete;
    PinnedBuffer& operator=(const PinnedBuffer&) = delete;
    
    // Movable
    PinnedBuffer(PinnedBuffer&& other) noexcept
        : data_(other.data_), size_(other.size_), capacity_(other.capacity_) {
        other.data_ = nullptr;
        other.size_ = 0;
        other.capacity_ = 0;
    }
    
    PinnedBuffer& operator=(PinnedBuffer&& other) noexcept {
        if (this != &other) {
            free();
            data_ = other.data_;
            size_ = other.size_;
            capacity_ = other.capacity_;
            other.data_ = nullptr;
            other.size_ = 0;
            other.capacity_ = 0;
        }
        return *this;
    }
    
    void allocate(size_t count) {
        if (count > capacity_) {
            free();
            ETB_CUDA_CHECK(cudaMallocHost(&data_, count * sizeof(T)));
            capacity_ = count;
        }
        size_ = count;
    }
    
    void free() {
        if (data_) {
            cudaFreeHost(data_);
            data_ = nullptr;
            size_ = 0;
            capacity_ = 0;
        }
    }
    
    T* data() { return data_; }
    const T* data() const { return data_; }
    size_t size() const { return size_; }
    size_t capacity() const { return capacity_; }
    size_t bytes() const { return size_ * sizeof(T); }
    bool empty() const { return size_ == 0; }
    
    T& operator[](size_t index) { return data_[index]; }
    const T& operator[](size_t index) const { return data_[index]; }
    
    // Copy from host vector
    void copy_from(const std::vector<T>& src) {
        allocate(src.size());
        std::memcpy(data_, src.data(), src.size() * sizeof(T));
    }
    
    // Copy to host vector
    std::vector<T> to_vector() const {
        return std::vector<T>(data_, data_ + size_);
    }

private:
    T* data_;
    size_t size_;
    size_t capacity_;
};

/**
 * RAII wrapper for device (GPU) memory.
 */
template<typename T>
class DeviceBuffer {
public:
    DeviceBuffer() : data_(nullptr), size_(0), capacity_(0) {}
    
    explicit DeviceBuffer(size_t count) : data_(nullptr), size_(0), capacity_(0) {
        allocate(count);
    }
    
    ~DeviceBuffer() {
        free();
    }
    
    // Non-copyable
    DeviceBuffer(const DeviceBuffer&) = delete;
    DeviceBuffer& operator=(const DeviceBuffer&) = delete;
    
    // Movable
    DeviceBuffer(DeviceBuffer&& other) noexcept
        : data_(other.data_), size_(other.size_), capacity_(other.capacity_) {
        other.data_ = nullptr;
        other.size_ = 0;
        other.capacity_ = 0;
    }
    
    DeviceBuffer& operator=(DeviceBuffer&& other) noexcept {
        if (this != &other) {
            free();
            data_ = other.data_;
            size_ = other.size_;
            capacity_ = other.capacity_;
            other.data_ = nullptr;
            other.size_ = 0;
            other.capacity_ = 0;
        }
        return *this;
    }
    
    void allocate(size_t count) {
        if (count > capacity_) {
            free();
            ETB_CUDA_CHECK(cudaMalloc(&data_, count * sizeof(T)));
            capacity_ = count;
        }
        size_ = count;
    }
    
    void free() {
        if (data_) {
            cudaFree(data_);
            data_ = nullptr;
            size_ = 0;
            capacity_ = 0;
        }
    }
    
    void clear() {
        if (data_ && size_ > 0) {
            ETB_CUDA_CHECK(cudaMemset(data_, 0, size_ * sizeof(T)));
        }
    }
    
    T* data() { return data_; }
    const T* data() const { return data_; }
    size_t size() const { return size_; }
    size_t capacity() const { return capacity_; }
    size_t bytes() const { return size_ * sizeof(T); }
    bool empty() const { return size_ == 0; }
    
    // Copy from host
    void copy_from_host(const T* src, size_t count) {
        allocate(count);
        ETB_CUDA_CHECK(cudaMemcpy(data_, src, count * sizeof(T), cudaMemcpyHostToDevice));
    }
    
    void copy_from_host(const std::vector<T>& src) {
        copy_from_host(src.data(), src.size());
    }
    
    void copy_from_host(const PinnedBuffer<T>& src) {
        copy_from_host(src.data(), src.size());
    }
    
    // Async copy from pinned host memory
    void copy_from_host_async(const PinnedBuffer<T>& src, cudaStream_t stream) {
        allocate(src.size());
        ETB_CUDA_CHECK(cudaMemcpyAsync(data_, src.data(), src.bytes(), 
                                        cudaMemcpyHostToDevice, stream));
    }
    
    // Copy to host
    void copy_to_host(T* dst, size_t count) const {
        ETB_CUDA_CHECK(cudaMemcpy(dst, data_, count * sizeof(T), cudaMemcpyDeviceToHost));
    }
    
    void copy_to_host(std::vector<T>& dst) const {
        dst.resize(size_);
        copy_to_host(dst.data(), size_);
    }
    
    void copy_to_host(PinnedBuffer<T>& dst) const {
        dst.allocate(size_);
        copy_to_host(dst.data(), size_);
    }
    
    // Async copy to pinned host memory
    void copy_to_host_async(PinnedBuffer<T>& dst, cudaStream_t stream) const {
        dst.allocate(size_);
        ETB_CUDA_CHECK(cudaMemcpyAsync(dst.data(), data_, bytes(),
                                        cudaMemcpyDeviceToHost, stream));
    }

private:
    T* data_;
    size_t size_;
    size_t capacity_;
};

/**
 * GPU memory manager for the ETB library.
 * Handles allocation and management of all GPU memory resources.
 * 
 * Requirements: 9.4, 9.5, 9.6
 */
class GPUMemoryManager {
public:
    /**
     * Configuration for GPU memory allocation.
     */
    struct Config {
        size_t max_input_size;          // Maximum input buffer size
        size_t prefix_trie_capacity;    // Number of trie nodes
        size_t candidate_queue_capacity; // Number of candidates to track
        size_t work_queue_capacity;     // Work items for path generation
        int num_streams;                // Number of CUDA streams
        
        Config()
            : max_input_size(1024 * 1024)  // 1MB default
            , prefix_trie_capacity(65536)
            , candidate_queue_capacity(1024)
            , work_queue_capacity(65536)
            , num_streams(4) {}
    };
    
    GPUMemoryManager();
    explicit GPUMemoryManager(const Config& config);
    ~GPUMemoryManager();
    
    // Non-copyable, non-movable
    GPUMemoryManager(const GPUMemoryManager&) = delete;
    GPUMemoryManager& operator=(const GPUMemoryManager&) = delete;
    
    /**
     * Initialize GPU memory with the given configuration.
     * @param config Memory configuration
     * @return true if initialization succeeded
     */
    bool initialize(const Config& config);
    
    /**
     * Check if the manager is initialized.
     */
    bool is_initialized() const { return initialized_; }
    
    /**
     * Release all GPU memory.
     */
    void release();
    
    // Input buffer management (pinned host + device)
    PinnedBuffer<uint8_t>& get_pinned_input() { return pinned_input_; }
    DeviceBuffer<uint8_t>& get_device_input() { return device_input_; }
    
    /**
     * Upload input data to GPU.
     * @param data Input byte data
     * @param length Length of input
     * @param stream CUDA stream for async transfer (nullptr for sync)
     */
    void upload_input(const uint8_t* data, size_t length, cudaStream_t stream = nullptr);
    
    // Prefix trie (shared memory compatible)
    DeviceBuffer<DevicePrefixTrieNode>& get_prefix_trie() { return prefix_trie_; }
    
    /**
     * Initialize prefix trie on device.
     * @param initial_nodes Initial nodes to upload (optional)
     */
    void init_prefix_trie(const std::vector<DevicePrefixTrieNode>* initial_nodes = nullptr);
    
    // Candidate queue (global memory)
    DeviceBuffer<DeviceCandidate>& get_candidate_queue() { return candidate_queue_; }
    DeviceBuffer<uint32_t>& get_candidate_count() { return candidate_count_; }
    DeviceBuffer<float>& get_min_score() { return min_score_; }
    
    /**
     * Reset candidate queue for new extraction.
     */
    void reset_candidate_queue();
    
    /**
     * Download candidates from GPU.
     * @param candidates Output vector for candidates
     * @return Number of candidates downloaded
     */
    size_t download_candidates(std::vector<DeviceCandidate>& candidates);
    
    // Work queue for path generation
    DeviceBuffer<uint32_t>& get_work_queue() { return work_queue_; }
    DeviceBuffer<uint32_t>& get_work_queue_head() { return work_queue_head_; }
    DeviceBuffer<uint32_t>& get_work_queue_tail() { return work_queue_tail_; }
    
    // Histogram buffer for entropy calculation
    DeviceBuffer<uint32_t>& get_histogram() { return histogram_; }
    
    // CUDA streams
    cudaStream_t get_stream(int index) const;
    int num_streams() const { return static_cast<int>(streams_.size()); }
    
    /**
     * Synchronize all streams.
     */
    void synchronize_all();
    
    /**
     * Get memory usage statistics.
     */
    struct MemoryStats {
        size_t total_allocated;
        size_t input_buffer_size;
        size_t trie_size;
        size_t candidate_queue_size;
        size_t work_queue_size;
        size_t other_size;
    };
    MemoryStats get_memory_stats() const;
    
    /**
     * Get the current configuration.
     */
    const Config& get_config() const { return config_; }

private:
    Config config_;
    bool initialized_;
    
    // Pinned host memory for fast transfers
    PinnedBuffer<uint8_t> pinned_input_;
    
    // Device memory buffers
    DeviceBuffer<uint8_t> device_input_;
    DeviceBuffer<DevicePrefixTrieNode> prefix_trie_;
    DeviceBuffer<DeviceCandidate> candidate_queue_;
    DeviceBuffer<uint32_t> candidate_count_;
    DeviceBuffer<float> min_score_;
    DeviceBuffer<uint32_t> work_queue_;
    DeviceBuffer<uint32_t> work_queue_head_;
    DeviceBuffer<uint32_t> work_queue_tail_;
    DeviceBuffer<uint32_t> histogram_;
    
    // CUDA streams
    std::vector<cudaStream_t> streams_;
    
    void allocate_buffers();
    void create_streams();
    void destroy_streams();
};

/**
 * Constant memory manager for signature dictionary.
 * Signatures are stored in constant memory for fast broadcast reads.
 * 
 * Requirements: 9.4
 */
class SignatureConstantMemory {
public:
    /**
     * Upload signatures to constant memory.
     * @param signatures Vector of device signatures
     * @return true if upload succeeded
     */
    static bool upload_signatures(const std::vector<DeviceFileSignature>& signatures);
    
    /**
     * Upload footer signatures to constant memory.
     * @param footers Vector of footer signatures
     * @return true if upload succeeded
     */
    static bool upload_footers(const std::vector<DeviceFooterSignature>& footers);
    
    /**
     * Get the number of signatures in constant memory.
     */
    static uint32_t get_signature_count();
    
    /**
     * Clear constant memory signatures.
     */
    static void clear();
};

} // namespace cuda
} // namespace etb

#endif // ETB_GPU_MEMORY_CUH
