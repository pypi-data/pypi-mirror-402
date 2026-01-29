#include "etb/cuda/signature_kernel.cuh"

namespace etb {
namespace cuda {

// ============================================================================
// Kernel Implementations
// ============================================================================

__global__ void signature_matcher_kernel(
    const uint8_t* data,
    uint32_t length,
    uint32_t max_offset,
    DeviceSignatureMatch* result
) {
    __shared__ SignatureSharedMem smem;
    
    const int tid = threadIdx.x;
    const int block_size = blockDim.x;
    
    // Initialize shared memory
    if (tid == 0) {
        smem.best_match.matched = false;
        smem.best_match.confidence = 0.0f;
        smem.best_match.format_id = 0;
        smem.best_match.match_offset = 0;
        smem.best_match.header_matched = false;
        smem.best_match.footer_matched = false;
    }
    __syncthreads();
    
    // Each thread checks different offset/signature combinations
    uint32_t sig_count = d_signature_count;
    uint32_t total_checks = (max_offset + 1) * sig_count;
    
    float local_best_score = 0.0f;
    uint32_t local_best_sig = 0;
    uint32_t local_best_offset = 0;
    bool local_header = false;
    bool local_footer = false;
    
    for (uint32_t check_idx = tid; check_idx < total_checks; check_idx += block_size) {
        uint32_t offset = check_idx / sig_count;
        uint32_t sig_idx = check_idx % sig_count;
        
        if (offset > max_offset || offset >= length) continue;
        
        if (check_signature_at_position(data, length, offset, sig_idx)) {
            const DeviceFileSignature& sig = d_signatures[sig_idx];
            
            // Check footer
            bool footer_matched = false;
            bool footer_required = false;
            if (sig_idx < d_footer_count) {
                footer_required = d_footers[sig_idx].required;
                footer_matched = check_footer_at_end(data, length, sig_idx);
            }
            
            float confidence = calculate_match_confidence(
                sig, true, footer_matched, footer_required);
            
            if (confidence > local_best_score) {
                local_best_score = confidence;
                local_best_sig = sig_idx;
                local_best_offset = offset;
                local_header = true;
                local_footer = footer_matched;
            }
        }
    }
    
    // Store local results to shared memory for reduction
    smem.match_scores[tid] = local_best_score;
    smem.match_indices[tid] = local_best_sig;
    __syncthreads();
    
    // Block-level reduction to find best match
    for (int stride = block_size / 2; stride > 0; stride /= 2) {
        if (tid < stride) {
            if (smem.match_scores[tid + stride] > smem.match_scores[tid]) {
                smem.match_scores[tid] = smem.match_scores[tid + stride];
                smem.match_indices[tid] = smem.match_indices[tid + stride];
            }
        }
        __syncthreads();
    }
    
    // Thread 0 writes final result
    if (tid == 0) {
        if (smem.match_scores[0] > 0.0f) {
            uint32_t best_sig = smem.match_indices[0];
            
            // Re-check to get all details
            for (uint32_t offset = 0; offset <= max_offset && offset < length; ++offset) {
                if (check_signature_at_position(data, length, offset, best_sig)) {
                    const DeviceFileSignature& sig = d_signatures[best_sig];
                    
                    bool footer_matched = false;
                    bool footer_required = false;
                    if (best_sig < d_footer_count) {
                        footer_required = d_footers[best_sig].required;
                        footer_matched = check_footer_at_end(data, length, best_sig);
                    }
                    
                    float confidence = calculate_match_confidence(
                        sig, true, footer_matched, footer_required);
                    
                    if (confidence == smem.match_scores[0]) {
                        result->matched = true;
                        result->format_id = sig.format_id;
                        result->confidence = confidence;
                        result->match_offset = offset;
                        result->header_matched = true;
                        result->footer_matched = footer_matched;
                        break;
                    }
                }
            }
        } else {
            result->matched = false;
            result->confidence = 0.0f;
        }
    }
}

__global__ void batch_signature_matcher_kernel(
    const uint8_t** data_ptrs,
    const uint32_t* lengths,
    uint32_t num_sequences,
    uint32_t max_offset,
    DeviceSignatureMatch* results
) {
    // Each block handles one sequence
    const uint32_t seq_idx = blockIdx.x;
    
    if (seq_idx >= num_sequences) return;
    
    const uint8_t* data = data_ptrs[seq_idx];
    uint32_t length = lengths[seq_idx];
    DeviceSignatureMatch* result = &results[seq_idx];
    
    __shared__ SignatureSharedMem smem;
    
    const int tid = threadIdx.x;
    const int block_size = blockDim.x;
    
    // Initialize
    if (tid == 0) {
        smem.best_match.matched = false;
        smem.best_match.confidence = 0.0f;
    }
    __syncthreads();
    
    uint32_t sig_count = d_signature_count;
    uint32_t total_checks = (max_offset + 1) * sig_count;
    
    float local_best_score = 0.0f;
    uint32_t local_best_sig = 0;
    
    for (uint32_t check_idx = tid; check_idx < total_checks; check_idx += block_size) {
        uint32_t offset = check_idx / sig_count;
        uint32_t sig_idx = check_idx % sig_count;
        
        if (offset > max_offset || offset >= length) continue;
        
        if (check_signature_at_position(data, length, offset, sig_idx)) {
            const DeviceFileSignature& sig = d_signatures[sig_idx];
            
            bool footer_matched = false;
            bool footer_required = false;
            if (sig_idx < d_footer_count) {
                footer_required = d_footers[sig_idx].required;
                footer_matched = check_footer_at_end(data, length, sig_idx);
            }
            
            float confidence = calculate_match_confidence(
                sig, true, footer_matched, footer_required);
            
            if (confidence > local_best_score) {
                local_best_score = confidence;
                local_best_sig = sig_idx;
            }
        }
    }
    
    smem.match_scores[tid] = local_best_score;
    smem.match_indices[tid] = local_best_sig;
    __syncthreads();
    
    // Reduction
    for (int stride = block_size / 2; stride > 0; stride /= 2) {
        if (tid < stride) {
            if (smem.match_scores[tid + stride] > smem.match_scores[tid]) {
                smem.match_scores[tid] = smem.match_scores[tid + stride];
                smem.match_indices[tid] = smem.match_indices[tid + stride];
            }
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        if (smem.match_scores[0] > 0.0f) {
            uint32_t best_sig = smem.match_indices[0];
            
            for (uint32_t offset = 0; offset <= max_offset && offset < length; ++offset) {
                if (check_signature_at_position(data, length, offset, best_sig)) {
                    const DeviceFileSignature& sig = d_signatures[best_sig];
                    
                    bool footer_matched = false;
                    bool footer_required = false;
                    if (best_sig < d_footer_count) {
                        footer_required = d_footers[best_sig].required;
                        footer_matched = check_footer_at_end(data, length, best_sig);
                    }
                    
                    float confidence = calculate_match_confidence(
                        sig, true, footer_matched, footer_required);
                    
                    if (confidence == smem.match_scores[0]) {
                        result->matched = true;
                        result->format_id = sig.format_id;
                        result->confidence = confidence;
                        result->match_offset = offset;
                        result->header_matched = true;
                        result->footer_matched = footer_matched;
                        break;
                    }
                }
            }
        } else {
            result->matched = false;
            result->confidence = 0.0f;
        }
    }
}

__global__ void signature_prefix_check_kernel(
    const uint8_t* data,
    uint32_t length,
    bool* has_potential_match
) {
    const int tid = threadIdx.x;
    
    __shared__ bool found_match;
    if (tid == 0) {
        found_match = false;
    }
    __syncthreads();
    
    if (length < 4) {
        if (tid == 0) {
            *has_potential_match = false;
        }
        return;
    }
    
    uint32_t sig_count = d_signature_count;
    
    // Each thread checks one signature
    if (tid < sig_count) {
        const DeviceFileSignature& sig = d_signatures[tid];
        
        // Check first 4 bytes
        uint8_t check_len = sig.length < 4 ? sig.length : 4;
        bool matches = true;
        
        for (uint8_t j = 0; j < check_len && matches; ++j) {
            uint8_t masked_data = data[j] & sig.mask[j];
            uint8_t masked_sig = sig.magic_bytes[j] & sig.mask[j];
            if (masked_data != masked_sig) {
                matches = false;
            }
        }
        
        if (matches) {
            found_match = true;
        }
    }
    
    __syncthreads();
    
    if (tid == 0) {
        *has_potential_match = found_match;
    }
}

// ============================================================================
// Host-side Launcher Implementation
// ============================================================================

SignatureMatcherKernel::SignatureMatcherKernel() : configured_(false) {}

SignatureMatcherKernel::~SignatureMatcherKernel() {}

void SignatureMatcherKernel::configure(int device_id) {
    kernel_config_ = get_optimal_config(device_id, 256, sizeof(SignatureSharedMem));
    configured_ = true;
}

void SignatureMatcherKernel::match(const uint8_t* data, uint32_t length, uint32_t max_offset,
                                    DeviceSignatureMatch* result, cudaStream_t stream) {
    if (!configured_) {
        configure(0);
    }
    
    // Single block for single sequence
    int threads = 256;
    
    signature_matcher_kernel<<<1, threads, sizeof(SignatureSharedMem), stream>>>(
        data, length, max_offset, result
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

void SignatureMatcherKernel::match_batch(const uint8_t** data_ptrs, const uint32_t* lengths,
                                          uint32_t num_sequences, uint32_t max_offset,
                                          DeviceSignatureMatch* results, cudaStream_t stream) {
    if (!configured_) {
        configure(0);
    }
    
    // One block per sequence
    int threads = 256;
    int blocks = num_sequences;
    
    batch_signature_matcher_kernel<<<blocks, threads, sizeof(SignatureSharedMem), stream>>>(
        data_ptrs, lengths, num_sequences, max_offset, results
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

void SignatureMatcherKernel::prefix_check(const uint8_t* data, uint32_t length,
                                           bool* has_potential, cudaStream_t stream) {
    if (!configured_) {
        configure(0);
    }
    
    // Single block with enough threads for all signatures
    int threads = MAX_SIGNATURES;
    
    signature_prefix_check_kernel<<<1, threads, 0, stream>>>(
        data, length, has_potential
    );
    
    ETB_CUDA_CHECK(cudaGetLastError());
}

} // namespace cuda
} // namespace etb
