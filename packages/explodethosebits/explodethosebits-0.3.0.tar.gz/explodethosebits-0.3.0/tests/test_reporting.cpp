#include <gtest/gtest.h>
#include "etb/reporting.hpp"
#include "etb/scoring.hpp"
#include "etb/heuristics.hpp"
#include "etb/signature.hpp"
#include "etb/path.hpp"
#include <vector>
#include <cstdint>

using namespace etb;

// ============================================================================
// SuccessResultBuilder Tests
// ============================================================================

TEST(SuccessResultBuilderTest, BasicBuild) {
    std::vector<uint8_t> data = {0x89, 0x50, 0x4E, 0x47};
    
    SuccessResultBuilder builder;
    auto result = builder
        .set_data(data)
        .set_format("PNG", "image")
        .set_confidence(0.95f)
        .build();
    
    EXPECT_EQ(result.extracted_bytes, data);
    EXPECT_EQ(result.detected_format, "PNG");
    EXPECT_EQ(result.format_category, "image");
    EXPECT_FLOAT_EQ(result.confidence, 0.95f);
}

TEST(SuccessResultBuilderTest, ConfidenceClamp) {
    SuccessResultBuilder builder;
    
    // Test clamping above 1.0
    auto result1 = builder.set_confidence(1.5f).build();
    EXPECT_FLOAT_EQ(result1.confidence, 1.0f);
    
    // Test clamping below 0.0
    auto result2 = SuccessResultBuilder().set_confidence(-0.5f).build();
    EXPECT_FLOAT_EQ(result2.confidence, 0.0f);
}

TEST(SuccessResultBuilderTest, WithPath) {
    Path path;
    path.add(BitCoordinate(0, 3));
    path.add(BitCoordinate(1, 5));
    path.add(BitCoordinate(2, 1));
    
    auto result = SuccessResultBuilder()
        .set_path(path)
        .build();
    
    EXPECT_EQ(result.reconstruction_path.length(), 3);
    EXPECT_EQ(result.reconstruction_path[0].byte_index, 0);
    EXPECT_EQ(result.reconstruction_path[0].bit_position, 3);
}

TEST(SuccessResultBuilderTest, WithHeuristics) {
    HeuristicResult heuristics;
    heuristics.entropy = 5.5f;
    heuristics.printable_ratio = 0.8f;
    heuristics.composite_score = 0.75f;
    
    auto result = SuccessResultBuilder()
        .set_heuristics(heuristics)
        .build();
    
    EXPECT_FLOAT_EQ(result.heuristics.entropy, 5.5f);
    EXPECT_FLOAT_EQ(result.heuristics.printable_ratio, 0.8f);
    EXPECT_FLOAT_EQ(result.heuristics.composite_score, 0.75f);
}

TEST(SuccessResultBuilderTest, ValidationReport) {
    SignatureMatch sig_match;
    sig_match.matched = true;
    sig_match.format_name = "PNG";
    sig_match.confidence = 0.9f;
    sig_match.header_matched = true;
    sig_match.footer_matched = true;
    
    HeuristicResult heuristics;
    heuristics.entropy = 5.0f;
    heuristics.max_null_run = 4;
    heuristics.composite_score = 0.8f;
    
    StructuralValidation structure;
    structure.validity_score = 0.9f;
    structure.has_valid_length = true;
    structure.has_valid_checksum = true;
    
    auto result = SuccessResultBuilder()
        .set_format("PNG", "image")
        .set_signature_match(sig_match)
        .set_heuristics(heuristics)
        .set_structural_validation(structure)
        .build_validation_report()
        .build();
    
    EXPECT_TRUE(result.validation.signature_valid);
    EXPECT_TRUE(result.validation.structure_valid);
    EXPECT_TRUE(result.validation.heuristics_valid);
    EXPECT_GT(result.validation.overall_validity, 0.0f);
    EXPECT_FALSE(result.validation.validation_notes.empty());
}

TEST(SuccessResultBuilderTest, FromCandidate) {
    Candidate candidate;
    candidate.data = {0x89, 0x50, 0x4E, 0x47};
    candidate.format_name = "PNG";
    candidate.confidence = 0.95f;
    candidate.signature_match.matched = true;
    candidate.signature_match.category = "image";
    candidate.heuristics.entropy = 5.0f;
    
    auto result = SuccessResultBuilder::from_candidate(candidate);
    
    EXPECT_EQ(result.extracted_bytes, candidate.data);
    EXPECT_EQ(result.detected_format, "PNG");
    EXPECT_EQ(result.format_category, "image");
    EXPECT_FLOAT_EQ(result.confidence, 0.95f);
}

