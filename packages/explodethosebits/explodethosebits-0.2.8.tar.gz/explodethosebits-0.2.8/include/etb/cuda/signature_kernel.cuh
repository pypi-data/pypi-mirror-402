#ifndef ETB_SIGNATURE_KERNEL_CUH
#define ETB_SIGNATURE_KERNEL_CUH

#include "cuda_common.cuh"
#include "gpu_memory.cuh"

namespace etb {
namespace cuda {

// Constant memory declarations (defined in gpu_memory.cu)
extern __constant__ DeviceFileSignature d_signatures[MAX_SIGNATURES];
extern __constant__ DeviceFooterSignature d_footers[MAX_SIGNATURES];
extern __constant__ uint32_t d_signature_count;
extern __constant__ uint32_t d_footer_count;

/**
 * Shared memory structure for signature matching.
 */
struct SignatureSharedMem {
    // Best match found by this block
    DeviceSignatureMatch best_match;
    
    // Reduction scratch space
    float match_scores[256];
    uint32_t match_indices[256];
};

/**
 * Signature matcher CUDA kernel.
 * 
 * Performs parallel sliding window matching using constant memory
 * for signature broadcast.
 * 
 * Requirements: 9.4
 * 
 * @param data Input byte data
 * @param length Length of data
 * @param max_offset Maximum offset to search for headers
 * @param result Output signature match result
 */
__global__ void signature_matcher_kernel(
    const uint8_t* data,
    uint32_t length,
    uint32_t max_offset,
    DeviceSignatureMatch* result
);

/**
 * Batch signature matching kernel.
 * Each block handles one byte sequence.
 * 
 * @param data_ptrs Array of pointers to byte sequences
 * @param lengths Array of sequence lengths
 * @param num_sequences Number of sequences
 * @param max_offset Maximum offset to search
 * @param results Output array of match results
 */
__global__ void batch_signature_matcher_kernel(
    const uint8_t** data_ptrs,
    const uint32_t* lengths,
    uint32_t num_sequences,
    uint32_t max_offset,
    DeviceSignatureMatch* results
);

/**
 * Quick signature prefix check kernel.
 * Checks only the first few bytes for fast rejection.
 * 
 * @param data Input byte data
 * @param length Length of data
 * @param has_potential_match Output flag indicating if any signature could match
 */
__global__ void signature_prefix_check_kernel(
    const uint8_t* data,
    uint32_t length,
    bool* has_potential_match
);

/**
 * Host-side launcher for signature matching kernels.
 */
class SignatureMatcherKernel {
public:
    SignatureMatcherKernel();
    ~SignatureMatcherKernel();
    
    /**
     * Configure the kernel for a specific device.
     * @param device_id CUDA device ID
     */
    void configure(int device_id);
    
    /**
     * Match signatures against a byte sequence.
     * @param data Device pointer to byte data
     * @param length Length of data
     * @param max_offset Maximum offset to search
     * @param result Device pointer to result
     * @param stream CUDA stream
     */
    void match(const uint8_t* data, uint32_t length, uint32_t max_offset,
               DeviceSignatureMatch* result, cudaStream_t stream = nullptr);
    
    /**
     * Match signatures against multiple byte sequences.
     * @param data_ptrs Device array of pointers
     * @param lengths Device array of lengths
     * @param num_sequences Number of sequences
     * @param max_offset Maximum offset to search
     * @param results Device array of results
     * @param stream CUDA stream
     */
    void match_batch(const uint8_t** data_ptrs, const uint32_t* lengths,
                     uint32_t num_sequences, uint32_t max_offset,
                     DeviceSignatureMatch* results, cudaStream_t stream = nullptr);
    
    /**
     * Quick prefix check for early rejection.
     * @param data Device pointer to byte data
     * @param length Length of data
     * @param has_potential Device pointer to result flag
     * @param stream CUDA stream
     */
    void prefix_check(const uint8_t* data, uint32_t length,
                      bool* has_potential, cudaStream_t stream = nullptr);
    
