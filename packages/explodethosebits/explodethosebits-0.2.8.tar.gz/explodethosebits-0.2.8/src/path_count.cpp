#include "etb/path_count.hpp"
#include <cmath>
#include <limits>

namespace etb {

uint8_t count_bits_in_mask(uint8_t mask) {
    uint8_t count = 0;
    while (mask) {
        count += mask & 1;
        mask >>= 1;
    }
    return count;
}

std::optional<uint64_t> exact_path_count(uint32_t input_length, uint8_t bits_per_byte) {
    if (input_length == 0 || bits_per_byte == 0) {
        return 0;
    }
    
    // Path count = (1 + bits_per_byte)^n - 1
    // Check for overflow during computation
    
    uint64_t base = 1 + bits_per_byte;  // 9 for full 8 bits
    uint64_t result = 1;
    
    for (uint32_t i = 0; i < input_length; ++i) {
        // Check for overflow before multiplication
        if (result > std::numeric_limits<uint64_t>::max() / base) {
            return std::nullopt;  // Would overflow
        }
        result *= base;
    }
    
    // Subtract 1 for empty path (result is at least 'base' so no underflow)
    return result - 1;
}

double log10_path_count(uint32_t input_length, uint8_t bits_per_byte) {
    if (input_length == 0 || bits_per_byte == 0) {
        return 0.0;
    }
    
    // log10((1 + bits_per_byte)^n - 1) ≈ n * log10(1 + bits_per_byte) for large n
    double base = 1.0 + bits_per_byte;
    return input_length * std::log10(base);
}

PathCountResult estimate_path_count(uint32_t input_length, 
                                    uint8_t bits_per_byte,
                                    uint64_t threshold) {
    PathCountResult result;
    result.log_count = log10_path_count(input_length, bits_per_byte);
    
    auto exact = exact_path_count(input_length, bits_per_byte);
    
    if (exact.has_value()) {
        result.estimated_count = exact.value();
        result.is_exact = true;
    } else {
        // Overflow - use max value as estimate
        result.estimated_count = std::numeric_limits<uint64_t>::max();
        result.is_exact = false;
    }
    
    if (threshold > 0) {
        if (result.is_exact) {
            result.exceeds_threshold = result.estimated_count > threshold;
        } else {
            // Use log comparison for overflow cases
            double log_threshold = std::log10(static_cast<double>(threshold));
            result.exceeds_threshold = result.log_count > log_threshold;
        }
    } else {
        result.exceeds_threshold = false;
    }
    
    return result;
}

bool path_count_exceeds_threshold(uint32_t input_length,
                                  uint8_t bits_per_byte,
                                  uint64_t threshold) {
    if (threshold == 0) {
        return input_length > 0 && bits_per_byte > 0;
    }
    
    // Use logarithmic comparison for efficiency
    double log_count = log10_path_count(input_length, bits_per_byte);
    double log_threshold = std::log10(static_cast<double>(threshold));
    
    return log_count > log_threshold;
}

} // namespace etb
