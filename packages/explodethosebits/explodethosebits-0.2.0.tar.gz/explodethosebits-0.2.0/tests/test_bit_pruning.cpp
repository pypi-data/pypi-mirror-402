#include <gtest/gtest.h>
#include "etb/bit_pruning.hpp"

using namespace etb;

// Test default constructor creates exhaustive mode
TEST(BitPruningConfigTest, DefaultConstructorExhaustive) {
    BitPruningConfig config;
    EXPECT_EQ(config.mode, BitPruningMode::EXHAUSTIVE);
    EXPECT_EQ(config.bit_mask, 0xFF);
    EXPECT_EQ(config.allowed_bit_count(), 8);
    EXPECT_TRUE(config.is_valid());
}

// Test exhaustive mode allows all bits
TEST(BitPruningConfigTest, ExhaustiveModeAllBits) {
    BitPruningConfig config(BitPruningMode::EXHAUSTIVE);
    
    for (uint8_t i = 0; i <= 7; ++i) {
        EXPECT_TRUE(config.is_bit_allowed(i)) << "Bit " << static_cast<int>(i) << " should be allowed";
    }
    EXPECT_EQ(config.branching_factor(), 8);
}

// Test MSB-only mode allows only bits 4-7
TEST(BitPruningConfigTest, MSBOnlyModeBits4to7) {
    BitPruningConfig config(BitPruningMode::MSB_ONLY);
    
    EXPECT_EQ(config.bit_mask, 0xF0);
    
    // Bits 0-3 should NOT be allowed
    for (uint8_t i = 0; i <= 3; ++i) {
        EXPECT_FALSE(config.is_bit_allowed(i)) << "Bit " << static_cast<int>(i) << " should NOT be allowed";
    }
    
    // Bits 4-7 should be allowed
    for (uint8_t i = 4; i <= 7; ++i) {
        EXPECT_TRUE(config.is_bit_allowed(i)) << "Bit " << static_cast<int>(i) << " should be allowed";
    }
    
    EXPECT_EQ(config.branching_factor(), 4);
    EXPECT_TRUE(config.is_valid());
}

// Test single-bit mode with specific positions
TEST(BitPruningConfigTest, SingleBitModeSpecificPositions) {
    BitPruningConfig config(2, 5);  // Bits 2 and 5
    
    EXPECT_EQ(config.mode, BitPruningMode::SINGLE_BIT);
    EXPECT_EQ(config.bit_mask, (1 << 2) | (1 << 5));  // 0x24
    
    // Only bits 2 and 5 should be allowed
    for (uint8_t i = 0; i <= 7; ++i) {
        if (i == 2 || i == 5) {
            EXPECT_TRUE(config.is_bit_allowed(i)) << "Bit " << static_cast<int>(i) << " should be allowed";
        } else {
            EXPECT_FALSE(config.is_bit_allowed(i)) << "Bit " << static_cast<int>(i) << " should NOT be allowed";
        }
    }
    
    EXPECT_EQ(config.branching_factor(), 2);
    EXPECT_TRUE(config.is_valid());
}

// Test custom mask
TEST(BitPruningConfigTest, CustomMask) {
    BitPruningConfig config(static_cast<uint8_t>(0x55));  // Bits 0, 2, 4, 6
    
    EXPECT_EQ(config.mode, BitPruningMode::CUSTOM);
    EXPECT_EQ(config.bit_mask, 0x55);
    
    EXPECT_TRUE(config.is_bit_allowed(0));
    EXPECT_FALSE(config.is_bit_allowed(1));
    EXPECT_TRUE(config.is_bit_allowed(2));
    EXPECT_FALSE(config.is_bit_allowed(3));
    EXPECT_TRUE(config.is_bit_allowed(4));
    EXPECT_FALSE(config.is_bit_allowed(5));
    EXPECT_TRUE(config.is_bit_allowed(6));
    EXPECT_FALSE(config.is_bit_allowed(7));
    
    EXPECT_EQ(config.branching_factor(), 4);
    EXPECT_TRUE(config.is_valid());
}

// Test get_allowed_positions
TEST(BitPruningConfigTest, GetAllowedPositions) {
    BitPruningConfig config(BitPruningMode::MSB_ONLY);
    
    auto positions = config.get_allowed_positions();
    ASSERT_EQ(positions.size(), 4);
    EXPECT_EQ(positions[0], 4);
    EXPECT_EQ(positions[1], 5);
    EXPECT_EQ(positions[2], 6);
    EXPECT_EQ(positions[3], 7);
}

// Test invalid bit position
TEST(BitPruningConfigTest, InvalidBitPosition) {
    BitPruningConfig config;
    EXPECT_FALSE(config.is_bit_allowed(8));
    EXPECT_FALSE(config.is_bit_allowed(255));
}

// Test zero mask is invalid
TEST(BitPruningConfigTest, ZeroMaskInvalid) {
    BitPruningConfig config(static_cast<uint8_t>(0x00));
    EXPECT_FALSE(config.is_valid());
}

