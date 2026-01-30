#include "etb/path.hpp"

namespace etb {

bool Path::add(const BitCoordinate& coord) {
    // Check forward-only constraint
    if (!coordinates_.empty()) {
        if (coord.byte_index <= coordinates_.back().byte_index) {
            return false;  // Violates forward-only constraint
        }
    }
    coordinates_.push_back(coord);
    return true;
}

bool Path::is_valid() const {
    if (coordinates_.size() <= 1) {
        return true;  // Empty or single-element paths are always valid
    }

    for (size_t i = 1; i < coordinates_.size(); ++i) {
        if (coordinates_[i].byte_index <= coordinates_[i - 1].byte_index) {
            return false;  // Forward-only constraint violated
        }
    }
    return true;
}

const BitCoordinate& Path::back() const {
    if (coordinates_.empty()) {
        throw std::out_of_range("Path is empty");
    }
    return coordinates_.back();
}

} // namespace etb
