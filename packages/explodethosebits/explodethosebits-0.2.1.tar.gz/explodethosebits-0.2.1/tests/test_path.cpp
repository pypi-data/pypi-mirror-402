#include <gtest/gtest.h>
#include "etb/path.hpp"

using namespace etb;

TEST(PathTest, DefaultConstruction) {
    Path path;
    EXPECT_TRUE(path.empty());
    EXPECT_EQ(path.length(), 0);
    EXPECT_TRUE(path.is_valid());
}

TEST(PathTest, AddCoordinatesForwardOnly) {
    Path path;
    
    EXPECT_TRUE(path.add(BitCoordinate(0, 3)));
    EXPECT_TRUE(path.add(BitCoordinate(1, 5)));
    EXPECT_TRUE(path.add(BitCoordinate(5, 0)));
    
    EXPECT_EQ(path.length(), 3);
    EXPECT_TRUE(path.is_valid());
}

TEST(PathTest, RejectBackwardCoordinate) {
    Path path;
    
    EXPECT_TRUE(path.add(BitCoordinate(5, 3)));
    EXPECT_FALSE(path.add(BitCoordinate(3, 0)));  // byte_index 3 < 5
    
    EXPECT_EQ(path.length(), 1);  // Second add should have failed
    EXPECT_TRUE(path.is_valid());
}

TEST(PathTest, RejectSameByteIndex) {
    Path path;
    
    EXPECT_TRUE(path.add(BitCoordinate(5, 3)));
    EXPECT_FALSE(path.add(BitCoordinate(5, 7)));  // Same byte_index
    
    EXPECT_EQ(path.length(), 1);
}

TEST(PathTest, AccessCoordinates) {
    Path path;
    path.add(BitCoordinate(0, 1));
    path.add(BitCoordinate(2, 3));
    path.add(BitCoordinate(4, 5));
    
    EXPECT_EQ(path.at(0).byte_index, 0);
    EXPECT_EQ(path.at(1).byte_index, 2);
    EXPECT_EQ(path[2].byte_index, 4);
    
    EXPECT_EQ(path.back().byte_index, 4);
    EXPECT_EQ(path.back().bit_position, 5);
}

TEST(PathTest, Clear) {
    Path path;
    path.add(BitCoordinate(0, 0));
    path.add(BitCoordinate(1, 0));
    
    EXPECT_EQ(path.length(), 2);
    
    path.clear();
    EXPECT_TRUE(path.empty());
    EXPECT_EQ(path.length(), 0);
}

TEST(PathTest, Iterator) {
    Path path;
    path.add(BitCoordinate(0, 0));
    path.add(BitCoordinate(1, 1));
    path.add(BitCoordinate(2, 2));
    
    size_t count = 0;
    for (const auto& coord : path) {
        EXPECT_EQ(coord.byte_index, count);
        EXPECT_EQ(coord.bit_position, count);
        ++count;
    }
    EXPECT_EQ(count, 3);
}

TEST(PathTest, BackThrowsOnEmpty) {
    Path path;
    EXPECT_THROW(path.back(), std::out_of_range);
}

TEST(PathTest, AtThrowsOnInvalidIndex) {
    Path path;
    path.add(BitCoordinate(0, 0));
    
    EXPECT_NO_THROW(path.at(0));
    EXPECT_THROW(path.at(1), std::out_of_range);
}
