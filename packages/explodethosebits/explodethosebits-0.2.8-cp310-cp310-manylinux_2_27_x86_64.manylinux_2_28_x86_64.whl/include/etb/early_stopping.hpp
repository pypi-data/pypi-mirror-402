#ifndef ETB_EARLY_STOPPING_HPP
#define ETB_EARLY_STOPPING_HPP

#include <cstdint>
#include <cstddef>
#include <vector>
#include "etb/heuristics.hpp"
#include "etb/signature.hpp"

namespace etb {

/**
 * Stop levels for multi-level early stopping.
 * Each level represents a depth at which stopping decisions are made.
 */
enum class StopLevel : uint8_t {
    LEVEL_1 = 4,    // 2-4 bytes: signature prefix + basic heuristics
    LEVEL_2 = 8,    // 8 bytes: entropy bounds + checksum validation
    LEVEL_3 = 16    // 16 bytes: structural coherence
};

/**
 * Result of an early stopping check.
 */
struct StopDecision {
    bool should_stop;           // Whether to stop exploring this path
    StopLevel level;            // Level at which decision was made
    float score;                // Heuristic score at decision point
    const char* reason;         // Human-readable reason for stopping

    StopDecision() 
        : should_stop(false), level(StopLevel::LEVEL_1), 
          score(0.0f), reason(nullptr) {}
};

/**
 * Configuration for early stopping thresholds.
 */
struct EarlyStoppingConfig {
    // Byte thresholds for each level
    uint32_t level1_bytes;      // Default: 4
    uint32_t level2_bytes;      // Default: 8
    uint32_t level3_bytes;      // Default: 16

    // Entropy bounds
    float min_entropy;          // Below this = repeated pattern garbage (default: 0.1)
    float max_entropy;          // Above this = random/encrypted (default: 7.9)

    // Heuristic thresholds
    float level1_threshold;     // Minimum score to continue at level 1 (default: 0.2)
    float level2_threshold;     // Minimum score to continue at level 2 (default: 0.3)
    float level3_threshold;     // Minimum score to continue at level 3 (default: 0.4)

    // Adaptive threshold settings
    bool adaptive_thresholds;   // Enable adaptive threshold adjustment
    float adaptive_tighten;     // Threshold when global best > 0.8 (default: 0.6)
    float adaptive_relax;       // Threshold when global best < 0.3 (default: 0.2)
    float adaptive_default;     // Default threshold (default: 0.4)

    EarlyStoppingConfig()
        : level1_bytes(4)
        , level2_bytes(8)
        , level3_bytes(16)
        , min_entropy(0.1f)
        , max_entropy(7.9f)
        , level1_threshold(0.2f)
        , level2_threshold(0.3f)
        , level3_threshold(0.4f)
        , adaptive_thresholds(true)
        , adaptive_tighten(0.6f)
        , adaptive_relax(0.2f)
        , adaptive_default(0.4f) {}
};


/**
 * Adaptive threshold manager for early stopping.
 * Tracks global best score and adjusts thresholds based on running statistics.
 */
class AdaptiveThresholdManager {
public:
    AdaptiveThresholdManager();
    explicit AdaptiveThresholdManager(const EarlyStoppingConfig& config);

    /**
     * Update the global best score seen so far.
     * @param score New score to consider
     */
    void update_best_score(float score);

    /**
     * Get the current global best score.
     */
    float get_best_score() const { return global_best_score_; }

    /**
     * Get the current adaptive threshold based on global best score.
     */
    float get_adaptive_threshold() const;

    /**
     * Reset the manager to initial state.
     */
    void reset();

    /**
     * Get statistics about threshold adjustments.
     */
    uint64_t get_update_count() const { return update_count_; }

private:
    EarlyStoppingConfig config_;
    float global_best_score_;
    uint64_t update_count_;
};

/**
 * Early Stopping Controller - CPU Reference Implementation
 * 
 * Implements multi-level early stopping to reduce search space from O(8^n) to O(8^d)
 * where d << n. Uses signature matching, heuristics, and adaptive thresholds.
 */
class EarlyStoppingController {
public:
    /**
     * Construct with default configuration.
     */
    EarlyStoppingController();

