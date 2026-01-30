#ifndef ETB_BIT_COORDINATE_HPP
#define ETB_BIT_COORDINATE_HPP

#include <cstdint>

namespace etb {

/**
 * Represents a coordinate in the bit extraction system.
 * Maps each bit to (byte_index, bit_position) where bit_position is in range [0,7].
 */
struct BitCoordinate {
    uint32_t byte_index;    // Index into input byte array
    uint8_t bit_position;   // Position within byte [0-7], 0 = LSB

    BitCoordinate() : byte_index(0), bit_position(0) {}
    BitCoordinate(uint32_t byte_idx, uint8_t bit_pos) 
        : byte_index(byte_idx), bit_position(bit_pos) {}

    // Comparison operators for ordering
    bool operator<(const BitCoordinate& other) const {
        return byte_index < other.byte_index;
    }

    bool operator==(const BitCoordinate& other) const {
        return byte_index == other.byte_index && bit_position == other.bit_position;
    }

    bool operator!=(const BitCoordinate& other) const {
        return !(*this == other);
    }

    /**
     * Check if this coordinate is valid for a given input length.
     * @param input_length Length of the input byte array
     * @return true if coordinate is within bounds
     */
    bool is_valid(uint32_t input_length) const {
        return byte_index < input_length && bit_position <= 7;
    }
};

} // namespace etb

#endif // ETB_BIT_COORDINATE_HPP
