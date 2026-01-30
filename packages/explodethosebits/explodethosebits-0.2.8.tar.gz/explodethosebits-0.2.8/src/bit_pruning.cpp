#include "etb/bit_pruning.hpp"
#include <algorithm>
#include <sstream>

namespace etb {

BitPruningConfig::BitPruningConfig()
    : mode(BitPruningMode::EXHAUSTIVE)
    , bit_mask(0xFF)
    , single_bits{}
{}

BitPruningConfig::BitPruningConfig(BitPruningMode m)
    : mode(m)
    , bit_mask(0xFF)
    , single_bits{}
{
    switch (mode) {
        case BitPruningMode::EXHAUSTIVE:
            bit_mask = 0xFF;  // All 8 bits
            break;
        case BitPruningMode::MSB_ONLY:
            bit_mask = 0xF0;  // Bits 4-7 only
            break;
        case BitPruningMode::SINGLE_BIT:
            // Default to bits 0 and 7 for single-bit mode
            single_bits = {0, 7};
            bit_mask = (1 << 0) | (1 << 7);  // 0x81
            break;
        case BitPruningMode::CUSTOM:
            bit_mask = 0xFF;  // Default to all bits for custom
            break;
    }
}

BitPruningConfig::BitPruningConfig(uint8_t custom_mask)
    : mode(BitPruningMode::CUSTOM)
    , bit_mask(custom_mask)
    , single_bits{}
{}

BitPruningConfig::BitPruningConfig(uint8_t bit1, uint8_t bit2)
    : mode(BitPruningMode::SINGLE_BIT)
    , bit_mask(0)
    , single_bits{bit1, bit2}
{
    // Clamp to valid range
    bit1 = std::min(bit1, static_cast<uint8_t>(7));
    bit2 = std::min(bit2, static_cast<uint8_t>(7));
    single_bits = {bit1, bit2};
    bit_mask = (1 << bit1) | (1 << bit2);
}

bool BitPruningConfig::is_bit_allowed(uint8_t bit_pos) const {
    if (bit_pos > 7) return false;
    return (bit_mask & (1 << bit_pos)) != 0;
}

uint8_t BitPruningConfig::allowed_bit_count() const {
    uint8_t count = 0;
    uint8_t mask = bit_mask;
    while (mask) {
        count += mask & 1;
        mask >>= 1;
    }
    return count;
}

std::vector<uint8_t> BitPruningConfig::get_allowed_positions() const {
    std::vector<uint8_t> positions;
    for (uint8_t i = 0; i <= 7; ++i) {
        if (is_bit_allowed(i)) {
            positions.push_back(i);
        }
    }
    return positions;
}

uint8_t BitPruningConfig::branching_factor() const {
    return allowed_bit_count();
}

std::string BitPruningConfig::description() const {
    std::ostringstream oss;
    
    switch (mode) {
        case BitPruningMode::EXHAUSTIVE:
            oss << "Exhaustive (all 8 bits, O(8^d))";
            break;
        case BitPruningMode::MSB_ONLY:
            oss << "MSB-only (bits 4-7, O(4^d))";
            break;
        case BitPruningMode::SINGLE_BIT:
            oss << "Single-bit (bits ";
            if (single_bits.size() >= 2) {
                oss << static_cast<int>(single_bits[0]) << "," 
                    << static_cast<int>(single_bits[1]);
            }
            oss << ", O(2^d))";
            break;
        case BitPruningMode::CUSTOM:
            oss << "Custom (mask=0x" << std::hex << static_cast<int>(bit_mask) 
                << ", O(" << std::dec << static_cast<int>(allowed_bit_count()) << "^d))";
            break;
    }
    
    return oss.str();
}

bool BitPruningConfig::is_valid() const {
    // Must have at least one bit allowed
    if (bit_mask == 0) return false;
    
    // For single-bit mode, must have exactly 2 positions
    if (mode == BitPruningMode::SINGLE_BIT) {
        if (single_bits.size() != 2) return false;
        if (single_bits[0] > 7 || single_bits[1] > 7) return false;
        // Verify mask matches single_bits
        uint8_t expected_mask = (1 << single_bits[0]) | (1 << single_bits[1]);
        if (bit_mask != expected_mask) return false;
    }
    
    // For MSB_ONLY, verify mask is correct
    if (mode == BitPruningMode::MSB_ONLY && bit_mask != 0xF0) {
        return false;
    }
    
    // For EXHAUSTIVE, verify mask is correct
    if (mode == BitPruningMode::EXHAUSTIVE && bit_mask != 0xFF) {
        return false;
    }
    
    return true;
}

std::optional<BitPruningMode> parse_bit_pruning_mode(const std::string& mode_str) {
    std::string lower = mode_str;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    
    if (lower == "exhaustive") return BitPruningMode::EXHAUSTIVE;
    if (lower == "msb_only" || lower == "msb-only" || lower == "msbonly") return BitPruningMode::MSB_ONLY;
    if (lower == "single_bit" || lower == "single-bit" || lower == "singlebit") return BitPruningMode::SINGLE_BIT;
    if (lower == "custom") return BitPruningMode::CUSTOM;
    if (lower == "adaptive") return BitPruningMode::CUSTOM;  // Treat adaptive as custom
    
    return std::nullopt;
}

std::string bit_pruning_mode_to_string(BitPruningMode mode) {
    switch (mode) {
        case BitPruningMode::EXHAUSTIVE: return "exhaustive";
        case BitPruningMode::MSB_ONLY: return "msb_only";
        case BitPruningMode::SINGLE_BIT: return "single_bit";
        case BitPruningMode::CUSTOM: return "custom";
    }
    return "unknown";
}

std::optional<BitPruningConfig> create_bit_pruning_config(
    const std::string& mode_str,
    std::optional<uint8_t> custom_mask,
    std::optional<std::pair<uint8_t, uint8_t>> single_bits
) {
    auto mode = parse_bit_pruning_mode(mode_str);
    if (!mode) return std::nullopt;
    
    switch (*mode) {
        case BitPruningMode::EXHAUSTIVE:
            return BitPruningConfig(BitPruningMode::EXHAUSTIVE);
            
        case BitPruningMode::MSB_ONLY:
            return BitPruningConfig(BitPruningMode::MSB_ONLY);
            
        case BitPruningMode::SINGLE_BIT:
            if (single_bits) {
                return BitPruningConfig(single_bits->first, single_bits->second);
            }
            // Default single bits
            return BitPruningConfig(static_cast<uint8_t>(0), static_cast<uint8_t>(7));
            
        case BitPruningMode::CUSTOM:
            if (custom_mask) {
                return BitPruningConfig(*custom_mask);
            }
            // Default to exhaustive if no mask provided
            return BitPruningConfig(static_cast<uint8_t>(0xFF));
    }
    
    return std::nullopt;
}

} // namespace etb
