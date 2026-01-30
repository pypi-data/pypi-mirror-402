#ifndef ETB_PATH_COUNT_HPP
#define ETB_PATH_COUNT_HPP

#include <cstdint>
#include <optional>

namespace etb {

/**
 * Path count estimation utilities.
 * 
 * For n bytes with 8 bits each, the total number of forward-only paths is:
 * Sum over all path lengths k from 1 to n of: C(n,k) * 8^k
 * 
 * This equals (1+8)^n - 1 = 9^n - 1 (by binomial theorem, minus empty path)
 * 
 * With bit masking (m allowed bits per byte):
 * Total paths = (1+m)^n - 1
 */

/**
 * Result of path count estimation.
 */
struct PathCountResult {
    uint64_t estimated_count;       // Estimated total path count
    bool is_exact;                  // True if count is exact (not overflow)
    bool exceeds_threshold;         // True if count exceeds the given threshold
    double log_count;               // log10 of the count (for large values)
};

/**
 * Calculate the exact number of paths for small inputs.
 * Returns nullopt if the calculation would overflow uint64_t.
 * 
 * @param input_length Number of bytes in input
 * @param bits_per_byte Number of allowed bit positions per byte (default 8)
 * @return Exact path count or nullopt on overflow
 */
std::optional<uint64_t> exact_path_count(uint32_t input_length, uint8_t bits_per_byte = 8);

/**
 * Estimate the path count with overflow detection.
 * 
 * @param input_length Number of bytes in input
 * @param bits_per_byte Number of allowed bit positions per byte (default 8)
 * @param threshold Optional threshold for early bailout check
 * @return PathCountResult with estimation details
 */
PathCountResult estimate_path_count(uint32_t input_length, 
                                    uint8_t bits_per_byte = 8,
                                    uint64_t threshold = 0);

/**
 * Check if path count exceeds a threshold without computing exact count.
 * Uses logarithmic comparison for efficiency with large values.
 * 
 * @param input_length Number of bytes in input
 * @param bits_per_byte Number of allowed bit positions per byte
 * @param threshold The threshold to check against
 * @return true if estimated count exceeds threshold
 */
bool path_count_exceeds_threshold(uint32_t input_length,
                                  uint8_t bits_per_byte,
                                  uint64_t threshold);

/**
 * Calculate the log10 of the path count.
 * Useful for displaying very large counts.
 * 
 * @param input_length Number of bytes in input
 * @param bits_per_byte Number of allowed bit positions per byte
 * @return log10 of the path count
 */
double log10_path_count(uint32_t input_length, uint8_t bits_per_byte = 8);

/**
 * Count the number of set bits in a byte (popcount).
 * Used to determine bits_per_byte from a bit mask.
 * 
 * @param mask The bit mask
 * @return Number of set bits
 */
uint8_t count_bits_in_mask(uint8_t mask);

} // namespace etb

#endif // ETB_PATH_COUNT_HPP
