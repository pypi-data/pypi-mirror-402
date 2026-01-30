#ifndef ETB_PATH_HPP
#define ETB_PATH_HPP

#include "bit_coordinate.hpp"
#include <vector>
#include <cstdint>
#include <stdexcept>

namespace etb {

/**
 * Represents a forward-only traversal path through bit coordinates.
 * Enforces the constraint that each subsequent coordinate must have
 * a strictly greater byte index than the previous one.
 */
class Path {
public:
    Path() = default;
    explicit Path(size_t capacity) { coordinates_.reserve(capacity); }

    /**
     * Add a coordinate to the path.
     * @param coord The coordinate to add
     * @return true if added successfully, false if forward-only constraint violated
     */
    bool add(const BitCoordinate& coord);

    /**
     * Validate that the path maintains forward-only traversal.
     * @return true if all coordinates satisfy byte_index[i] < byte_index[i+1]
     */
    bool is_valid() const;

    /**
     * Get the number of coordinates in the path.
     */
    size_t length() const { return coordinates_.size(); }

    /**
     * Check if the path is empty.
     */
    bool empty() const { return coordinates_.empty(); }

    /**
     * Clear all coordinates from the path.
     */
    void clear() { coordinates_.clear(); }

    /**
     * Reserve capacity for coordinates.
     */
    void reserve(size_t capacity) { coordinates_.reserve(capacity); }

    /**
     * Get coordinate at index.
     * @throws std::out_of_range if index is invalid
     */
    const BitCoordinate& at(size_t index) const { return coordinates_.at(index); }

    /**
     * Get coordinate at index (no bounds checking).
     */
    const BitCoordinate& operator[](size_t index) const { return coordinates_[index]; }

    /**
     * Get the last coordinate in the path.
     * @throws std::out_of_range if path is empty
     */
    const BitCoordinate& back() const;

    /**
     * Get read-only access to the underlying coordinates.
     */
    const std::vector<BitCoordinate>& coordinates() const { return coordinates_; }

    // Iterator support
    auto begin() const { return coordinates_.begin(); }
    auto end() const { return coordinates_.end(); }

private:
    std::vector<BitCoordinate> coordinates_;
};

} // namespace etb

#endif // ETB_PATH_HPP
