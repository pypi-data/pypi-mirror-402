#include <gtest/gtest.h>
#include "etb/bit_extraction.hpp"

using namespace etb;

// Test extract_bit function
TEST(BitExtractionTest, ExtractBitLSB) {
    std::vector<uint8_t> data = {0b10101010};  // 0xAA
    
    // bit_position 0 = LSB
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 0)), 0);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 1)), 1);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 2)), 0);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 3)), 1);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 4)), 0);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 5)), 1);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 6)), 0);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 7)), 1);  // MSB
}

TEST(BitExtractionTest, ExtractBitMultipleBytes) {
    std::vector<uint8_t> data = {0xFF, 0x00, 0b11110000};
    
    // All bits set in first byte
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 0)), 1);
    EXPECT_EQ(extract_bit(data, BitCoordinate(0, 7)), 1);
    
    // No bits set in second byte
    EXPECT_EQ(extract_bit(data, BitCoordinate(1, 0)), 0);
    EXPECT_EQ(extract_bit(data, BitCoordinate(1, 7)), 0);
    
    // Third byte: 0xF0 = 11110000
    EXPECT_EQ(extract_bit(data, BitCoordinate(2, 0)), 0);
    EXPECT_EQ(extract_bit(data, BitCoordinate(2, 3)), 0);
    EXPECT_EQ(extract_bit(data, BitCoordinate(2, 4)), 1);
    EXPECT_EQ(extract_bit(data, BitCoordinate(2, 7)), 1);
}

TEST(BitExtractionTest, ExtractBitOutOfBounds) {
    std::vector<uint8_t> data = {0xFF};
    
    EXPECT_THROW(extract_bit(data, BitCoordinate(1, 0)), std::out_of_range);
    EXPECT_THROW(extract_bit(data, BitCoordinate(100, 0)), std::out_of_range);
}

// Test bits_to_bytes function
TEST(BitExtractionTest, BitsToBytesSingleByte) {
    std::vector<uint8_t> bits = {1, 0, 1, 0, 1, 0, 1, 0};  // 0xAA
    auto bytes = bits_to_bytes(bits);
    
    ASSERT_EQ(bytes.size(), 1);
    EXPECT_EQ(bytes[0], 0xAA);
}

TEST(BitExtractionTest, BitsToBytesPadding) {
    // Only 4 bits - should be padded to 0xA0
    std::vector<uint8_t> bits = {1, 0, 1, 0};
    auto bytes = bits_to_bytes(bits);
    
    ASSERT_EQ(bytes.size(), 1);
    EXPECT_EQ(bytes[0], 0xA0);  // 10100000
}

TEST(BitExtractionTest, BitsToBytesTwoBytes) {
    // 16 bits = 2 bytes
    std::vector<uint8_t> bits = {1,1,1,1, 0,0,0,0, 1,0,1,0, 1,0,1,0};  // 0xF0, 0xAA
    auto bytes = bits_to_bytes(bits);
    
    ASSERT_EQ(bytes.size(), 2);
    EXPECT_EQ(bytes[0], 0xF0);
    EXPECT_EQ(bytes[1], 0xAA);
}

TEST(BitExtractionTest, BitsToByteEmpty) {
    std::vector<uint8_t> bits;
    auto bytes = bits_to_bytes(bits);
    EXPECT_TRUE(bytes.empty());
}

// Test bytes_to_bits function
TEST(BitExtractionTest, BytesToBitsSingleByte) {
    std::vector<uint8_t> bytes = {0xAA};  // 10101010
    auto bits = bytes_to_bits(bytes);
    
    ASSERT_EQ(bits.size(), 8);
    std::vector<uint8_t> expected = {1, 0, 1, 0, 1, 0, 1, 0};
    EXPECT_EQ(bits, expected);
}

TEST(BitExtractionTest, BytesToBitsMultipleBytes) {
    std::vector<uint8_t> bytes = {0xF0, 0x0F};
    auto bits = bytes_to_bits(bytes);
    
    ASSERT_EQ(bits.size(), 16);
    // 0xF0 = 11110000, 0x0F = 00001111
    std::vector<uint8_t> expected = {1,1,1,1, 0,0,0,0, 0,0,0,0, 1,1,1,1};
    EXPECT_EQ(bits, expected);
}

// Test extract_bits_from_path function
TEST(BitExtractionTest, ExtractBitsFromPath) {
    std::vector<uint8_t> data = {0xFF, 0x00, 0xAA};  // All 1s, all 0s, alternating
    
    Path path;
    path.add(BitCoordinate(0, 0));  // 1 from 0xFF
    path.add(BitCoordinate(1, 7));  // 0 from 0x00
    path.add(BitCoordinate(2, 1));  // 1 from 0xAA (bit 1)
    
    auto bits = extract_bits_from_path(data, path);
    
    ASSERT_EQ(bits.size(), 3);
    EXPECT_EQ(bits[0], 1);
    EXPECT_EQ(bits[1], 0);
    EXPECT_EQ(bits[2], 1);
}

// Test path_to_bytes function
TEST(BitExtractionTest, PathToBytes) {
    std::vector<uint8_t> data = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    
    // Create a path that extracts 8 bits (all 1s)
    Path path;
    for (uint32_t i = 0; i < 8; ++i) {
        path.add(BitCoordinate(i, 0));
    }
    
    auto bytes = path_to_bytes(data, path);
    
    ASSERT_EQ(bytes.size(), 1);
    EXPECT_EQ(bytes[0], 0xFF);  // All extracted bits are 1
}

TEST(BitExtractionTest, PathToBytesAlternating) {
    // Create data where we can extract alternating bits
    std::vector<uint8_t> data = {0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00};
    
    Path path;
    for (uint32_t i = 0; i < 8; ++i) {
        path.add(BitCoordinate(i, 0));
    }
    
    auto bytes = path_to_bytes(data, path);
    
    ASSERT_EQ(bytes.size(), 1);
    EXPECT_EQ(bytes[0], 0xAA);  // 10101010 - alternating from FF, 00, FF, 00...
}
