#ifndef ETB_BIT_EXTRACTION_HPP
#define ETB_BIT_EXTRACTION_HPP

#include "path.hpp"
#include <vector>
#include <cstdint>

namespace etb {

/**
 * Bit Extraction Engine - CPU Reference Implementation
 * 
 * Provides functions for converting between paths (bit coordinates) and byte sequences.
 * This is the core functionality for extracting and reconstructing bit combinations.
 */

/**
 * Extract a single bit from a byte array at the given coordinate.
 * @param data The input byte array
 * @param coord The bit coordinate to extract
 * @return The bit value (0 or 1)
 * @throws std::out_of_range if coordinate is out of bounds
 */
uint8_t extract_bit(const std::vector<uint8_t>& data, const BitCoordinate& coord);

/**
 * Extract a single bit from a byte array at the given coordinate.
 * @param data Pointer to the input byte array
 * @param data_length Length of the input byte array
 * @param coord The bit coordinate to extract
 * @return The bit value (0 or 1)
 * @throws std::out_of_range if coordinate is out of bounds
 */
uint8_t extract_bit(const uint8_t* data, size_t data_length, const BitCoordinate& coord);

/**
 * Extract bits at specified path coordinates from a byte array.
 * Returns the extracted bit values in order.
 * 
 * @param data The input byte array
 * @param path The path containing coordinates to extract
 * @return Vector of bit values (0 or 1) in path order
 * @throws std::out_of_range if any coordinate is out of bounds
 */
std::vector<uint8_t> extract_bits_from_path(const std::vector<uint8_t>& data, const Path& path);

/**
 * Convert a sequence of bits to a byte array.
 * Bits are packed into bytes with the first bit going to the MSB of the first byte.
 * If the number of bits is not a multiple of 8, the last byte is zero-padded on the right.
 * 
 * @param bits Vector of bit values (0 or 1)
 * @return Packed byte array
 */
std::vector<uint8_t> bits_to_bytes(const std::vector<uint8_t>& bits);

/**
 * Convert a path with associated bit values to a byte array.
 * This extracts bits from the source data at path coordinates and packs them into bytes.
 * 
 * @param source_data The source byte array to extract bits from
 * @param path The path specifying which bit coordinates to extract
 * @return Packed byte array of extracted bits
 * @throws std::out_of_range if any coordinate is out of bounds
 */
std::vector<uint8_t> path_to_bytes(const std::vector<uint8_t>& source_data, const Path& path);

/**
 * Convert a byte array to a sequence of bits.
 * Each byte is unpacked to 8 bits, MSB first.
 * 
 * @param bytes The input byte array
 * @return Vector of bit values (0 or 1)
 */
std::vector<uint8_t> bytes_to_bits(const std::vector<uint8_t>& bytes);

} // namespace etb

#endif // ETB_BIT_EXTRACTION_HPP