// ============================================================================
// FailureResultBuilder Tests
// ============================================================================

TEST(FailureResultBuilderTest, BasicBuild) {
    auto result = FailureResultBuilder()
        .set_paths_explored(1000000)
        .set_effective_depth(12)
        .build();
    
    EXPECT_EQ(result.paths_explored, 1000000);
    EXPECT_EQ(result.effective_depth_reached, 12);
}

TEST(FailureResultBuilderTest, WithPartialMatches) {
    PartialMatch partial;
    partial.partial_data = {0x89, 0x50};
    partial.possible_format = "PNG";
    partial.partial_score = 0.3f;
    partial.depth_reached = 4;
    partial.failure_reason = "Entropy out of range";
    
    auto result = FailureResultBuilder()
        .add_partial_match(partial)
        .build();
    
    ASSERT_EQ(result.best_partials.size(), 1);
    EXPECT_EQ(result.best_partials[0].possible_format, "PNG");
    EXPECT_FLOAT_EQ(result.best_partials[0].partial_score, 0.3f);
}

TEST(FailureResultBuilderTest, WithSuggestions) {
    auto result = FailureResultBuilder()
        .add_suggestion("early_stopping.level1_threshold", "0.4", "0.2", 
                       "High prune rate suggests threshold is too strict")
        .build();
    
    ASSERT_EQ(result.suggestions.size(), 1);
    EXPECT_EQ(result.suggestions[0].parameter_name, "early_stopping.level1_threshold");
    EXPECT_EQ(result.suggestions[0].current_value, "0.4");
    EXPECT_EQ(result.suggestions[0].suggested_value, "0.2");
}

TEST(FailureResultBuilderTest, GenerateSummary) {
    PartialMatch partial;
    partial.possible_format = "JPEG";
    partial.partial_score = 0.45f;
    
    auto result = FailureResultBuilder()
        .set_paths_explored(500000)
        .set_effective_depth(8)
        .add_partial_match(partial)
        .generate_summary()
        .build();
    
    EXPECT_FALSE(result.failure_summary.empty());
    EXPECT_NE(result.failure_summary.find("500"), std::string::npos); // Contains path count
}

TEST(FailureResultBuilderTest, GenerateSuggestionsFromMetrics) {
    ExtractionMetrics metrics;
    metrics.level1_prune_rate = 0.98f;  // Very high prune rate
    metrics.cache_hit_rate = 0.05f;     // Low cache hit rate
    metrics.paths_evaluated = 50000;
    metrics.effective_branching_factor = 7.0f;
    
    auto result = FailureResultBuilder()
        .generate_suggestions(metrics)
        .build();
    
    EXPECT_GT(result.suggestions.size(), 0);
}

// ============================================================================
// MetricsReporter Tests
// ============================================================================

TEST(MetricsReporterTest, BasicBuild) {
    auto metrics = MetricsReporter()
        .set_total_paths_possible(1000000)
        .set_paths_evaluated(50000)
        .set_paths_pruned_level1(30000)
        .set_paths_pruned_level2(15000)
        .set_paths_pruned_level3(5000)
        .build();
    
    EXPECT_EQ(metrics.total_paths_possible, 1000000);
    EXPECT_EQ(metrics.paths_evaluated, 50000);
    EXPECT_EQ(metrics.paths_pruned_level1, 30000);
    EXPECT_EQ(metrics.paths_pruned_level2, 15000);
    EXPECT_EQ(metrics.paths_pruned_level3, 5000);
}

TEST(MetricsReporterTest, EfficiencyMetrics) {
    auto metrics = MetricsReporter()
        .set_effective_branching_factor(2.5f)
        .set_effective_depth(8.0f)
        .set_cache_hit_rate(0.75f)
        .build();
    
    EXPECT_FLOAT_EQ(metrics.effective_branching_factor, 2.5f);
    EXPECT_FLOAT_EQ(metrics.effective_depth, 8.0f);
    EXPECT_FLOAT_EQ(metrics.cache_hit_rate, 0.75f);
}

