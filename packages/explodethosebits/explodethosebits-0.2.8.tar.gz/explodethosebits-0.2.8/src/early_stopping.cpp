#include "etb/early_stopping.hpp"
#include <algorithm>
#include <cstring>

namespace etb {

// ============================================================================
// AdaptiveThresholdManager Implementation
// ============================================================================

AdaptiveThresholdManager::AdaptiveThresholdManager()
    : config_()
    , global_best_score_(0.0f)
    , update_count_(0) {}

AdaptiveThresholdManager::AdaptiveThresholdManager(const EarlyStoppingConfig& config)
    : config_(config)
    , global_best_score_(0.0f)
    , update_count_(0) {}

void AdaptiveThresholdManager::update_best_score(float score) {
    if (score > global_best_score_) {
        global_best_score_ = score;
    }
    update_count_++;
}

float AdaptiveThresholdManager::get_adaptive_threshold() const {
    if (!config_.adaptive_thresholds) {
        return config_.adaptive_default;
    }

    // Adaptive threshold logic from design:
    // if (global_best_score > 0.8): threshold = 0.6 (tighten)
    // elif (global_best_score < 0.3): threshold = 0.2 (relax)
    // else: threshold = 0.4 (default)
    if (global_best_score_ > 0.8f) {
        return config_.adaptive_tighten;
    } else if (global_best_score_ < 0.3f) {
        return config_.adaptive_relax;
    }
    return config_.adaptive_default;
}

void AdaptiveThresholdManager::reset() {
    global_best_score_ = 0.0f;
    update_count_ = 0;
}

// ============================================================================
// EarlyStoppingController Implementation
// ============================================================================

EarlyStoppingController::EarlyStoppingController()
    : config_()
    , dictionary_(nullptr)
    , heuristics_engine_(nullptr)
    , default_heuristics_()
    , threshold_manager_(config_)
    , stats_() {}

EarlyStoppingController::EarlyStoppingController(const EarlyStoppingConfig& config)
    : config_(config)
    , dictionary_(nullptr)
    , heuristics_engine_(nullptr)
    , default_heuristics_()
    , threshold_manager_(config)
    , stats_() {}

EarlyStoppingController::EarlyStoppingController(
    const EarlyStoppingConfig& config,
    const SignatureDictionary* dictionary)
    : config_(config)
    , dictionary_(dictionary)
    , heuristics_engine_(nullptr)
    , default_heuristics_()
    , threshold_manager_(config)
    , stats_() {}

void EarlyStoppingController::set_signature_dictionary(const SignatureDictionary* dictionary) {
    dictionary_ = dictionary;
}

void EarlyStoppingController::set_heuristics_engine(const HeuristicsEngine* engine) {
    heuristics_engine_ = engine;
}

bool EarlyStoppingController::is_all_null(const uint8_t* data, size_t length) {
    if (length == 0) {
        return false;
    }
    for (size_t i = 0; i < length; ++i) {
        if (data[i] != 0x00) {
            return false;
        }
    }
    return true;
}

bool EarlyStoppingController::is_repeated_byte_pattern(const uint8_t* data, size_t length) {
    if (length <= 1) {
        return length == 1;  // Single byte is trivially repeated
    }
    uint8_t first_byte = data[0];
    for (size_t i = 1; i < length; ++i) {
        if (data[i] != first_byte) {
            return false;
        }
    }
    return true;
}

bool EarlyStoppingController::has_signature_prefix_match(const uint8_t* data, size_t length) const {
    if (!dictionary_ || dictionary_->empty() || length == 0) {
        return false;
    }

    // Check if any signature's prefix matches the data
    for (const auto& format : dictionary_->get_formats()) {
        for (const auto& sig : format.signatures) {
            // Check if we have enough bytes to match the signature prefix
            size_t check_len = std::min(length, sig.magic_bytes.size());
            if (check_len == 0) continue;

            // Check if the prefix matches (considering offset)
            if (sig.offset > 0 && length <= sig.offset) {
                continue;  // Not enough data to check offset-based signature
            }

            size_t start_pos = sig.offset;
            if (start_pos + check_len > length) {
                check_len = length - start_pos;
            }

            bool prefix_matches = true;
            for (size_t i = 0; i < check_len; ++i) {
                uint8_t mask = (i < sig.mask.size()) ? sig.mask[i] : 0xFF;
                if ((data[start_pos + i] & mask) != (sig.magic_bytes[i] & mask)) {
                    prefix_matches = false;
                    break;
                }
            }

            if (prefix_matches) {
                return true;
            }
        }
    }
    return false;
}

float EarlyStoppingController::get_threshold_for_level(StopLevel level) const {
    float adaptive = threshold_manager_.get_adaptive_threshold();
    
    // Use the more restrictive of adaptive and level-specific thresholds
    switch (level) {
        case StopLevel::LEVEL_1:
            return std::max(config_.level1_threshold, adaptive * 0.5f);
        case StopLevel::LEVEL_2:
            return std::max(config_.level2_threshold, adaptive * 0.75f);
        case StopLevel::LEVEL_3:
            return std::max(config_.level3_threshold, adaptive);
        default:
            return adaptive;
    }
}

StopDecision EarlyStoppingController::check_level1(
    const uint8_t* data, size_t length, const HeuristicResult& heuristics) const {
    
    StopDecision decision;
    decision.level = StopLevel::LEVEL_1;
    decision.score = heuristics.composite_score;

    // Level 1: signature prefix + basic heuristics
    // Stop if: no signature prefix match AND poor heuristics
    bool has_sig_match = has_signature_prefix_match(data, length);
    float threshold = get_threshold_for_level(StopLevel::LEVEL_1);

    if (!has_sig_match && heuristics.composite_score < threshold) {
        decision.should_stop = true;
        decision.reason = "Level 1: No signature prefix match and poor heuristics";
        return decision;
    }

    decision.should_stop = false;
    return decision;
}

StopDecision EarlyStoppingController::check_level2(
    const uint8_t* data, size_t length, const HeuristicResult& heuristics) const {
    
    StopDecision decision;
    decision.level = StopLevel::LEVEL_2;
    decision.score = heuristics.composite_score;

    // Level 2: entropy bounds + checksum validation
    // Stop if: entropy outside expected ranges
    if (heuristics.entropy < config_.min_entropy) {
        decision.should_stop = true;
        decision.reason = "Level 2: Entropy too low (repeated pattern)";
        return decision;
    }

    if (heuristics.entropy > config_.max_entropy) {
        // High entropy might still be valid (encrypted/compressed)
        // Only stop if heuristics are also poor
        float threshold = get_threshold_for_level(StopLevel::LEVEL_2);
        if (heuristics.composite_score < threshold) {
            decision.should_stop = true;
            decision.reason = "Level 2: High entropy with poor heuristics";
            return decision;
        }
    }

    // Check overall heuristic threshold
    float threshold = get_threshold_for_level(StopLevel::LEVEL_2);
    if (heuristics.composite_score < threshold) {
        decision.should_stop = true;
        decision.reason = "Level 2: Heuristic score below threshold";
        return decision;
    }

    decision.should_stop = false;
    return decision;
}

StopDecision EarlyStoppingController::check_level3(
    const uint8_t* data, size_t length, const HeuristicResult& heuristics) const {
    
    StopDecision decision;
    decision.level = StopLevel::LEVEL_3;
    decision.score = heuristics.composite_score;

    // Level 3: structural coherence
    // This is the absolute cutoff before infeasible territory
    float threshold = get_threshold_for_level(StopLevel::LEVEL_3);

    if (heuristics.composite_score < threshold) {
        decision.should_stop = true;
        decision.reason = "Level 3: No internal consistency";
        return decision;
    }

    // Check for excessive null runs (structural issue)
    if (heuristics.max_null_run > length / 2) {
        decision.should_stop = true;
        decision.reason = "Level 3: Excessive null byte runs";
        return decision;
    }

    decision.should_stop = false;
    return decision;
}

StopDecision EarlyStoppingController::should_stop(const uint8_t* data, size_t length) const {
    stats_.total_checks++;
    StopDecision decision;

    if (length == 0) {
        decision.should_stop = false;
        stats_.continued++;
        return decision;
    }

    // Immediate check: all null or single repeated byte
    // This should abort immediately at first detection (Requirement 4.2)
    if (is_all_null(data, length)) {
        decision.should_stop = true;
        decision.level = StopLevel::LEVEL_1;
        decision.score = 0.0f;
        decision.reason = "All null bytes detected";
        stats_.stopped_repeated++;
        return decision;
    }

    if (is_repeated_byte_pattern(data, length)) {
        decision.should_stop = true;
        decision.level = StopLevel::LEVEL_1;
        decision.score = 0.0f;
        decision.reason = "Single repeated byte pattern detected";
        stats_.stopped_repeated++;
        return decision;
    }

    // Get heuristics for the data
    const HeuristicsEngine* engine = heuristics_engine_ ? heuristics_engine_ : &default_heuristics_;
    HeuristicResult heuristics = engine->analyze(data, length);

    // Level 1 check (2-4 bytes)
    if (length >= config_.level1_bytes) {
        decision = check_level1(data, length, heuristics);
        if (decision.should_stop) {
            stats_.stopped_level1++;
            return decision;
        }
    }

    // Level 2 check (8 bytes)
    if (length >= config_.level2_bytes) {
        decision = check_level2(data, length, heuristics);
        if (decision.should_stop) {
            stats_.stopped_level2++;
            return decision;
        }
    }

    // Level 3 check (16 bytes)
    if (length >= config_.level3_bytes) {
        decision = check_level3(data, length, heuristics);
        if (decision.should_stop) {
            stats_.stopped_level3++;
            return decision;
        }
    }

    // Continue exploring this path
    decision.should_stop = false;
    decision.score = heuristics.composite_score;
    stats_.continued++;
    return decision;
}

StopDecision EarlyStoppingController::should_stop(const std::vector<uint8_t>& data) const {
    return should_stop(data.data(), data.size());
}

void EarlyStoppingController::update_best_score(float score) {
    threshold_manager_.update_best_score(score);
}

float EarlyStoppingController::get_adaptive_threshold() const {
    return threshold_manager_.get_adaptive_threshold();
}

void EarlyStoppingController::reset_statistics() {
    stats_ = Statistics();
}

} // namespace etb
