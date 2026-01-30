#ifndef ETB_REPORTING_HPP
#define ETB_REPORTING_HPP

#include "scoring.hpp"
#include "heuristics.hpp"
#include "signature.hpp"
#include "path.hpp"
#include "bit_pruning.hpp"
#include <cstdint>
#include <string>
#include <vector>
#include <chrono>
#include <optional>

namespace etb {

/**
 * Validation report for a successful extraction.
 * Contains detailed validation information about the extracted data.
 */
struct ValidationReport {
    bool signature_valid;           // Signature validation passed
    bool structure_valid;           // Structural validation passed
    bool heuristics_valid;          // Heuristics within expected ranges
    float overall_validity;         // Overall validity score [0.0, 1.0]
    std::string validation_notes;   // Human-readable validation notes

    ValidationReport()
        : signature_valid(false)
        , structure_valid(false)
        , heuristics_valid(false)
        , overall_validity(0.0f) {}
};

/**
 * Success result containing extracted data and metadata.
 * Requirements: 12.1
 */
struct SuccessResult {
    std::vector<uint8_t> extracted_bytes;   // The extracted byte sequence
    std::string detected_format;            // Detected format name (e.g., "PNG", "JPEG")
    std::string format_category;            // Format category (e.g., "image", "archive")
    float confidence;                       // Confidence score [0.0, 1.0]
    Path reconstruction_path;               // The path taken to reconstruct the data
    ValidationReport validation;            // Detailed validation report
    HeuristicResult heuristics;             // Heuristic analysis results
    SignatureMatch signature_match;         // Signature match details

    SuccessResult() : confidence(0.0f) {}
};

/**
 * Partial match information for failed extractions.
 */
struct PartialMatch {
    std::vector<uint8_t> partial_data;      // Partial reconstructed data
    std::string possible_format;            // Possible format (if any signature prefix matched)
    float partial_score;                    // Score achieved before failure
    size_t depth_reached;                   // How deep the path went before stopping
    std::string failure_reason;             // Why this path was abandoned

    PartialMatch() : partial_score(0.0f), depth_reached(0) {}
};

/**
 * Suggestion for parameter adjustment when extraction fails.
 */
struct ParameterSuggestion {
    std::string parameter_name;             // Name of the parameter to adjust
    std::string current_value;              // Current value as string
    std::string suggested_value;            // Suggested new value
    std::string rationale;                  // Why this adjustment might help

    ParameterSuggestion() = default;
    ParameterSuggestion(const std::string& name, const std::string& current,
                       const std::string& suggested, const std::string& reason)
        : parameter_name(name), current_value(current)
        , suggested_value(suggested), rationale(reason) {}
};

/**
 * Failure result containing diagnostic information.
 * Requirements: 12.2
 */
struct FailureResult {
    uint64_t paths_explored;                // Total paths explored before giving up
    size_t effective_depth_reached;         // Maximum depth reached
    std::vector<PartialMatch> best_partials;// Best partial matches found
    std::vector<ParameterSuggestion> suggestions; // Suggestions for parameter adjustment
    std::string failure_summary;            // Human-readable failure summary

    FailureResult() : paths_explored(0), effective_depth_reached(0) {}
};

/**
 * Extraction metrics for reporting.
 * Requirements: 12.3, 12.4
 */
struct ExtractionMetrics {
    // Path statistics
    uint64_t total_paths_possible;          // Theoretical total paths
    uint64_t paths_evaluated;               // Actual paths evaluated
    uint64_t paths_pruned_level1;           // Paths pruned at Level 1 (2-4 bytes)
    uint64_t paths_pruned_level2;           // Paths pruned at Level 2 (8 bytes)
    uint64_t paths_pruned_level3;           // Paths pruned at Level 3 (16 bytes)
    uint64_t paths_pruned_prefix;           // Paths pruned by prefix trie

    // Efficiency metrics
    float effective_branching_factor;       // Actual branching factor achieved
    float effective_depth;                  // Average depth of evaluated paths
    float cache_hit_rate;                   // Memoization cache hit rate [0.0, 1.0]

    // Prune rates
    float level1_prune_rate;                // Percentage pruned at Level 1
    float level2_prune_rate;                // Percentage pruned at Level 2
    float level3_prune_rate;                // Percentage pruned at Level 3
    float prefix_prune_rate;                // Percentage pruned by prefix