TEST(MetricsReporterTest, CacheHitRateClamp) {
    auto metrics1 = MetricsReporter().set_cache_hit_rate(1.5f).build();
    EXPECT_FLOAT_EQ(metrics1.cache_hit_rate, 1.0f);
    
    auto metrics2 = MetricsReporter().set_cache_hit_rate(-0.5f).build();
    EXPECT_FLOAT_EQ(metrics2.cache_hit_rate, 0.0f);
}

TEST(MetricsReporterTest, FormatDistribution) {
    auto metrics = MetricsReporter()
        .add_format_detection("PNG", 10)
        .add_format_detection("JPEG", 5)
        .add_format_detection("PNG", 3)  // Should add to existing
        .build();
    
    ASSERT_EQ(metrics.format_distribution.size(), 2);
    
    // Find PNG entry
    bool found_png = false;
    for (const auto& [format, count] : metrics.format_distribution) {
        if (format == "PNG") {
            EXPECT_EQ(count, 13);  // 10 + 3
            found_png = true;
        }
    }
    EXPECT_TRUE(found_png);
}

TEST(MetricsReporterTest, CalculateDerivedMetrics) {
    auto metrics = MetricsReporter()
        .set_paths_evaluated(50000)
        .set_paths_pruned_level1(30000)
        .set_paths_pruned_level2(15000)
        .set_paths_pruned_level3(5000)
        .set_wall_clock_time(2.5)
        .calculate_derived_metrics()
        .build();
    
    // Check prune rates are calculated
    EXPECT_GT(metrics.level1_prune_rate, 0.0f);
    EXPECT_GT(metrics.level2_prune_rate, 0.0f);
    EXPECT_GT(metrics.level3_prune_rate, 0.0f);
    
    // Check average time per path
    EXPECT_GT(metrics.average_time_per_path_us, 0.0);
}

TEST(MetricsReporterTest, ComplexityReduction) {
    auto metrics = MetricsReporter()
        .set_total_paths_possible(1000000000)
        .set_paths_evaluated(100000)
        .set_effective_branching_factor(2.5f)
        .set_effective_depth(8.0f)
        .generate_complexity_reduction(32)
        .build();
    
    EXPECT_FALSE(metrics.complexity_reduction.empty());
    EXPECT_NE(metrics.complexity_reduction.find("O("), std::string::npos);
    EXPECT_NE(metrics.complexity_reduction.find("k="), std::string::npos);
}

TEST(MetricsReporterTest, ToStringMinimal) {
    MetricsReporter reporter;
    reporter.set_paths_evaluated(50000)
           .set_total_paths_possible(1000000)
           .set_wall_clock_time(1.5)
           .set_cache_hit_rate(0.75f);
    
    std::string output = reporter.to_string("minimal");
    EXPECT_FALSE(output.empty());
    EXPECT_NE(output.find("Paths:"), std::string::npos);
    EXPECT_NE(output.find("Time:"), std::string::npos);
    EXPECT_NE(output.find("Cache:"), std::string::npos);
}

TEST(MetricsReporterTest, ToStringFull) {
    MetricsReporter reporter;
    reporter.set_paths_evaluated(50000)
           .set_total_paths_possible(1000000)
           .set_paths_pruned_level1(30000)
           .set_wall_clock_time(1.5)
           .set_gpu_utilization(0.85f)
           .add_format_detection("PNG", 10)
           .calculate_derived_metrics();
    
    std::string output = reporter.to_string("full");
    EXPECT_FALSE(output.empty());
    EXPECT_NE(output.find("Path Statistics"), std::string::npos);
    EXPECT_NE(output.find("Efficiency"), std::string::npos);
    EXPECT_NE(output.find("Timing"), std::string::npos);
    EXPECT_NE(output.find("Format Distribution"), std::string::npos);
}

// ============================================================================
// ExtractionResultBuilder Tests
// ============================================================================

TEST(ExtractionResultBuilderTest, SuccessfulExtraction) {
    SuccessResult success;
    success.detected_format = "PNG";
    success.confidence = 0.95f;
    
    ExtractionMetrics metrics;
    metrics.paths_evaluated = 10000;
    
    auto result = ExtractionResultBuilder()
        .set_success(true)
        .add_candidate(success)
        .set_metrics(metrics)
        .build();
    
    EXPECT_TRUE(result.success);
    ASSERT_EQ(result.candidates.size(), 1);
    EXPECT_EQ(result.candidates[0].detected_format, "PNG");
    EXPECT_EQ(result.metrics.paths_evaluated, 10000);
    EXPECT_FALSE(result.failure.has_value());
}