// Test parse_bit_pruning_mode
TEST(BitPruningModeParseTest, ValidModes) {
    EXPECT_EQ(parse_bit_pruning_mode("exhaustive"), BitPruningMode::EXHAUSTIVE);
    EXPECT_EQ(parse_bit_pruning_mode("EXHAUSTIVE"), BitPruningMode::EXHAUSTIVE);
    EXPECT_EQ(parse_bit_pruning_mode("msb_only"), BitPruningMode::MSB_ONLY);
    EXPECT_EQ(parse_bit_pruning_mode("msb-only"), BitPruningMode::MSB_ONLY);
    EXPECT_EQ(parse_bit_pruning_mode("MSB_ONLY"), BitPruningMode::MSB_ONLY);
    EXPECT_EQ(parse_bit_pruning_mode("single_bit"), BitPruningMode::SINGLE_BIT);
    EXPECT_EQ(parse_bit_pruning_mode("single-bit"), BitPruningMode::SINGLE_BIT);
    EXPECT_EQ(parse_bit_pruning_mode("custom"), BitPruningMode::CUSTOM);
    EXPECT_EQ(parse_bit_pruning_mode("adaptive"), BitPruningMode::CUSTOM);
}

// Test parse_bit_pruning_mode invalid
TEST(BitPruningModeParseTest, InvalidMode) {
    EXPECT_FALSE(parse_bit_pruning_mode("invalid").has_value());
    EXPECT_FALSE(parse_bit_pruning_mode("").has_value());
    EXPECT_FALSE(parse_bit_pruning_mode("all").has_value());
}

// Test bit_pruning_mode_to_string
TEST(BitPruningModeStringTest, ModeToString) {
    EXPECT_EQ(bit_pruning_mode_to_string(BitPruningMode::EXHAUSTIVE), "exhaustive");
    EXPECT_EQ(bit_pruning_mode_to_string(BitPruningMode::MSB_ONLY), "msb_only");
    EXPECT_EQ(bit_pruning_mode_to_string(BitPruningMode::SINGLE_BIT), "single_bit");
    EXPECT_EQ(bit_pruning_mode_to_string(BitPruningMode::CUSTOM), "custom");
}

// Test create_bit_pruning_config
TEST(CreateBitPruningConfigTest, ExhaustiveMode) {
    auto config = create_bit_pruning_config("exhaustive");
    ASSERT_TRUE(config.has_value());
    EXPECT_EQ(config->mode, BitPruningMode::EXHAUSTIVE);
    EXPECT_EQ(config->bit_mask, 0xFF);
}

TEST(CreateBitPruningConfigTest, MSBOnlyMode) {
    auto config = create_bit_pruning_config("msb_only");
    ASSERT_TRUE(config.has_value());
    EXPECT_EQ(config->mode, BitPruningMode::MSB_ONLY);
    EXPECT_EQ(config->bit_mask, 0xF0);
}

TEST(CreateBitPruningConfigTest, SingleBitModeWithPositions) {
    auto config = create_bit_pruning_config("single_bit", std::nullopt, std::make_pair<uint8_t, uint8_t>(1, 6));
    ASSERT_TRUE(config.has_value());
    EXPECT_EQ(config->mode, BitPruningMode::SINGLE_BIT);
    EXPECT_EQ(config->bit_mask, (1 << 1) | (1 << 6));
}

TEST(CreateBitPruningConfigTest, CustomModeWithMask) {
    auto config = create_bit_pruning_config("custom", static_cast<uint8_t>(0xAA));
    ASSERT_TRUE(config.has_value());
    EXPECT_EQ(config->mode, BitPruningMode::CUSTOM);
    EXPECT_EQ(config->bit_mask, 0xAA);
}

TEST(CreateBitPruningConfigTest, InvalidMode) {
    auto config = create_bit_pruning_config("invalid");
    EXPECT_FALSE(config.has_value());
}

// Test description output
TEST(BitPruningConfigTest, Description) {
    BitPruningConfig exhaustive(BitPruningMode::EXHAUSTIVE);
    EXPECT_NE(exhaustive.description().find("Exhaustive"), std::string::npos);
    EXPECT_NE(exhaustive.description().find("O(8^d)"), std::string::npos);
    
    BitPruningConfig msb(BitPruningMode::MSB_ONLY);
    EXPECT_NE(msb.description().find("MSB"), std::string::npos);
    EXPECT_NE(msb.description().find("O(4^d)"), std::string::npos);
    
    BitPruningConfig single(0, 7);
    EXPECT_NE(single.description().find("Single-bit"), std::string::npos);
    EXPECT_NE(single.description().find("O(2^d)"), std::string::npos);
}


// Integration tests with PathGenerator
#include "etb/path_generator.hpp"

TEST(BitPruningIntegrationTest, PathGeneratorWithExhaustiveMode) {
    BitPruningConfig pruning(BitPruningMode::EXHAUSTIVE);
    PathGeneratorConfig config(1, pruning);
    
    EXPECT_EQ(config.bit_mask, 0xFF);
    
    PathGenerator gen(config);
    int count = 0;
    while (gen.has_next()) {
        gen.next();
        count++;
    }
    // All 8 bits should be generated
    EXPECT_EQ(count, 8);
}