    // Format detection
    std::vector<std::pair<std::string, uint32_t>> format_distribution; // Format -> count

    // Timing
    double wall_clock_seconds;              // Total wall clock time
    double average_time_per_path_us;        // Average microseconds per path
    float gpu_utilization;                  // GPU utilization percentage [0.0, 1.0]

    // Complexity reduction
    std::string complexity_reduction;       // Human-readable complexity reduction

    ExtractionMetrics()
        : total_paths_possible(0)
        , paths_evaluated(0)
        , paths_pruned_level1(0)
        , paths_pruned_level2(0)
        , paths_pruned_level3(0)
        , paths_pruned_prefix(0)
        , effective_branching_factor(8.0f)
        , effective_depth(0.0f)
        , cache_hit_rate(0.0f)
        , level1_prune_rate(0.0f)
        , level2_prune_rate(0.0f)
        , level3_prune_rate(0.0f)
        , prefix_prune_rate(0.0f)
        , wall_clock_seconds(0.0)
        , average_time_per_path_us(0.0)
        , gpu_utilization(0.0f) {}
};

/**
 * Complete extraction result combining success/failure with metrics.
 */
struct ExtractionResult {
    bool success;                           // Whether extraction succeeded
    std::vector<SuccessResult> candidates;  // Successful candidates (if any)
    std::optional<FailureResult> failure;   // Failure details (if failed)
    ExtractionMetrics metrics;              // Extraction metrics

    ExtractionResult() : success(false) {}
};


/**
 * Success Result Builder
 * Formats extracted bytes, format, confidence, path, and validation report.
 * Requirements: 12.1
 */
class SuccessResultBuilder {
public:
    SuccessResultBuilder() = default;

    /**
     * Set the extracted byte data.
     */
    SuccessResultBuilder& set_data(const std::vector<uint8_t>& data);
    SuccessResultBuilder& set_data(std::vector<uint8_t>&& data);

    /**
     * Set the detected format information.
     */
    SuccessResultBuilder& set_format(const std::string& format_name, 
                                     const std::string& category = "");

    /**
     * Set the confidence score.
     */
    SuccessResultBuilder& set_confidence(float confidence);

    /**
     * Set the reconstruction path.
     */
    SuccessResultBuilder& set_path(const Path& path);
    SuccessResultBuilder& set_path(Path&& path);

    /**
     * Set the heuristic analysis results.
     */
    SuccessResultBuilder& set_heuristics(const HeuristicResult& heuristics);

    /**
     * Set the signature match results.
     */
    SuccessResultBuilder& set_signature_match(const SignatureMatch& match);

    /**
     * Set structural validation results.
     */
    SuccessResultBuilder& set_structural_validation(const StructuralValidation& structure);

    /**
     * Build the validation report based on set values.
     */
    SuccessResultBuilder& build_validation_report();

    /**
     * Build and return the success result.
     */
    SuccessResult build() const;

    /**
     * Build a success result from a Candidate object.
     */
    static SuccessResult from_candidate(const Candidate& candidate);

private:
    SuccessResult result_;
    StructuralValidation structure_;
    bool has_structure_ = false;

    void compute_validation();
};

/**
 * Failure Result Builder
 * Includes paths explored, best partials, and suggestions.
 * Requirements: 12.2
 */
class FailureResultBuilder {
public:
    FailureResultBuilder() = default;

    /**
     * Set the number of paths explored.
     */
    FailureResultBuilder& set_paths_explored(uint64_t count);

    /**
     * Set the effective depth reached.
     */
    FailureResultBuilder& set_effective_depth(size_t depth);

    /**
     * Add a partial match.
     */
    FailureResultBuilder& add_partial_match(const PartialMatch& partial);
    FailureResultBuilder& add_partial_match(PartialMatch&& partial);

    /**
     * Add a partial match from a Candidate.
     */
    FailureResultBuilder& add_partial_from_candidate(const Candidate& candidate,
                                                     const std::string& failure_reason);

    /**
     * Add a parameter suggestion.
     */
    FailureResultBuilder& add_suggestion(const ParameterSuggestion& suggestion);
    FailureResultBuilder& add_suggestion(const std::string& param, const std::string& current,
                                        const std::string& suggested, const std::string& rationale);

    /**
     * Generate suggestions based on metrics.
     */
    FailureResultBuilder& generate_suggestions(const ExtractionMetrics& metrics);