    /**
     * Get the kernel configuration.
     */
    const KernelConfig& get_config() const { return kernel_config_; }

private:
    KernelConfig kernel_config_;
    bool configured_;
};

// ============================================================================
// Device Functions
// ============================================================================

/**
 * Check if signature matches at a specific position.
 * Uses constant memory for signature data.
 */
__device__ inline bool check_signature_at_position(
    const uint8_t* data,
    uint32_t data_length,
    uint32_t position,
    uint32_t sig_idx
) {
    const DeviceFileSignature& sig = d_signatures[sig_idx];
    
    // Check if signature fits at this position
    if (position + sig.offset + sig.length > data_length) {
        return false;
    }
    
    // Compare bytes with mask
    const uint8_t* check_pos = data + position + sig.offset;
    for (uint8_t i = 0; i < sig.length; ++i) {
        uint8_t masked_data = check_pos[i] & sig.mask[i];
        uint8_t masked_sig = sig.magic_bytes[i] & sig.mask[i];
        if (masked_data != masked_sig) {
            return false;
        }
    }
    
    return true;
}

/**
 * Check if footer matches at end of data.
 */
__device__ inline bool check_footer_at_end(
    const uint8_t* data,
    uint32_t data_length,
    uint32_t footer_idx
) {
    const DeviceFooterSignature& footer = d_footers[footer_idx];
    
    if (footer.length == 0 || footer.length > data_length) {
        return false;
    }
    
    const uint8_t* footer_pos = data + data_length - footer.length;
    for (uint8_t i = 0; i < footer.length; ++i) {
        if (footer_pos[i] != footer.magic_bytes[i]) {
            return false;
        }
    }
    
    return true;
}

/**
 * Calculate match confidence based on match quality.
 */
__device__ inline float calculate_match_confidence(
    const DeviceFileSignature& sig,
    bool header_matched,
    bool footer_matched,
    bool footer_required
) {
    float confidence = sig.base_confidence;
    
    if (!header_matched) {
        return 0.0f;
    }
    
    if (footer_matched) {
        // Boost confidence for header + footer match
        confidence = fminf(confidence + 0.1f, 1.0f);
    } else if (footer_required) {
        // Reduce confidence if footer was required but not found
        confidence *= 0.7f;
    }
    
    return confidence;
}

/**
 * Warp-level reduction to find best match.
 */
__device__ inline void warp_reduce_best_match(
    float& best_score,
    uint32_t& best_idx,
    uint32_t& best_offset,
    bool& best_header,
    bool& best_footer
) {
    for (int offset = 16; offset > 0; offset /= 2) {
        float other_score = __shfl_down_sync(0xFFFFFFFF, best_score, offset);
        uint32_t other_idx = __shfl_down_sync(0xFFFFFFFF, best_idx, offset);
        uint32_t other_offset = __shfl_down_sync(0xFFFFFFFF, best_offset, offset);
        bool other_header = __shfl_down_sync(0xFFFFFFFF, best_header ? 1 : 0, offset);
        bool other_footer = __shfl_down_sync(0xFFFFFFFF, best_footer ? 1 : 0, offset);
        
        if (other_score > best_score) {
            best_score = other_score;
            best_idx = other_idx;
            best_offset = other_offset;
            best_header = other_header;
            best_footer = other_footer;
        }
    }
}

/**
 * Inline signature check for use within other kernels.
 * Checks first 4 bytes against all signatures for quick rejection.
 */
__device__ inline bool quick_signature_check(const uint8_t* data, uint32_t length) {
    if (length < 4) return false;
    
    uint32_t sig_count = d_signature_count;
    
    for (uint32_t i = 0; i < sig_count; ++i) {
        const DeviceFileSignature& sig = d_signatures[i];
        
        // Only check first 4 bytes for quick match
        uint8_t check_len = sig.length < 4 ? sig.length : 4;
        bool matches = true;
        
        for (uint8_t j = 0; j < check_len && matches; ++j) {
            uint8_t masked_data = data[j] & sig.mask[j];
            uint8_t masked_sig = sig.magic_bytes[j] & sig.mask[j];
            if (masked_data != masked_sig) {
                matches = false;
            }
        }
        
        if (matches) return true;
    }
    
    return false;
}

/**
 * Full signature match for inline use.
 * Returns the best matching signature index or -1 if no match.
 */
__device__ inline DeviceSignatureMatch inline_signature_match(
    const uint8_t* data,
    uint32_t length,
    uint32_t max_offset
) {
    DeviceSignatureMatch result;
    result.matched = false;
    result.confidence = 0.0f;
    
    uint32_t sig_count = d_signature_count;
    
    for (uint32_t offset = 0; offset <= max_offset && offset < length; ++offset) {
        for (uint32_t i = 0; i < sig_count; ++i) {
            if (check_signature_at_position(data, length, offset, i)) {
                const DeviceFileSignature& sig = d_signatures[i];
                
                // Check footer if available
                bool footer_matched = false;
                bool footer_required = false;
                if (i < d_footer_count) {
                    footer_required = d_footers[i].required;
                    footer_matched = check_footer_at_end(data, length, i);
                }
                
                float confidence = calculate_match_confidence(
                    sig, true, footer_matched, footer_required);
                
                if (confidence > result.confidence) {
                    result.matched = true;
                    result.format_id = sig.format_id;
                    result.confidence = confidence;
                    result.match_offset = offset;
                    result.header_matched = true;
                    result.footer_matched = footer_matched;
                }
            }
        }
    }
    
    return result;
}

} // namespace cuda
} // namespace etb

#endif // ETB_SIGNATURE_KERNEL_CUH