TEST(ExtractionResultBuilderTest, FailedExtraction) {
    FailureResult failure;
    failure.paths_explored = 1000000;
    failure.failure_summary = "No valid candidates found";
    
    auto result = ExtractionResultBuilder()
        .set_success(false)
        .set_failure(failure)
        .build();
    
    EXPECT_FALSE(result.success);
    EXPECT_TRUE(result.candidates.empty());
    ASSERT_TRUE(result.failure.has_value());
    EXPECT_EQ(result.failure->paths_explored, 1000000);
}

TEST(ExtractionResultBuilderTest, AddCandidatesFromVector) {
    std::vector<Candidate> candidates;
    
    Candidate c1;
    c1.format_name = "PNG";
    c1.confidence = 0.95f;
    candidates.push_back(c1);
    
    Candidate c2;
    c2.format_name = "JPEG";
    c2.confidence = 0.85f;
    candidates.push_back(c2);
    
    auto result = ExtractionResultBuilder()
        .set_success(true)
        .add_candidates(candidates)
        .build();
    
    EXPECT_TRUE(result.success);
    ASSERT_EQ(result.candidates.size(), 2);
    EXPECT_EQ(result.candidates[0].detected_format, "PNG");
    EXPECT_EQ(result.candidates[1].detected_format, "JPEG");
}

// ============================================================================
// Utility Function Tests
// ============================================================================

TEST(UtilityFunctionsTest, FormatPath) {
    Path path;
    path.add(BitCoordinate(0, 3));
    path.add(BitCoordinate(1, 5));
    path.add(BitCoordinate(2, 1));
    
    std::string formatted = format_path(path);
    EXPECT_NE(formatted.find("(0,3)"), std::string::npos);
    EXPECT_NE(formatted.find("(1,5)"), std::string::npos);
    EXPECT_NE(formatted.find("(2,1)"), std::string::npos);
}

TEST(UtilityFunctionsTest, FormatPathTruncated) {
    Path path;
    for (uint32_t i = 0; i < 20; ++i) {
        path.add(BitCoordinate(i, i % 8));
    }
    
    std::string formatted = format_path(path, 5);
    EXPECT_NE(formatted.find("more"), std::string::npos);
}

TEST(UtilityFunctionsTest, FormatBytesHex) {
    std::vector<uint8_t> data = {0x89, 0x50, 0x4E, 0x47};
    
    std::string formatted = format_bytes_hex(data);
    EXPECT_NE(formatted.find("89"), std::string::npos);
    EXPECT_NE(formatted.find("50"), std::string::npos);
    EXPECT_NE(formatted.find("4E"), std::string::npos);
    EXPECT_NE(formatted.find("47"), std::string::npos);
}

TEST(UtilityFunctionsTest, FormatBytesHexTruncated) {
    std::vector<uint8_t> data(100, 0xAB);
    
    std::string formatted = format_bytes_hex(data, 10);
    EXPECT_NE(formatted.find("more"), std::string::npos);
}

TEST(UtilityFunctionsTest, FormatConfidence) {
    EXPECT_EQ(format_confidence(0.95f), "95.0%");
    EXPECT_EQ(format_confidence(0.5f), "50.0%");
    EXPECT_EQ(format_confidence(1.0f), "100.0%");
}

TEST(UtilityFunctionsTest, FormatDuration) {
    // Microseconds
    std::string us = format_duration(0.0001);
    EXPECT_NE(us.find("µs"), std::string::npos);
    
    // Milliseconds
    std::string ms = format_duration(0.5);
    EXPECT_NE(ms.find("ms"), std::string::npos);
    
    // Seconds
    std::string s = format_duration(5.0);
    EXPECT_NE(s.find("s"), std::string::npos);
    
    // Minutes
    std::string m = format_duration(120.0);
    EXPECT_NE(m.find("m"), std::string::npos);
    
    // Hours
    std::string h = format_duration(7200.0);
    EXPECT_NE(h.find("h"), std::string::npos);
}

TEST(UtilityFunctionsTest, FormatCount) {
    EXPECT_EQ(format_count(500), "500");
    EXPECT_NE(format_count(5000).find("K"), std::string::npos);
    EXPECT_NE(format_count(5000000).find("M"), std::string::npos);
    EXPECT_NE(format_count(5000000000).find("B"), std::string::npos);
}
