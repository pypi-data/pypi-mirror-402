#ifndef ETB_CUDA_COMMON_CUH
#define ETB_CUDA_COMMON_CUH

#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace etb {
namespace cuda {

// Error checking macro
#define ETB_CUDA_CHECK(call) \
    do { \
        cudaError_t err = call; \
        if (err != cudaSuccess) { \
            throw std::runtime_error(std::string("CUDA error: ") + \
                cudaGetErrorString(err) + " at " + __FILE__ + ":" + std::to_string(__LINE__)); \
        } \
    } while(0)

// Architecture-specific constants
namespace arch {
    // SM 90 (Hopper) configuration
    constexpr int HOPPER_SM = 90;
    constexpr int HOPPER_THREADS_PER_BLOCK = 256;
    constexpr int HOPPER_SHARED_MEM_SIZE = 48 * 1024;  // 48KB default
    constexpr int HOPPER_MAX_SHARED_MEM = 228 * 1024;  // 228KB max with opt-in
    
    // SM 100 (Blackwell) configuration
    constexpr int BLACKWELL_SM = 100;
    constexpr int BLACKWELL_THREADS_PER_BLOCK = 512;
    constexpr int BLACKWELL_SHARED_MEM_SIZE = 64 * 1024;  // 64KB default
    constexpr int BLACKWELL_MAX_SHARED_MEM = 256 * 1024;  // 256KB max with opt-in
    
    // Common constants
    constexpr int WARP_SIZE = 32;
    constexpr int MAX_GRID_DIM = 65535;
}

// Maximum sizes for constant memory structures
constexpr size_t MAX_SIGNATURES = 256;
constexpr size_t MAX_SIGNATURE_LENGTH = 32;
constexpr size_t MAX_FORMAT_NAME_LENGTH = 32;

// GPU-compatible bit coordinate (matches CPU version)
struct alignas(8) DeviceBitCoordinate {
    uint32_t byte_index;
    uint8_t bit_position;
    uint8_t padding[3];  // Alignment padding
    
    __host__ __device__ DeviceBitCoordinate() 
        : byte_index(0), bit_position(0), padding{0, 0, 0} {}
    
    __host__ __device__ DeviceBitCoordinate(uint32_t byte_idx, uint8_t bit_pos)
        : byte_index(byte_idx), bit_position(bit_pos), padding{0, 0, 0} {}
    
    __host__ __device__ bool is_valid(uint32_t input_length) const {
        return byte_index < input_length && bit_position <= 7;
    }
};

// GPU-compatible path structure
struct DevicePath {
    DeviceBitCoordinate* coordinates;
    uint32_t length;
    uint32_t capacity;
    
    __host__ __device__ DevicePath() 
        : coordinates(nullptr), length(0), capacity(0) {}
};

// GPU-compatible file signature for constant memory
// Note: No constructor to allow __constant__ memory usage
struct alignas(64) DeviceFileSignature {
    uint8_t magic_bytes[MAX_SIGNATURE_LENGTH];
    uint8_t mask[MAX_SIGNATURE_LENGTH];
    uint8_t length;
    uint16_t offset;
    uint16_t format_id;
    float base_confidence;
    uint8_t padding[1];  // Alignment
};

// GPU-compatible footer signature
// Note: No constructor to allow __constant__ memory usage
struct DeviceFooterSignature {
    uint8_t magic_bytes[MAX_SIGNATURE_LENGTH];
    uint8_t length;
    bool required;
    uint8_t padding[2];
};

// GPU-compatible heuristic result
struct DeviceHeuristicResult {
    float entropy;
    float printable_ratio;
    float control_char_ratio;
    uint32_t max_null_run;
    float utf8_validity;
    float composite_score;
    
    __host__ __device__ DeviceHeuristicResult()
        : entropy(0.0f), printable_ratio(0.0f), control_char_ratio(0.0f)
        , max_null_run(0), utf8_validity(0.0f), composite_score(0.0f) {}
};

// GPU-compatible heuristic weights
struct DeviceHeuristicWeights {
    float entropy_weight;
    float printable_weight;
    float control_char_weight;
    float null_run_weight;
    float utf8_weight;
    
    __host__ __device__ DeviceHeuristicWeights()
        : entropy_weight(0.25f), printable_weight(0.25f)
        , control_char_weight(0.15f), null_run_weight(0.15f)
        , utf8_weight(0.20f) {}
};

// GPU-compatible scoring weights
struct DeviceScoringWeights {
    float signature_weight;
    float heuristic_weight;
    float length_weight;
    float structure_weight;
    
