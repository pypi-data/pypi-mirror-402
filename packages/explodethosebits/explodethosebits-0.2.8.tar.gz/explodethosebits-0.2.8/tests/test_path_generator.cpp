#include <gtest/gtest.h>
#include "etb/path_generator.hpp"
#include <set>

using namespace etb;

TEST(PathGeneratorTest, EmptyInput) {
    PathGenerator gen(0);
    EXPECT_FALSE(gen.has_next());
    EXPECT_FALSE(gen.next().has_value());
}

TEST(PathGeneratorTest, SingleByteGeneratesAllBitPaths) {
    PathGenerator gen(1);
    
    std::set<uint8_t> seen_bits;
    int count = 0;
    
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        ASSERT_EQ(path->length(), 1);
        
        const auto& coord = path->at(0);
        EXPECT_EQ(coord.byte_index, 0);
        EXPECT_LE(coord.bit_position, 7);
        
        seen_bits.insert(coord.bit_position);
        count++;
    }
    
    // Should generate exactly 8 paths (one for each bit)
    EXPECT_EQ(count, 8);
    EXPECT_EQ(seen_bits.size(), 8);
}

TEST(PathGeneratorTest, TwoBytesForwardOnly) {
    PathGenerator gen(2);
    
    int count = 0;
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        EXPECT_TRUE(path->is_valid());  // Forward-only constraint
        
        // Verify forward-only: each byte_index > previous
        for (size_t i = 1; i < path->length(); ++i) {
            EXPECT_GT(path->at(i).byte_index, path->at(i-1).byte_index);
        }
        
        count++;
    }
    
    // For 2 bytes: 8 single-bit paths from byte 0 + 8 single-bit paths from byte 1
    // + 8*8 two-bit paths = 8 + 8 + 64 = 80
    EXPECT_EQ(count, 80);
}

TEST(PathGeneratorTest, StartingByteIndex) {
    PathGeneratorConfig config(3);
    config.starting_byte_index = 1;  // Start from byte 1
    
    PathGenerator gen(config);
    
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        
        // All paths should start at byte_index >= 1
        EXPECT_GE(path->at(0).byte_index, 1);
    }
}

TEST(PathGeneratorTest, MaxPathLength) {
    PathGeneratorConfig config(4);
    config.max_path_length = 2;  // Limit to 2 coordinates per path
    
    PathGenerator gen(config);
    
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        EXPECT_LE(path->length(), 2);
    }
}

TEST(PathGeneratorTest, BitMaskMSBOnly) {
    PathGeneratorConfig config(2);
    config.bit_mask = 0xF0;  // Only bits 4-7 (MSB half)
    
    PathGenerator gen(config);
    
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        
        for (const auto& coord : *path) {
            EXPECT_GE(coord.bit_position, 4);
            EXPECT_LE(coord.bit_position, 7);
        }
    }
}

TEST(PathGeneratorTest, BitMaskSingleBit) {
    PathGeneratorConfig config(2);
    config.bit_mask = 0x01;  // Only bit 0
    
    PathGenerator gen(config);
    
    int count = 0;
    while (gen.has_next()) {
        auto path = gen.next();
        ASSERT_TRUE(path.has_value());
        
        for (const auto& coord : *path) {
            EXPECT_EQ(coord.bit_position, 0);
        }
        count++;
    }
    
    // With only 1 bit per byte and 2 bytes: 1 + 1 + 1 = 3 paths
    // (byte0), (byte1), (byte0, byte1)
    EXPECT_EQ(count, 3);
}

TEST(PathGeneratorTest, Reset) {
    PathGenerator gen(1);
    
    // Exhaust the generator
    while (gen.has_next()) {
        gen.next();
    }
    EXPECT_FALSE(gen.has_next());
    
    // Reset and verify we can iterate again
    gen.reset();
    EXPECT_TRUE(gen.has_next());
    
    int count = 0;
    while (gen.has_next()) {
        gen.next();
        count++;
    }
    EXPECT_EQ(count, 8);
}

TEST(PathGeneratorTest, PathsGeneratedCounter) {
    PathGenerator gen(1);
    
    EXPECT_EQ(gen.paths_generated(), 0);
    
    gen.next();
    EXPECT_EQ(gen.paths_generated(), 1);
    
    while (gen.has_next()) {
        gen.next();
    }
    EXPECT_EQ(gen.paths_generated(), 8);
}

TEST(PathGeneratorTest, RangeBasedFor) {
    PathGenerator gen(1);
    PathRange range(gen);
    
    int count = 0;
    for (const auto& path : range) {
        EXPECT_TRUE(path.is_valid());
        count++;
    }
    EXPECT_EQ(count, 8);
}
