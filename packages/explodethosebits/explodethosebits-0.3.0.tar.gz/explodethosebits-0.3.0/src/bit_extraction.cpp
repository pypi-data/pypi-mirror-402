#include "etb/bit_extraction.hpp"
#include <stdexcept>

namespace etb {

uint8_t extract_bit(const std::vector<uint8_t>& data, const BitCoordinate& coord) {
    return extract_bit(data.data(), data.size(), coord);
}

uint8_t extract_bit(const uint8_t* data, size_t data_length, const BitCoordinate& coord) {
    if (!coord.is_valid(static_cast<uint32_t>(data_length))) {
        throw std::out_of_range("BitCoordinate out of bounds");
    }
    
    // Extract the bit at the specified position
    // bit_position 0 = LSB, bit_position 7 = MSB
    uint8_t byte_val = data[coord.byte_index];
    return (byte_val >> coord.bit_position) & 0x01;
}

std::vector<uint8_t> extract_bits_from_path(const std::vector<uint8_t>& data, const Path& path) {
    std::vector<uint8_t> bits;
    bits.reserve(path.length());
    
    for (const auto& coord : path) {
        bits.push_back(extract_bit(data, coord));
    }
    
    return bits;
}

std::vector<uint8_t> bits_to_bytes(const std::vector<uint8_t>& bits) {
    if (bits.empty()) {
        return {};
    }
    
    // Calculate number of bytes needed (ceiling division)
    size_t num_bytes = (bits.size() + 7) / 8;
    std::vector<uint8_t> bytes(num_bytes, 0);
    
    for (size_t i = 0; i < bits.size(); ++i) {
        size_t byte_idx = i / 8;
        size_t bit_idx = 7 - (i % 8);  // MSB first packing
        
        if (bits[i]) {
            bytes[byte_idx] |= (1 << bit_idx);
        }
    }
    
    return bytes;
}

std::vector<uint8_t> path_to_bytes(const std::vector<uint8_t>& source_data, const Path& path) {
    std::vector<uint8_t> bits = extract_bits_from_path(source_data, path);
    return bits_to_bytes(bits);
}

std::vector<uint8_t> bytes_to_bits(const std::vector<uint8_t>& bytes) {
    std::vector<uint8_t> bits;
    bits.reserve(bytes.size() * 8);
    
    for (uint8_t byte_val : bytes) {
        // Unpack each byte to 8 bits, MSB first
        for (int i = 7; i >= 0; --i) {
            bits.push_back((byte_val >> i) & 0x01);
        }
    }
    
    return bits;
}

} // namespace etb
