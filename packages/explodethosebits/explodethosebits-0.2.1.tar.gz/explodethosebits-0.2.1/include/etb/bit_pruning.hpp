#ifndef ETB_BIT_PRUNING_HPP
#define ETB_BIT_PRUNING_HPP

#include <cstdint>
#include <string>
#include <vector>
#include <optional>

namespace etb {

/**
 * Bit pruning modes that control which bit positions are explored.
 * These modes reduce the search space from O(8^d) to smaller complexities.
 */
enum class BitPruningMode {
    EXHAUSTIVE,     // All 8 bit positions (O(8^d)) - bit_mask = 0xFF
    MSB_ONLY,       // Only bits 4-7 (O(4^d)) - bit_mask = 0xF0
    SINGLE_BIT,     // Only 2 configured bit positions (O(2^d))
    CUSTOM          // User-defined bit mask
};

/**
 * Configuration for the bit pruning system.
 * Controls which bit positions are allowed during path generation.
 */
struct BitPruningConfig {
    BitPruningMode mode;
    uint8_t bit_mask;                   // Bitmask of allowed positions (bit N set = position N allowed)
    std::vector<uint8_t> single_bits;   // For SINGLE_BIT mode: which 2 positions to use
    
    /**
     * Default constructor - exhaustive mode (all bits allowed).
     */
    BitPruningConfig();
    
    /**
     * Construct with a specific mode.
     */
    explicit BitPruningConfig(BitPruningMode mode);
    
    /**
     * Construct with a custom bit mask.
     */
    explicit BitPruningConfig(uint8_t custom_mask);
    
    /**
     * Construct single-bit mode with specified positions.
     * @param bit1 First bit position (0-7)
     * @param bit2 Second bit position (0-7)
     */
    BitPruningConfig(uint8_t bit1, uint8_t bit2);
    
    /**
     * Check if a bit position is allowed by this configuration.
     * @param bit_pos Bit position (0-7)
     * @return true if the position is allowed
     */
    bool is_bit_allowed(uint8_t bit_pos) const;
    
    /**
     * Get the number of allowed bit positions.
     * @return Count of set bits in the mask
     */
    uint8_t allowed_bit_count() const;
    
    /**
     * Get all allowed bit positions.
     * @return Vector of allowed positions (0-7)
     */
    std::vector<uint8_t> get_allowed_positions() const;
    
    /**
     * Get the effective branching factor for complexity analysis.
     * @return Number of choices per byte level
     */
    uint8_t branching_factor() const;
    
    /**
     * Get a human-readable description of the configuration.
     */
    std::string description() const;
    
    /**
     * Validate the configuration.
     * @return true if configuration is valid
     */
    bool is_valid() const;
    
    /**
     * Get the bit mask for use with PathGeneratorConfig.
     */
    uint8_t get_mask() const { return bit_mask; }
};

/**
 * Parse a bit pruning mode from a string.
 * @param mode_str Mode string: "exhaustive", "msb_only", "single_bit", "custom"
 * @return Parsed mode, or std::nullopt if invalid
 */
std::optional<BitPruningMode> parse_bit_pruning_mode(const std::string& mode_str);

/**
 * Convert a bit pruning mode to string.
 */
std::string bit_pruning_mode_to_string(BitPruningMode mode);

/**
 * Create a BitPruningConfig from a mode string and optional mask.
 * @param mode_str Mode string
 * @param custom_mask Optional custom mask (used when mode is "custom")
 * @param single_bits Optional single bit positions (used when mode is "single_bit")
 * @return Configured BitPruningConfig, or std::nullopt if invalid
 */
std::optional<BitPruningConfig> create_bit_pruning_config(
    const std::string& mode_str,
    std::optional<uint8_t> custom_mask = std::nullopt,
    std::optional<std::pair<uint8_t, uint8_t>> single_bits = std::nullopt
);

} // namespace etb

#endif // ETB_BIT_PRUNING_HPP