    /**
     * Set the failure summary.
     */
    FailureResultBuilder& set_summary(const std::string& summary);

    /**
     * Auto-generate failure summary based on set values.
     */
    FailureResultBuilder& generate_summary();

    /**
     * Build and return the failure result.
     */
    FailureResult build() const;

private:
    FailureResult result_;
};

/**
 * Metrics Reporter
 * Calculates and reports all extraction metrics.
 * Requirements: 12.3, 12.4
 */
class MetricsReporter {
public:
    MetricsReporter() = default;

    /**
     * Set path statistics.
     */
    MetricsReporter& set_total_paths_possible(uint64_t count);
    MetricsReporter& set_paths_evaluated(uint64_t count);
    MetricsReporter& set_paths_pruned_level1(uint64_t count);
    MetricsReporter& set_paths_pruned_level2(uint64_t count);
    MetricsReporter& set_paths_pruned_level3(uint64_t count);
    MetricsReporter& set_paths_pruned_prefix(uint64_t count);

    /**
     * Set efficiency metrics.
     */
    MetricsReporter& set_effective_branching_factor(float factor);
    MetricsReporter& set_effective_depth(float depth);
    MetricsReporter& set_cache_hit_rate(float rate);

    /**
     * Add format detection result.
     */
    MetricsReporter& add_format_detection(const std::string& format, uint32_t count = 1);

    /**
     * Set timing information.
     */
    MetricsReporter& set_wall_clock_time(double seconds);
    MetricsReporter& set_gpu_utilization(float utilization);

    /**
     * Calculate derived metrics (prune rates, average time, complexity reduction).
     */
    MetricsReporter& calculate_derived_metrics();

    /**
     * Generate complexity reduction string.
     * Format: "Reduced from O(8^n) to O(k^d) where k=X.X, d=Y"
     */
    MetricsReporter& generate_complexity_reduction(uint32_t input_length);

    /**
     * Build and return the metrics.
     */
    ExtractionMetrics build() const;

    /**
     * Get a human-readable report string.
     * @param verbosity "minimal", "standard", or "full"
     */
    std::string to_string(const std::string& verbosity = "full") const;

private:
    ExtractionMetrics metrics_;
};

/**
 * Complete Extraction Result Builder
 * Combines success/failure results with metrics.
 */
class ExtractionResultBuilder {
public:
    ExtractionResultBuilder() = default;

    /**
     * Mark as successful extraction.
     */
    ExtractionResultBuilder& set_success(bool success);

    /**
     * Add a successful candidate.
     */
    ExtractionResultBuilder& add_candidate(const SuccessResult& result);
    ExtractionResultBuilder& add_candidate(SuccessResult&& result);

    /**
     * Add candidates from a vector of Candidate objects.
     */
    ExtractionResultBuilder& add_candidates(const std::vector<Candidate>& candidates);

    /**
     * Set failure information.
     */
    ExtractionResultBuilder& set_failure(const FailureResult& failure);
    ExtractionResultBuilder& set_failure(FailureResult&& failure);

    /**
     * Set extraction metrics.
     */
    ExtractionResultBuilder& set_metrics(const ExtractionMetrics& metrics);
    ExtractionResultBuilder& set_metrics(ExtractionMetrics&& metrics);

    /**
     * Build and return the complete result.
     */
    ExtractionResult build() const;

private:
    ExtractionResult result_;
};

// Utility functions

/**
 * Format a path as a human-readable string.
 * @param path The path to format
 * @param max_coords Maximum coordinates to show (0 = all)
 * @return Formatted string like "[(0,3), (1,5), (2,1), ...]"
 */
std::string format_path(const Path& path, size_t max_coords = 10);

/**
 * Format bytes as a hex string.
 * @param data The bytes to format
 * @param max_bytes Maximum bytes to show (0 = all)
 * @return Formatted hex string like "89 50 4E 47 ..."
 */
std::string format_bytes_hex(const std::vector<uint8_t>& data, size_t max_bytes = 32);

/**
 * Format a confidence score as a percentage string.
 */
std::string format_confidence(float confidence);

/**
 * Format a duration in human-readable form.
 */
std::string format_duration(double seconds);

/**
 * Format a large number with appropriate suffix (K, M, B).
 */
std::string format_count(uint64_t count);

} // namespace etb

#endif // ETB_REPORTING_HPP