    /**
     * Construct with custom configuration.
     * @param config Early stopping configuration
     */
    explicit EarlyStoppingController(const EarlyStoppingConfig& config);

    /**
     * Construct with configuration and signature dictionary.
     * @param config Early stopping configuration
     * @param dictionary Signature dictionary for prefix matching
     */
    EarlyStoppingController(const EarlyStoppingConfig& config,
                           const SignatureDictionary* dictionary);

    /**
     * Set the signature dictionary for prefix matching.
     * @param dictionary Pointer to signature dictionary (can be nullptr)
     */
    void set_signature_dictionary(const SignatureDictionary* dictionary);

    /**
     * Set the heuristics engine for scoring.
     * @param engine Pointer to heuristics engine (can be nullptr for default)
     */
    void set_heuristics_engine(const HeuristicsEngine* engine);

    /**
     * Check if a path should be stopped at the current depth.
     * @param data Reconstructed byte sequence
     * @param length Length of the byte sequence
     * @return StopDecision indicating whether to stop and why
     */
    StopDecision should_stop(const uint8_t* data, size_t length) const;

    /**
     * Check if a path should be stopped (vector overload).
     * @param data Reconstructed byte sequence
     * @return StopDecision indicating whether to stop and why
     */
    StopDecision should_stop(const std::vector<uint8_t>& data) const;

    /**
     * Check if data consists entirely of repeated bytes.
     * @param data Byte sequence to check
     * @param length Length of the sequence
     * @return true if all bytes are the same value
     */
    static bool is_repeated_byte_pattern(const uint8_t* data, size_t length);

    /**
     * Check if data consists entirely of null bytes.
     * @param data Byte sequence to check
     * @param length Length of the sequence
     * @return true if all bytes are 0x00
     */
    static bool is_all_null(const uint8_t* data, size_t length);

    /**
     * Update the adaptive threshold manager with a new score.
     * @param score Score to update with
     */
    void update_best_score(float score);

    /**
     * Get the current adaptive threshold.
     */
    float get_adaptive_threshold() const;

    /**
     * Get the configuration.
     */
    const EarlyStoppingConfig& get_config() const { return config_; }

    /**
     * Get statistics about stopping decisions.
     */
    struct Statistics {
        uint64_t total_checks;
        uint64_t stopped_level1;
        uint64_t stopped_level2;
        uint64_t stopped_level3;
        uint64_t stopped_repeated;
        uint64_t continued;

        Statistics() : total_checks(0), stopped_level1(0), stopped_level2(0),
                      stopped_level3(0), stopped_repeated(0), continued(0) {}
    };

    const Statistics& get_statistics() const { return stats_; }
    void reset_statistics();

private:
    EarlyStoppingConfig config_;
    const SignatureDictionary* dictionary_;
    const HeuristicsEngine* heuristics_engine_;
    HeuristicsEngine default_heuristics_;
    AdaptiveThresholdManager threshold_manager_;
    mutable Statistics stats_;

    // Level-specific checks
    StopDecision check_level1(const uint8_t* data, size_t length, 
                              const HeuristicResult& heuristics) const;
    StopDecision check_level2(const uint8_t* data, size_t length,
                              const HeuristicResult& heuristics) const;
    StopDecision check_level3(const uint8_t* data, size_t length,
                              const HeuristicResult& heuristics) const;

    // Check for signature prefix match
    bool has_signature_prefix_match(const uint8_t* data, size_t length) const;

    // Get the effective threshold for a given level
    float get_threshold_for_level(StopLevel level) const;
};

} // namespace etb

#endif // ETB_EARLY_STOPPING_HPP
