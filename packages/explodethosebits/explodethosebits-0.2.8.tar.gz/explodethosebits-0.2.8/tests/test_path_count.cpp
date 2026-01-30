#include <gtest/gtest.h>
#include "etb/path_count.hpp"
#include <cmath>

using namespace etb;

TEST(PathCountTest, CountBitsInMask) {
    EXPECT_EQ(count_bits_in_mask(0x00), 0);
    EXPECT_EQ(count_bits_in_mask(0x01), 1);
    EXPECT_EQ(count_bits_in_mask(0x03), 2);
    EXPECT_EQ(count_bits_in_mask(0x0F), 4);
    EXPECT_EQ(count_bits_in_mask(0xF0), 4);
    EXPECT_EQ(count_bits_in_mask(0xFF), 8);
    EXPECT_EQ(count_bits_in_mask(0xAA), 4);  // 10101010
}

TEST(PathCountTest, ExactPathCountZeroInput) {
    auto count = exact_path_count(0);
    ASSERT_TRUE(count.has_value());
    EXPECT_EQ(count.value(), 0);
}

TEST(PathCountTest, ExactPathCountSingleByte) {
    // For 1 byte with 8 bits: (1+8)^1 - 1 = 8 paths
    auto count = exact_path_count(1, 8);
    ASSERT_TRUE(count.has_value());
    EXPECT_EQ(count.value(), 8);
}

TEST(PathCountTest, ExactPathCountTwoBytes) {
    // For 2 bytes with 8 bits: (1+8)^2 - 1 = 81 - 1 = 80 paths
    auto count = exact_path_count(2, 8);
    ASSERT_TRUE(count.has_value());
    EXPECT_EQ(count.value(), 80);
}

TEST(PathCountTest, ExactPathCountThreeBytes) {
    // For 3 bytes with 8 bits: (1+8)^3 - 1 = 729 - 1 = 728 paths
    auto count = exact_path_count(3, 8);
    ASSERT_TRUE(count.has_value());
    EXPECT_EQ(count.value(), 728);
}

TEST(PathCountTest, ExactPathCountWithReducedBits) {
    // For 2 bytes with 4 bits: (1+4)^2 - 1 = 25 - 1 = 24 paths
    auto count = exact_path_count(2, 4);
    ASSERT_TRUE(count.has_value());
    EXPECT_EQ(count.value(), 24);
    
    // For 2 bytes with 1 bit: (1+1)^2 - 1 = 4 - 1 = 3 paths
    count = exact_path_count(2, 1);
    ASSERT_TRUE(count.has_value());
    EXPECT_EQ(count.value(), 3);
}

TEST(PathCountTest, ExactPathCountOverflow) {
    // Very large input should overflow
    auto count = exact_path_count(100, 8);
    EXPECT_FALSE(count.has_value());
}

TEST(PathCountTest, Log10PathCount) {
    // For 1 byte: log10(8) ≈ 0.903
    double log_count = log10_path_count(1, 8);
    EXPECT_NEAR(log_count, std::log10(9.0), 0.001);
    
    // For 2 bytes: log10(80) ≈ 1.903
    log_count = log10_path_count(2, 8);
    EXPECT_NEAR(log_count, 2 * std::log10(9.0), 0.001);
}

TEST(PathCountTest, EstimatePathCountExact) {
    auto result = estimate_path_count(2, 8, 0);
    
    EXPECT_TRUE(result.is_exact);
    EXPECT_EQ(result.estimated_count, 80);
    EXPECT_FALSE(result.exceeds_threshold);
}

TEST(PathCountTest, EstimatePathCountWithThreshold) {
    // Count is 80, threshold is 100 - should not exceed
    auto result = estimate_path_count(2, 8, 100);
    EXPECT_FALSE(result.exceeds_threshold);
    
    // Count is 80, threshold is 50 - should exceed
    result = estimate_path_count(2, 8, 50);
    EXPECT_TRUE(result.exceeds_threshold);
}

TEST(PathCountTest, EstimatePathCountOverflow) {
    auto result = estimate_path_count(100, 8, 0);
    
    EXPECT_FALSE(result.is_exact);
    EXPECT_GT(result.log_count, 50);  // Should be very large
}

TEST(PathCountTest, PathCountExceedsThreshold) {
    // 80 paths, threshold 100 - should not exceed
    EXPECT_FALSE(path_count_exceeds_threshold(2, 8, 100));
    
    // 80 paths, threshold 50 - should exceed
    EXPECT_TRUE(path_count_exceeds_threshold(2, 8, 50));
    
    // Large input should exceed any reasonable threshold
    EXPECT_TRUE(path_count_exceeds_threshold(50, 8, 1000000));
}

TEST(PathCountTest, PathCountExceedsThresholdZero) {
    // Zero threshold - any non-empty input exceeds
    EXPECT_TRUE(path_count_exceeds_threshold(1, 8, 0));
    EXPECT_FALSE(path_count_exceeds_threshold(0, 8, 0));
}
