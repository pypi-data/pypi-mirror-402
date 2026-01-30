#ifndef ETB_PATH_GENERATOR_HPP
#define ETB_PATH_GENERATOR_HPP

#include "path.hpp"
#include "bit_coordinate.hpp"
#include "bit_pruning.hpp"
#include <vector>
#include <cstdint>
#include <optional>
#include <stack>

namespace etb {

/**
 * Configuration for the path generator.
 */
struct PathGeneratorConfig {
    uint32_t input_length;          // Length of input byte array
    uint32_t max_path_length;       // Maximum path length (0 = unlimited up to input_length)
    uint32_t starting_byte_index;   // Starting byte index for path generation
    uint8_t bit_mask;               // Bit mask for allowed bit positions (0xFF = all bits)
    
    PathGeneratorConfig(uint32_t len)
        : input_length(len)
        , max_path_length(0)
        , starting_byte_index(0)
        , bit_mask(0xFF)
    {}
    
    /**
     * Apply a BitPruningConfig to this generator config.
     * @param pruning_config The bit pruning configuration to apply
     */
    void apply_bit_pruning(const BitPruningConfig& pruning_config) {
        bit_mask = pruning_config.get_mask();
    }
    
    /**
     * Create a PathGeneratorConfig with bit pruning applied.
     * @param len Input length
     * @param pruning_config The bit pruning configuration
     */
    PathGeneratorConfig(uint32_t len, const BitPruningConfig& pruning_config)
        : input_length(len)
        , max_path_length(0)
        , starting_byte_index(0)
        , bit_mask(pruning_config.get_mask())
    {}
};

/**
 * Lazy path generator using iterator pattern.
 * Generates all valid forward-only traversal paths on-demand.
 * 
 * The generator explores paths depth-first, yielding each complete path
 * before backtracking to explore alternatives.
 * 
 * Forward-only constraint: Each coordinate in a path must have a strictly
 * greater byte_index than the previous coordinate.
 */
class PathGenerator {
public:
    /**
     * Construct a path generator for the given input length.
     * @param input_length Length of the input byte array
     */
    explicit PathGenerator(uint32_t input_length);
    
    /**
     * Construct a path generator with custom configuration.
     * @param config Generator configuration
     */
    explicit PathGenerator(const PathGeneratorConfig& config);
    
    /**
     * Check if there are more paths to generate.
     * @return true if next() will return a valid path
     */
    bool has_next() const;
    
    /**
     * Generate the next path.
     * @return The next path, or std::nullopt if no more paths
     */
    std::optional<Path> next();
    
    /**
     * Reset the generator to start from the beginning.
     */
    void reset();
    
    /**
     * Get the current configuration.
     */
    const PathGeneratorConfig& config() const { return config_; }
    
    /**
     * Get the number of paths generated so far.
     */
    uint64_t paths_generated() const { return paths_generated_; }

private:
    PathGeneratorConfig config_;
    
    // State for iterative depth-first traversal
    struct StackFrame {
        uint32_t byte_index;
        uint8_t bit_position;
        bool explored;  // Have we yielded a path ending here?
    };
    
    std::stack<StackFrame> stack_;
    Path current_path_;
    uint64_t paths_generated_;
    bool exhausted_;
    bool first_call_;
    
    // Helper to check if a bit position is allowed by the mask
    bool is_bit_allowed(uint8_t bit_pos) const;
    
    // Get the next allowed bit position starting from pos
    int next_allowed_bit(uint8_t start_pos) const;
    
    // Initialize the stack for a fresh start
    void initialize_stack();
    
    // Advance to the next state
    void advance();
};

/**
 * Iterator adapter for PathGenerator to support range-based for loops.
 */
class PathIterator {
public:
    using iterator_category = std::input_iterator_tag;
    using value_type = Path;
    using difference_type = std::ptrdiff_t;
    using pointer = const Path*;
    using reference = const Path&;
    
    PathIterator() : generator_(nullptr), current_path_(std::nullopt) {}
    explicit PathIterator(PathGenerator* gen);
    
    reference operator*() const { return *current_path_; }
    pointer operator->() const { return &(*current_path_); }
    
    PathIterator& operator++();
    PathIterator operator++(int);
    
    bool operator==(const PathIterator& other) const;
    bool operator!=(const PathIterator& other) const { return !(*this == other); }

private:
    PathGenerator* generator_;
    std::optional<Path> current_path_;
};

/**
 * Range adapter for PathGenerator to support range-based for loops.
 */
class PathRange {
public:
    explicit PathRange(PathGenerator& gen) : generator_(gen) {}
    
    PathIterator begin() { return PathIterator(&generator_); }
    PathIterator end() { return PathIterator(); }

private:
    PathGenerator& generator_;
};

} // namespace etb

#endif // ETB_PATH_GENERATOR_HPP
