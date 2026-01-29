#include "etb/reporting.hpp"
#include <sstream>
#include <iomanip>
#include <cmath>
#include <algorithm>

namespace etb {

// ============================================================================
// SuccessResultBuilder Implementation
// ============================================================================

SuccessResultBuilder& SuccessResultBuilder::set_data(const std::vector<uint8_t>& data) {
    result_.extracted_bytes = data;
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_data(std::vector<uint8_t>&& data) {
    result_.extracted_bytes = std::move(data);
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_format(const std::string& format_name,
                                                       const std::string& category) {
    result_.detected_format = format_name;
    result_.format_category = category;
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_confidence(float confidence) {
    result_.confidence = std::clamp(confidence, 0.0f, 1.0f);
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_path(const Path& path) {
    result_.reconstruction_path = path;
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_path(Path&& path) {
    result_.reconstruction_path = std::move(path);
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_heuristics(const HeuristicResult& heuristics) {
    result_.heuristics = heuristics;
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_signature_match(const SignatureMatch& match) {
    result_.signature_match = match;
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::set_structural_validation(const StructuralValidation& structure) {
    structure_ = structure;
    has_structure_ = true;
    return *this;
}

SuccessResultBuilder& SuccessResultBuilder::build_validation_report() {
    compute_validation();
    return *this;
}

void SuccessResultBuilder::compute_validation() {
    ValidationReport& report = result_.validation;
    std::ostringstream notes;

    // Signature validation
    report.signature_valid = result_.signature_match.matched && 
                            result_.signature_match.confidence >= 0.5f;
    if (report.signature_valid) {
        notes << "Signature: " << result_.detected_format << " detected";
        if (result_.signature_match.header_matched && result_.signature_match.footer_matched) {
            notes << " (header+footer)";
        } else if (result_.signature_match.header_matched) {
            notes << " (header only)";
        }
        notes << ". ";
    } else {
        notes << "Signature: No valid signature detected. ";
    }

    // Structure validation
    if (has_structure_) {
        report.structure_valid = structure_.validity_score >= 0.5f &&
                                structure_.has_valid_length &&
                                structure_.has_valid_checksum;
        if (report.structure_valid) {
            notes << "Structure: Valid. ";
        } else {
            notes << "Structure: Issues detected";
            if (!structure_.has_valid_length) notes << " (length)";
            if (!structure_.has_valid_checksum) notes << " (checksum)";
            if (!structure_.has_valid_pointers) notes << " (pointers)";
            notes << ". ";
        }
    } else {
        report.structure_valid = true; // Assume valid if not checked
        notes << "Structure: Not validated. ";
    }

    // Heuristics validation
    bool entropy_ok = result_.heuristics.entropy >= 0.1f && result_.heuristics.entropy <= 7.9f;
    bool printable_ok = result_.heuristics.printable_ratio >= 0.0f; // Always valid
    bool null_run_ok = result_.heuristics.max_null_run <= 64;
    
    report.heuristics_valid = entropy_ok && null_run_ok;
    if (report.heuristics_valid) {
        notes << "Heuristics: Within expected ranges. ";
    } else {
        notes << "Heuristics: ";
        if (!entropy_ok) notes << "Entropy out of range (" << result_.heuristics.entropy << "). ";
        if (!null_run_ok) notes << "Excessive null runs (" << result_.heuristics.max_null_run << "). ";
    }

    // Calculate overall validity
    float validity_sum = 0.0f;
    int validity_count = 0;

    if (report.signature_valid) {
        validity_sum += result_.signature_match.confidence;
        validity_count++;
    }
    if (has_structure_) {
        validity_sum += structure_.validity_score;
        validity_count++;
    }
    if (report.heuristics_valid) {
        validity_sum += result_.heuristics.composite_score;
        validity_count++;
    }

    report.overall_validity = validity_count > 0 ? validity_sum / validity_count : 0.0f;
    report.validation_notes = notes.str();
}

SuccessResult SuccessResultBuilder::build() const {
    return result_;
}

SuccessResult SuccessResultBuilder::from_candidate(const Candidate& candidate) {
    SuccessResultBuilder builder;
    builder.set_data(candidate.data)
           .set_format(candidate.format_name, candidate.signature_match.category)
           .set_confidence(candidate.confidence)
           .set_path(candidate.path)
           .set_heuristics(candidate.heuristics)
           .set_signature_match(candidate.signature_match)
           .set_structural_validation(candidate.structure)
           .build_validation_report();
    return builder.build();
}


// ============================================================================
// FailureResultBuilder Implementation
// ============================================================================

FailureResultBuilder& FailureResultBuilder::set_paths_explored(uint64_t count) {
    result_.paths_explored = count;
    return *this;
}

FailureResultBuilder& FailureResultBuilder::set_effective_depth(size_t depth) {
    result_.effective_depth_reached = depth;
    return *this;
}

FailureResultBuilder& FailureResultBuilder::add_partial_match(const PartialMatch& partial) {
    result_.best_partials.push_back(partial);
    return *this;
}

FailureResultBuilder& FailureResultBuilder::add_partial_match(PartialMatch&& partial) {
    result_.best_partials.push_back(std::move(partial));
    return *this;
}

FailureResultBuilder& FailureResultBuilder::add_partial_from_candidate(const Candidate& candidate,
                                                                       const std::string& failure_reason) {
    PartialMatch partial;
    partial.partial_data = candidate.data;
    partial.possible_format = candidate.format_name;
    partial.partial_score = candidate.composite_score;
    partial.depth_reached = candidate.path.length();
    partial.failure_reason = failure_reason;
    result_.best_partials.push_back(std::move(partial));
    return *this;
}

FailureResultBuilder& FailureResultBuilder::add_suggestion(const ParameterSuggestion& suggestion) {
    result_.suggestions.push_back(suggestion);
    return *this;
}

FailureResultBuilder& FailureResultBuilder::add_suggestion(const std::string& param,
                                                          const std::string& current,
                                                          const std::string& suggested,
                                                          const std::string& rationale) {
    result_.suggestions.emplace_back(param, current, suggested, rationale);
    return *this;
}

FailureResultBuilder& FailureResultBuilder::generate_suggestions(const ExtractionMetrics& metrics) {
    // Suggest based on prune rates
    if (metrics.level1_prune_rate > 0.95f) {
        add_suggestion("early_stopping.level1_threshold", 
                      std::to_string(0.4f),
                      std::to_string(0.2f),
                      "Very high Level 1 prune rate - consider relaxing threshold");
    }

    // Suggest based on cache hit rate
    if (metrics.cache_hit_rate < 0.1f && metrics.paths_evaluated > 10000) {
        add_suggestion("memoization.max_size_bytes",
                      "current",
                      "increase by 2x",
                      "Low cache hit rate - consider increasing cache size");
    }

    // Suggest based on effective branching factor
    if (metrics.effective_branching_factor > 6.0f) {
        add_suggestion("bit_pruning.mode",
                      "exhaustive",
                      "msb_only",
                      "High branching factor - consider MSB-only mode to reduce search space");
    }

    // Suggest based on paths evaluated vs possible
    if (metrics.paths_evaluated < metrics.total_paths_possible * 0.001) {
        add_suggestion("performance.max_paths",
                      "current",
                      "increase by 10x",
                      "Only a small fraction of paths explored - consider increasing limit");
    }

    return *this;
}

FailureResultBuilder& FailureResultBuilder::set_summary(const std::string& summary) {
    result_.failure_summary = summary;
    return *this;
}

FailureResultBuilder& FailureResultBuilder::generate_summary() {
    std::ostringstream summary;
    
    summary << "Extraction failed after exploring " << format_count(result_.paths_explored) << " paths. ";
    
    if (result_.effective_depth_reached > 0) {
        summary << "Maximum depth reached: " << result_.effective_depth_reached << " bytes. ";
    }

    if (!result_.best_partials.empty()) {
        summary << "Found " << result_.best_partials.size() << " partial match(es). ";
        const auto& best = result_.best_partials[0];
        if (!best.possible_format.empty()) {
            summary << "Best partial: " << best.possible_format 
                   << " (score: " << std::fixed << std::setprecision(2) 
                   << best.partial_score << "). ";
        }
    } else {
        summary << "No promising partial matches found. ";
    }

    if (!result_.suggestions.empty()) {
        summary << "Consider adjusting: ";
        for (size_t i = 0; i < result_.suggestions.size() && i < 3; ++i) {
            if (i > 0) summary << ", ";
            summary << result_.suggestions[i].parameter_name;
        }
        summary << ".";
    }

    result_.failure_summary = summary.str();
    return *this;
}

FailureResult FailureResultBuilder::build() const {
    return result_;
}

// ============================================================================
// MetricsReporter Implementation
// ============================================================================

MetricsReporter& MetricsReporter::set_total_paths_possible(uint64_t count) {
    metrics_.total_paths_possible = count;
    return *this;
}

MetricsReporter& MetricsReporter::set_paths_evaluated(uint64_t count) {
    metrics_.paths_evaluated = count;
    return *this;
}

MetricsReporter& MetricsReporter::set_paths_pruned_level1(uint64_t count) {
    metrics_.paths_pruned_level1 = count;
    return *this;
}

MetricsReporter& MetricsReporter::set_paths_pruned_level2(uint64_t count) {
    metrics_.paths_pruned_level2 = count;
    return *this;
}

MetricsReporter& MetricsReporter::set_paths_pruned_level3(uint64_t count) {
    metrics_.paths_pruned_level3 = count;
    return *this;
}

MetricsReporter& MetricsReporter::set_paths_pruned_prefix(uint64_t count) {
    metrics_.paths_pruned_prefix = count;
    return *this;
}

MetricsReporter& MetricsReporter::set_effective_branching_factor(float factor) {
    metrics_.effective_branching_factor = factor;
    return *this;
}

MetricsReporter& MetricsReporter::set_effective_depth(float depth) {
    metrics_.effective_depth = depth;
    return *this;
}

MetricsReporter& MetricsReporter::set_cache_hit_rate(float rate) {
    metrics_.cache_hit_rate = std::clamp(rate, 0.0f, 1.0f);
    return *this;
}

MetricsReporter& MetricsReporter::add_format_detection(const std::string& format, uint32_t count) {
    // Find existing entry or add new one
    for (auto& entry : metrics_.format_distribution) {
        if (entry.first == format) {
            entry.second += count;
            return *this;
        }
    }
    metrics_.format_distribution.emplace_back(format, count);
    return *this;
}

MetricsReporter& MetricsReporter::set_wall_clock_time(double seconds) {
    metrics_.wall_clock_seconds = seconds;
    return *this;
}

MetricsReporter& MetricsReporter::set_gpu_utilization(float utilization) {
    metrics_.gpu_utilization = std::clamp(utilization, 0.0f, 1.0f);
    return *this;
}

MetricsReporter& MetricsReporter::calculate_derived_metrics() {
    uint64_t total_pruned = metrics_.paths_pruned_level1 + 
                           metrics_.paths_pruned_level2 + 
                           metrics_.paths_pruned_level3;
    
    uint64_t total_considered = metrics_.paths_evaluated + total_pruned;
    
    if (total_considered > 0) {
        metrics_.level1_prune_rate = static_cast<float>(metrics_.paths_pruned_level1) / total_considered;
        metrics_.level2_prune_rate = static_cast<float>(metrics_.paths_pruned_level2) / total_considered;
        metrics_.level3_prune_rate = static_cast<float>(metrics_.paths_pruned_level3) / total_considered;
    }

    if (metrics_.paths_evaluated + metrics_.paths_pruned_prefix > 0) {
        metrics_.prefix_prune_rate = static_cast<float>(metrics_.paths_pruned_prefix) / 
                                    (metrics_.paths_evaluated + metrics_.paths_pruned_prefix);
    }

    // Calculate average time per path
    if (metrics_.paths_evaluated > 0 && metrics_.wall_clock_seconds > 0) {
        metrics_.average_time_per_path_us = (metrics_.wall_clock_seconds * 1e6) / metrics_.paths_evaluated;
    }

    return *this;
}

MetricsReporter& MetricsReporter::generate_complexity_reduction(uint32_t input_length) {
    std::ostringstream oss;
    
    float k = metrics_.effective_branching_factor;
    float d = metrics_.effective_depth;
    
    oss << "Reduced from O(8^" << input_length << ") to O(" 
        << std::fixed << std::setprecision(1) << k << "^" 
        << std::setprecision(0) << d << ") where k=" 
        << std::setprecision(2) << k << ", d=" 
        << std::setprecision(0) << d;
    
    // Calculate actual reduction factor if possible
    if (metrics_.total_paths_possible > 0 && metrics_.paths_evaluated > 0) {
        double reduction = static_cast<double>(metrics_.total_paths_possible) / metrics_.paths_evaluated;
        if (reduction > 1.0) {
            oss << " (reduction factor: " << std::scientific << std::setprecision(2) << reduction << ")";
        }
    }
    
    metrics_.complexity_reduction = oss.str();
    return *this;
}

ExtractionMetrics MetricsReporter::build() const {
    return metrics_;
}

std::string MetricsReporter::to_string(const std::string& verbosity) const {
    std::ostringstream oss;
    
    if (verbosity == "minimal") {
        oss << "Paths: " << format_count(metrics_.paths_evaluated) << "/" 
            << format_count(metrics_.total_paths_possible)
            << " | Time: " << format_duration(metrics_.wall_clock_seconds)
            << " | Cache: " << std::fixed << std::setprecision(1) 
            << (metrics_.cache_hit_rate * 100) << "%";
        return oss.str();
    }
    
    oss << "=== Extraction Metrics ===" << std::endl;
    
    // Path statistics
    oss << std::endl << "Path Statistics:" << std::endl;
    oss << "  Total possible:    " << format_count(metrics_.total_paths_possible) << std::endl;
    oss << "  Paths evaluated:   " << format_count(metrics_.paths_evaluated) << std::endl;
    oss << "  Pruned (Level 1):  " << format_count(metrics_.paths_pruned_level1) 
        << " (" << std::fixed << std::setprecision(1) << (metrics_.level1_prune_rate * 100) << "%)" << std::endl;
    oss << "  Pruned (Level 2):  " << format_count(metrics_.paths_pruned_level2)
        << " (" << (metrics_.level2_prune_rate * 100) << "%)" << std::endl;
    oss << "  Pruned (Level 3):  " << format_count(metrics_.paths_pruned_level3)
        << " (" << (metrics_.level3_prune_rate * 100) << "%)" << std::endl;
    oss << "  Pruned (Prefix):   " << format_count(metrics_.paths_pruned_prefix)
        << " (" << (metrics_.prefix_prune_rate * 100) << "%)" << std::endl;
    
    // Efficiency metrics
    oss << std::endl << "Efficiency:" << std::endl;
    oss << "  Branching factor:  " << std::setprecision(2) << metrics_.effective_branching_factor << std::endl;
    oss << "  Effective depth:   " << metrics_.effective_depth << std::endl;
    oss << "  Cache hit rate:    " << (metrics_.cache_hit_rate * 100) << "%" << std::endl;
    
    if (verbosity == "full") {
        // Timing
        oss << std::endl << "Timing:" << std::endl;
        oss << "  Wall clock:        " << format_duration(metrics_.wall_clock_seconds) << std::endl;
        oss << "  Avg per path:      " << std::setprecision(2) << metrics_.average_time_per_path_us << " µs" << std::endl;
        oss << "  GPU utilization:   " << (metrics_.gpu_utilization * 100) << "%" << std::endl;
        
        // Format distribution
        if (!metrics_.format_distribution.empty()) {
            oss << std::endl << "Format Distribution:" << std::endl;
            for (const auto& [format, count] : metrics_.format_distribution) {
                oss << "  " << format << ": " << count << std::endl;
            }
        }
        
        // Complexity reduction
        if (!metrics_.complexity_reduction.empty()) {
            oss << std::endl << "Complexity: " << metrics_.complexity_reduction << std::endl;
        }
    }
    
    return oss.str();
}


// ============================================================================
// ExtractionResultBuilder Implementation
// ============================================================================

ExtractionResultBuilder& ExtractionResultBuilder::set_success(bool success) {
    result_.success = success;
    return *this;
}

ExtractionResultBuilder& ExtractionResultBuilder::add_candidate(const SuccessResult& result) {
    result_.candidates.push_back(result);
    return *this;
}

ExtractionResultBuilder& ExtractionResultBuilder::add_candidate(SuccessResult&& result) {
    result_.candidates.push_back(std::move(result));
    return *this;
}

ExtractionResultBuilder& ExtractionResultBuilder::add_candidates(const std::vector<Candidate>& candidates) {
    for (const auto& candidate : candidates) {
        result_.candidates.push_back(SuccessResultBuilder::from_candidate(candidate));
    }
    return *this;
}

ExtractionResultBuilder& ExtractionResultBuilder::set_failure(const FailureResult& failure) {
    result_.failure = failure;
    return *this;
}

ExtractionResultBuilder& ExtractionResultBuilder::set_failure(FailureResult&& failure) {
    result_.failure = std::move(failure);
    return *this;
}

ExtractionResultBuilder& ExtractionResultBuilder::set_metrics(const ExtractionMetrics& metrics) {
    result_.metrics = metrics;
    return *this;
}

ExtractionResultBuilder& ExtractionResultBuilder::set_metrics(ExtractionMetrics&& metrics) {
    result_.metrics = std::move(metrics);
    return *this;
}

ExtractionResult ExtractionResultBuilder::build() const {
    return result_;
}

// ============================================================================
// Utility Functions
// ============================================================================

std::string format_path(const Path& path, size_t max_coords) {
    std::ostringstream oss;
    oss << "[";
    
    size_t count = path.length();
    size_t show_count = (max_coords == 0 || count <= max_coords) ? count : max_coords;
    
    for (size_t i = 0; i < show_count; ++i) {
        if (i > 0) oss << ", ";
        const auto& coord = path[i];
        oss << "(" << coord.byte_index << "," << static_cast<int>(coord.bit_position) << ")";
    }
    
    if (show_count < count) {
        oss << ", ... (" << (count - show_count) << " more)";
    }
    
    oss << "]";
    return oss.str();
}

std::string format_bytes_hex(const std::vector<uint8_t>& data, size_t max_bytes) {
    std::ostringstream oss;
    
    size_t count = data.size();
    size_t show_count = (max_bytes == 0 || count <= max_bytes) ? count : max_bytes;
    
    for (size_t i = 0; i < show_count; ++i) {
        if (i > 0) oss << " ";
        oss << std::hex << std::uppercase << std::setfill('0') << std::setw(2) 
            << static_cast<int>(data[i]);
    }
    
    if (show_count < count) {
        oss << " ... (" << std::dec << (count - show_count) << " more bytes)";
    }
    
    return oss.str();
}

std::string format_confidence(float confidence) {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(1) << (confidence * 100) << "%";
    return oss.str();
}

std::string format_duration(double seconds) {
    std::ostringstream oss;
    
    if (seconds < 0.001) {
        oss << std::fixed << std::setprecision(1) << (seconds * 1e6) << " µs";
    } else if (seconds < 1.0) {
        oss << std::fixed << std::setprecision(2) << (seconds * 1000) << " ms";
    } else if (seconds < 60.0) {
        oss << std::fixed << std::setprecision(2) << seconds << " s";
    } else if (seconds < 3600.0) {
        int minutes = static_cast<int>(seconds / 60);
        double secs = seconds - minutes * 60;
        oss << minutes << "m " << std::fixed << std::setprecision(1) << secs << "s";
    } else {
        int hours = static_cast<int>(seconds / 3600);
        int minutes = static_cast<int>((seconds - hours * 3600) / 60);
        oss << hours << "h " << minutes << "m";
    }
    
    return oss.str();
}

std::string format_count(uint64_t count) {
    std::ostringstream oss;
    
    if (count < 1000) {
        oss << count;
    } else if (count < 1000000) {
        oss << std::fixed << std::setprecision(1) << (count / 1000.0) << "K";
    } else if (count < 1000000000) {
        oss << std::fixed << std::setprecision(2) << (count / 1000000.0) << "M";
    } else {
        oss << std::fixed << std::setprecision(2) << (count / 1000000000.0) << "B";
    }
    
    return oss.str();
}

} // namespace etb