    __host__ __device__ DeviceScoringWeights()
        : signature_weight(0.40f), heuristic_weight(0.30f)
        , length_weight(0.15f), structure_weight(0.15f) {}
};

// Prefix trie node status
enum class DevicePrefixStatus : uint8_t {
    UNKNOWN = 0,
    VALID = 1,
    PRUNED = 2
};

// GPU-compatible prefix trie node
struct alignas(16) DevicePrefixTrieNode {
    uint8_t reconstructed_byte;
    DevicePrefixStatus status;
    uint8_t padding[2];
    float best_score;
    uint32_t children_offset;
    uint32_t visit_count;
    
    __host__ __device__ DevicePrefixTrieNode()
        : reconstructed_byte(0), status(DevicePrefixStatus::UNKNOWN)
        , padding{0, 0}, best_score(0.0f), children_offset(0), visit_count(0) {}
};

// Signature match result
struct DeviceSignatureMatch {
    bool matched;
    uint16_t format_id;
    float confidence;
    uint32_t match_offset;
    bool header_matched;
    bool footer_matched;
    uint8_t padding[2];
    
    __host__ __device__ DeviceSignatureMatch()
        : matched(false), format_id(0), confidence(0.0f)
        , match_offset(0), header_matched(false), footer_matched(false)
        , padding{0, 0} {}
};

// Candidate structure for GPU
struct DeviceCandidate {
    uint8_t* data;
    uint32_t data_length;
    uint16_t format_id;
    float confidence;
    float composite_score;
    DeviceHeuristicResult heuristics;
    DeviceSignatureMatch signature_match;
    
    __host__ __device__ DeviceCandidate()
        : data(nullptr), data_length(0), format_id(0)
        , confidence(0.0f), composite_score(0.0f) {}
};

// Early stopping configuration
struct DeviceEarlyStoppingConfig {
    uint32_t level1_bytes;
    uint32_t level2_bytes;
    uint32_t level3_bytes;
    float entropy_min;
    float entropy_max;
    float prune_threshold;
    bool adaptive_thresholds;
    uint8_t padding[3];
    
    __host__ __device__ DeviceEarlyStoppingConfig()
        : level1_bytes(4), level2_bytes(8), level3_bytes(16)
        , entropy_min(0.1f), entropy_max(7.9f), prune_threshold(0.3f)
        , adaptive_thresholds(true), padding{0, 0, 0} {}
};

// Bit pruning mode
enum class DeviceBitPruningMode : uint8_t {
    EXHAUSTIVE = 0,
    MSB_ONLY = 1,
    SINGLE_BIT = 2,
    CUSTOM = 3
};

// Bit pruning configuration
struct DeviceBitPruningConfig {
    DeviceBitPruningMode mode;
    uint8_t bit_mask;  // Bitmask for allowed bit positions
    uint8_t padding[2];
    
    __host__ __device__ DeviceBitPruningConfig()
        : mode(DeviceBitPruningMode::EXHAUSTIVE), bit_mask(0xFF), padding{0, 0} {}
};

// Kernel configuration
struct KernelConfig {
    int threads_per_block;
    int blocks_per_grid;
    size_t shared_mem_size;
    int sm_version;
    
    KernelConfig()
        : threads_per_block(256), blocks_per_grid(1)
        , shared_mem_size(0), sm_version(0) {}
};

// Device information
struct DeviceInfo {
    int device_id;
    int sm_version;
    size_t total_global_mem;
    size_t shared_mem_per_block;
    size_t shared_mem_per_multiprocessor;
    int multiprocessor_count;
    int max_threads_per_block;
    int warp_size;
    bool supports_cooperative_groups;
    
    DeviceInfo()
        : device_id(-1), sm_version(0), total_global_mem(0)
        , shared_mem_per_block(0), shared_mem_per_multiprocessor(0)
        , multiprocessor_count(0), max_threads_per_block(0)
        , warp_size(32), supports_cooperative_groups(false) {}
};

// Get device information
DeviceInfo get_device_info(int device_id = 0);

// Check if CUDA is available
bool is_cuda_available();

// Get optimal kernel configuration for the current device
KernelConfig get_optimal_config(int device_id, size_t work_items, size_t shared_mem_required = 0);

} // namespace cuda
} // namespace etb

#endif // ETB_CUDA_COMMON_CUH
