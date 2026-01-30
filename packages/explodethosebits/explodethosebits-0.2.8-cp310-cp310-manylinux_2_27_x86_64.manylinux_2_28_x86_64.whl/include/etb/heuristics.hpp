#ifndef ETB_HEURISTICS_HPP
#define ETB_HEURISTICS_HPP

#include <cstdint>
#include <cstddef>
#include <vector>
#include <array>

namespace etb {

/**
 * Result of heuristic analysis on a byte sequence.
 * All scores are normalized to specific ranges as documented.
 */
struct HeuristicResult {
    float entropy;              // Shannon entropy [0.0, 8.0]
    float printable_ratio;      // Ratio of printable ASCII [0.0, 1.0]
    float control_char_ratio;   // Ratio of control characters [0.0, 1.0]
    uint32_t max_null_run;      // Longest consecutive null byte run
    float utf8_validity;        // UTF-8 sequence validity score [0.0, 1.0]
    float composite_score;      // Weighted combination [0.0, 1.0]

    HeuristicResult()
        : entropy(0.0f)
        , printable_ratio(0.0f)
        , control_char_ratio(0.0f)
        , max_null_run(0)
        , utf8_validity(0.0f)
        , composite_score(0.0f) {}
};

/**
 * Configurable weights for composite heuristic scoring.
 */
struct HeuristicWeights {
    float entropy_weight;           // Weight for entropy score
    float printable_weight;         // Weight for printable ratio
    float control_char_weight;      // Weight for control char penalty
    float null_run_weight;          // Weight for null run penalty
    float utf8_weight;              // Weight for UTF-8 validity

    HeuristicWeights()
        : entropy_weight(0.25f)
        , printable_weight(0.25f)
        , control_char_weight(0.15f)
        , null_run_weight(0.15f)
        , utf8_weight(0.20f) {}
};

/**
 * Heuristics Engine - CPU Reference Implementation
 * 
 * Provides functions for analyzing byte sequences to determine viability
 * as valid data. Used for scoring partial reconstructions during path exploration.
 */
class HeuristicsEngine {
public:
    /**
     * Construct a heuristics engine with default weights.
     */
    HeuristicsEngine();

    /**
     * Construct a heuristics engine with custom weights.
     * @param weights Custom scoring weights
     */
    explicit HeuristicsEngine(const HeuristicWeights& weights);

    /**
     * Set the scoring weights.
     * @param weights New weights to use
     */
    void set_weights(const HeuristicWeights& weights);

    /**
     * Get the current scoring weights.
     */
    const HeuristicWeights& get_weights() const { return weights_; }

    /**
     * Perform full heuristic analysis on a byte sequence.
     * @param data Pointer to byte data
     * @param length Length of data
     * @return Complete heuristic analysis result
     */
    HeuristicResult analyze(const uint8_t* data, size_t length) const;

    /**
     * Perform full heuristic analysis on a vector of bytes.
     * @param data Byte vector to analyze
     * @return Complete heuristic analysis result
     */
    HeuristicResult analyze(const std::vector<uint8_t>& data) const;

    // Individual heuristic calculations

    /**
     * Calculate Shannon entropy of a byte sequence.
     * @param data Pointer to byte data
     * @param length Length of data
     * @return Entropy value in range [0.0, 8.0]
     */
    static float calculate_entropy(const uint8_t* data, size_t length);

    /**
     * Calculate Shannon entropy of a byte vector.
     * @param data Byte vector
     * @return Entropy value in range [0.0, 8.0]
     */
    static float calculate_entropy(const std::vector<uint8_t>& data);

    /**
     * Calculate the ratio of printable ASCII characters.
     * Printable ASCII: bytes in range [0x20, 0x7E]
     * @param data Pointer to byte data
     * @param length Length of data
     * @return Ratio in range [0.0, 1.0]
     */
    static float calculate_printable_ratio(const uint8_t* data, size_t length);

    /**
     * Calculate the ratio of control characters.
     * Control characters: bytes in range [0x00, 0x1F] excluding common whitespace (0x09, 0x0A, 0x0D)
     * @param data Pointer to byte data
     * @param length Length of data
     * @return Ratio in range [0.0, 1.0]
     */
    static float calculate_control_char_ratio(const uint8_t* data, size_t length);

    /**
     * Find the longest consecutive run of null bytes (0x00).
     * @param data Pointer to byte data
     * @param length Length of data
     * @return Length of longest null byte run
     */
    static uint32_t find_max_null_run(const uint8_t* data, size_t length);

    /**
     * Validate UTF-8 sequences and return a validity score.
     * @param data Pointer to byte data
     * @param length Length of data
     * @return Validity score in range [0.0, 1.0] where 1.0 = fully valid UTF-8
     */
    static float validate_utf8(const uint8_t* data, size_t length);

private:
    HeuristicWeights weights_;

    /**
     * Build a byte frequency histogram.
     * @param data Pointer to byte data
     * @param length Length of data
     * @return Array of 256 frequency counts
     */
    static std::array<uint32_t, 256> build_histogram(const uint8_t* data, size_t length);

    /**
     * Calculate composite score from individual heuristics.
     */
    float calculate_composite_score(const HeuristicResult& result, size_t data_length) const;
};

} // namespace etb

#endif // ETB_HEURISTICS_HPP
