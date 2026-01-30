#include <gtest/gtest.h>
#include "etb/bit_coordinate.hpp"

using namespace etb;

TEST(BitCoordinateTest, DefaultConstruction) {
    BitCoordinate coord;
    EXPECT_EQ(coord.byte_index, 0);
    EXPECT_EQ(coord.bit_position, 0);
}

TEST(BitCoordinateTest, ParameterizedConstruction) {
    BitCoordinate coord(5, 3);
    EXPECT_EQ(coord.byte_index, 5);
    EXPECT_EQ(coord.bit_position, 3);
}

TEST(BitCoordinateTest, Equality) {
    BitCoordinate a(1, 2);
    BitCoordinate b(1, 2);
    BitCoordinate c(1, 3);
    BitCoordinate d(2, 2);

    EXPECT_TRUE(a == b);
    EXPECT_FALSE(a == c);
    EXPECT_FALSE(a == d);
    EXPECT_TRUE(a != c);
}

TEST(BitCoordinateTest, LessThanComparison) {
    BitCoordinate a(1, 5);
    BitCoordinate b(2, 0);
    BitCoordinate c(1, 7);

    EXPECT_TRUE(a < b);
    EXPECT_FALSE(b < a);
    EXPECT_FALSE(a < c);  // Same byte_index, comparison is by byte_index only
}

TEST(BitCoordinateTest, IsValidWithinBounds) {
    BitCoordinate coord(5, 7);
    EXPECT_TRUE(coord.is_valid(10));
    EXPECT_TRUE(coord.is_valid(6));
    EXPECT_FALSE(coord.is_valid(5));  // byte_index must be < input_length
    EXPECT_FALSE(coord.is_valid(0));
}

TEST(BitCoordinateTest, IsValidBitPosition) {
    // bit_position must be <= 7
    for (uint8_t pos = 0; pos <= 7; ++pos) {
        BitCoordinate coord(0, pos);
        EXPECT_TRUE(coord.is_valid(1));
    }
}