TEST(BitPruningIntegrationTest, PathGeneratorWithMSBOnly) {
    BitPruningConfig pruning(BitPruningMode::MSB_ONLY);
    PathGeneratorConfig config(1, pruning);
    
    EXPECT_EQ(config.bit_mask, 0xF0);
    
    PathGenerator gen(config);
    int count = 0;
    std::set<uint8_t> seen_bits;
    
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        for (const auto& coord : *path) {
            seen_bits.insert(coord.bit_position);
            EXPECT_GE(coord.bit_position, 4);
            EXPECT_LE(coord.bit_position, 7);
        }
        count++;
    }
    // Only 4 bits (4-7) should be generated
    EXPECT_EQ(count, 4);
    EXPECT_EQ(seen_bits.size(), 4);
}

TEST(BitPruningIntegrationTest, PathGeneratorWithSingleBit) {
    BitPruningConfig pruning(0, 7);  // Only bits 0 and 7
    PathGeneratorConfig config(2, pruning);
    
    PathGenerator gen(config);
    
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        for (const auto& coord : *path) {
            EXPECT_TRUE(coord.bit_position == 0 || coord.bit_position == 7)
                << "Unexpected bit position: " << static_cast<int>(coord.bit_position);
        }
    }
}

TEST(BitPruningIntegrationTest, PathGeneratorWithCustomMask) {
    // Custom mask: bits 1, 3, 5 (0x2A)
    BitPruningConfig pruning(static_cast<uint8_t>(0x2A));
    PathGeneratorConfig config(1, pruning);
    
    PathGenerator gen(config);
    std::set<uint8_t> seen_bits;
    
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        for (const auto& coord : *path) {
            seen_bits.insert(coord.bit_position);
        }
    }
    
    // Should only see bits 1, 3, 5
    EXPECT_EQ(seen_bits.size(), 3);
    EXPECT_TRUE(seen_bits.count(1) > 0);
    EXPECT_TRUE(seen_bits.count(3) > 0);
    EXPECT_TRUE(seen_bits.count(5) > 0);
}

TEST(BitPruningIntegrationTest, ApplyBitPruningMethod) {
    PathGeneratorConfig config(2);
    EXPECT_EQ(config.bit_mask, 0xFF);  // Default is all bits
    
    BitPruningConfig pruning(BitPruningMode::MSB_ONLY);
    config.apply_bit_pruning(pruning);
    
    EXPECT_EQ(config.bit_mask, 0xF0);  // Now MSB only
    
    PathGenerator gen(config);
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        for (const auto& coord : *path) {
            EXPECT_GE(coord.bit_position, 4);
        }
    }
}

TEST(BitPruningIntegrationTest, PathCountReductionMSB) {
    // With 2 bytes and all bits: 8 + 8 + 64 = 80 paths
    PathGenerator gen_full(2);
    int full_count = 0;
    while (gen_full.has_next()) {
        gen_full.next();
        full_count++;
    }
    EXPECT_EQ(full_count, 80);
    
    // With 2 bytes and MSB only (4 bits): 4 + 4 + 16 = 24 paths
    BitPruningConfig pruning(BitPruningMode::MSB_ONLY);
    PathGeneratorConfig config(2, pruning);
    PathGenerator gen_msb(config);
    int msb_count = 0;
    while (gen_msb.has_next()) {
        gen_msb.next();
        msb_count++;
    }
    EXPECT_EQ(msb_count, 24);
    
    // MSB mode should reduce path count significantly
    EXPECT_LT(msb_count, full_count);
}

TEST(BitPruningIntegrationTest, PathCountReductionSingleBit) {
    // With 2 bytes and single bit (2 positions): 2 + 2 + 4 = 8 paths
    // Wait, let me recalculate:
    // Single byte paths from byte 0: 2 paths (bit 0, bit 7)
    // Single byte paths from byte 1: 2 paths (bit 0, bit 7)
    // Two byte paths: 2 * 2 = 4 paths
    // Total: 2 + 2 + 4 = 8 paths? No wait...
    // Actually for 2 bytes with 2 bit positions each:
    // Paths of length 1: 2 (from byte 0) + 2 (from byte 1) = 4
    // Paths of length 2: 2 * 2 = 4
    // Total = 8? Let me verify with the test
    
    BitPruningConfig pruning(0, 7);
    PathGeneratorConfig config(2, pruning);
    PathGenerator gen(config);
    int count = 0;
    while (gen.has_next()) {
        gen.next();
        count++;
    }
    
    // With 2 bytes and 2 bit positions:
    // From byte 0: 2 single-coord paths
    // From byte 1: 2 single-coord paths  
    // From byte 0 to byte 1: 2 * 2 = 4 two-coord paths
    // Total: 2 + 2 + 4 = 8 paths
    // But wait, the generator also generates paths starting from byte 1...
    // Let me trace through: starting_byte_index = 0
    // Paths: (0,0), (0,7), (1,0), (1,7), (0,0)-(1,0), (0,0)-(1,7), (0,7)-(1,0), (0,7)-(1,7)
    // That's 8 paths
    EXPECT_EQ(count, 8);
}
