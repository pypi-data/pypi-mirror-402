#include <gtest/gtest.h>
#include "etb/heuristics.hpp"
#include <vector>
#include <cstdint>
#include <cmath>
#include <string>

using namespace etb;

class HeuristicsEngineTest : public ::testing::Test {
protected:
    HeuristicsEngine engine;
};

// ============================================================================
// Shannon Entropy Tests (Task 5.1)
// ============================================================================

TEST_F(HeuristicsEngineTest, EntropyEmptyData) {
    std::vector<uint8_t> empty;
    float entropy = HeuristicsEngine::calculate_entropy(empty);
    EXPECT_FLOAT_EQ(entropy, 0.0f);
}

TEST_F(HeuristicsEngineTest, EntropyAllSameByte) {
    // All same bytes = 0 entropy
    std::vector<uint8_t> data(100, 0x42);
    float entropy = HeuristicsEngine::calculate_entropy(data);
    EXPECT_FLOAT_EQ(entropy, 0.0f);
}

TEST_F(HeuristicsEngineTest, EntropyTwoEqualBytes) {
    // Two equally distributed bytes = 1 bit of entropy
    std::vector<uint8_t> data;
    for (int i = 0; i < 50; ++i) {
        data.push_back(0x00);
        data.push_back(0xFF);
    }
    float entropy = HeuristicsEngine::calculate_entropy(data);
    EXPECT_NEAR(entropy, 1.0f, 0.01f);
}

TEST_F(HeuristicsEngineTest, EntropyMaximum) {
    // All 256 byte values equally distributed = 8 bits of entropy
    std::vector<uint8_t> data;
    for (int i = 0; i < 256; ++i) {
        data.push_back(static_cast<uint8_t>(i));
    }
    float entropy = HeuristicsEngine::calculate_entropy(data);
    EXPECT_NEAR(entropy, 8.0f, 0.01f);
}

TEST_F(HeuristicsEngineTest, EntropyInValidRange) {
    // Random-ish data should have entropy in [0, 8]
    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64};
    float entropy = HeuristicsEngine::calculate_entropy(data);
    EXPECT_GE(entropy, 0.0f);
    EXPECT_LE(entropy, 8.0f);
}

TEST_F(HeuristicsEngineTest, EntropyPointerOverload) {
    std::vector<uint8_t> data = {0x00, 0xFF, 0x00, 0xFF};
    float entropy1 = HeuristicsEngine::calculate_entropy(data);
    float entropy2 = HeuristicsEngine::calculate_entropy(data.data(), data.size());
    EXPECT_FLOAT_EQ(entropy1, entropy2);
}

// ============================================================================
// Byte Distribution Tests (Task 5.2)
// ============================================================================

TEST_F(HeuristicsEngineTest, PrintableRatioEmptyData) {
    std::vector<uint8_t> empty;
    float ratio = HeuristicsEngine::calculate_printable_ratio(empty.data(), empty.size());
    EXPECT_FLOAT_EQ(ratio, 0.0f);
}

TEST_F(HeuristicsEngineTest, PrintableRatioAllPrintable) {
    // "Hello World" - all printable ASCII
    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64};
    float ratio = HeuristicsEngine::calculate_printable_ratio(data.data(), data.size());
    EXPECT_FLOAT_EQ(ratio, 1.0f);
}

TEST_F(HeuristicsEngineTest, PrintableRatioNonePrintable) {
    // All null bytes - not printable
    std::vector<uint8_t> data(10, 0x00);
    float ratio = HeuristicsEngine::calculate_printable_ratio(data.data(), data.size());
    EXPECT_FLOAT_EQ(ratio, 0.0f);
}

TEST_F(HeuristicsEngineTest, PrintableRatioMixed) {
    // 5 printable + 5 non-printable = 0.5 ratio
    std::vector<uint8_t> data = {0x41, 0x42, 0x43, 0x44, 0x45, 0x00, 0x01, 0x02, 0x03, 0x04};
    float ratio = HeuristicsEngine::calculate_printable_ratio(data.data(), data.size());
    EXPECT_FLOAT_EQ(ratio, 0.5f);
}

TEST_F(HeuristicsEngineTest, PrintableRatioBoundaries) {
    // Test boundary values: 0x20 (space) and 0x7E (~) are printable
    std::vector<uint8_t> data = {0x1F, 0x20, 0x7E, 0x7F};
    float ratio = HeuristicsEngine::calculate_printable_ratio(data.data(), data.size());
    EXPECT_FLOAT_EQ(ratio, 0.5f);  // 0x20 and 0x7E are printable
}

TEST_F(HeuristicsEngineTest, ControlCharRatioEmptyData) {
    std::vector<uint8_t> empty;
    float ratio = HeuristicsEngine::calculate_control_char_ratio(empty.data(), empty.size());
    EXPECT_FLOAT_EQ(ratio, 0.0f);
}

TEST_F(HeuristicsEngineTest, ControlCharRatioAllControl) {
    // All control chars (excluding whitespace)
    std::vector<uint8_t> data = {0x00, 0x01, 0x02, 0x03, 0x04};
    float ratio = HeuristicsEngine::calculate_control_char_ratio(data.data(), data.size());
    EXPECT_FLOAT_EQ(ratio, 1.0f);
}

TEST_F(HeuristicsEngineTest, ControlCharRatioWhitespaceExcluded) {
    // Tab, LF, CR should NOT be counted as control chars
    std::vector<uint8_t> data = {0x09, 0x0A, 0x0D, 0x00, 0x01};  // Tab, LF, CR, NUL, SOH
    float ratio = HeuristicsEngine::calculate_control_char_ratio(data.data(), data.size());
    EXPECT_FLOAT_EQ(ratio, 0.4f);  // Only 0x00 and 0x01 are control chars
}

TEST_F(HeuristicsEngineTest, ControlCharRatioNoneControl) {
    // All printable ASCII
    std::vector<uint8_t> data = {0x41, 0x42, 0x43, 0x44, 0x45};
    float ratio = HeuristicsEngine::calculate_control_char_ratio(data.data(), data.size());
    EXPECT_FLOAT_EQ(ratio, 0.0f);
}

TEST_F(HeuristicsEngineTest, MaxNullRunEmptyData) {
    std::vector<uint8_t> empty;
    uint32_t run = HeuristicsEngine::find_max_null_run(empty.data(), empty.size());
    EXPECT_EQ(run, 0u);
}

TEST_F(HeuristicsEngineTest, MaxNullRunNoNulls) {
    std::vector<uint8_t> data = {0x41, 0x42, 0x43, 0x44, 0x45};
    uint32_t run = HeuristicsEngine::find_max_null_run(data.data(), data.size());
    EXPECT_EQ(run, 0u);
}

TEST_F(HeuristicsEngineTest, MaxNullRunAllNulls) {
    std::vector<uint8_t> data(10, 0x00);
    uint32_t run = HeuristicsEngine::find_max_null_run(data.data(), data.size());
    EXPECT_EQ(run, 10u);
}

TEST_F(HeuristicsEngineTest, MaxNullRunMultipleRuns) {
    // Two runs: 3 nulls, then 5 nulls
    std::vector<uint8_t> data = {0x00, 0x00, 0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x42};
    uint32_t run = HeuristicsEngine::find_max_null_run(data.data(), data.size());
    EXPECT_EQ(run, 5u);
}

TEST_F(HeuristicsEngineTest, MaxNullRunAtEnd) {
    std::vector<uint8_t> data = {0x41, 0x42, 0x00, 0x00, 0x00, 0x00};
    uint32_t run = HeuristicsEngine::find_max_null_run(data.data(), data.size());
    EXPECT_EQ(run, 4u);
}

// ============================================================================
// UTF-8 Validation Tests (Task 5.3)
// ============================================================================

TEST_F(HeuristicsEngineTest, Utf8ValidEmpty) {
    std::vector<uint8_t> empty;
    float validity = HeuristicsEngine::validate_utf8(empty.data(), empty.size());
    EXPECT_FLOAT_EQ(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8ValidAscii) {
    // Pure ASCII is valid UTF-8
    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F};  // "Hello"
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_FLOAT_EQ(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8ValidTwoByteSequence) {
    // Valid 2-byte UTF-8: é (U+00E9) = 0xC3 0xA9
    std::vector<uint8_t> data = {0xC3, 0xA9};
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_FLOAT_EQ(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8ValidThreeByteSequence) {
    // Valid 3-byte UTF-8: € (U+20AC) = 0xE2 0x82 0xAC
    std::vector<uint8_t> data = {0xE2, 0x82, 0xAC};
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_FLOAT_EQ(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8ValidFourByteSequence) {
    // Valid 4-byte UTF-8: 😀 (U+1F600) = 0xF0 0x9F 0x98 0x80
    std::vector<uint8_t> data = {0xF0, 0x9F, 0x98, 0x80};
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_FLOAT_EQ(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8InvalidContinuationByte) {
    // Continuation byte without start byte
    std::vector<uint8_t> data = {0x80, 0x41};
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_LT(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8InvalidTruncatedSequence) {
    // Start of 2-byte sequence without continuation
    std::vector<uint8_t> data = {0xC3};
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_LT(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8InvalidOverlongEncoding) {
    // Overlong encoding of ASCII 'A' (should be 0x41, not 0xC1 0x81)
    std::vector<uint8_t> data = {0xC0, 0x81};
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_LT(validity, 1.0f);
}

TEST_F(HeuristicsEngineTest, Utf8MixedValidInvalid) {
    // Mix of valid and invalid: "A" + invalid + "B"
    std::vector<uint8_t> data = {0x41, 0x80, 0x42};  // A, invalid continuation, B
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    // 2 valid out of 3 sequences
    EXPECT_NEAR(validity, 2.0f / 3.0f, 0.01f);
}

TEST_F(HeuristicsEngineTest, Utf8ValidMixedSequences) {
    // "Héllo" - mix of ASCII and 2-byte UTF-8
    std::vector<uint8_t> data = {0x48, 0xC3, 0xA9, 0x6C, 0x6C, 0x6F};
    float validity = HeuristicsEngine::validate_utf8(data.data(), data.size());
    EXPECT_FLOAT_EQ(validity, 1.0f);
}

// ============================================================================
// Composite Heuristic Tests (Task 5.4)
// ============================================================================

TEST_F(HeuristicsEngineTest, AnalyzeEmptyData) {
    std::vector<uint8_t> empty;
    HeuristicResult result = engine.analyze(empty);
    
    EXPECT_FLOAT_EQ(result.entropy, 0.0f);
    EXPECT_FLOAT_EQ(result.printable_ratio, 0.0f);
    EXPECT_FLOAT_EQ(result.control_char_ratio, 0.0f);
    EXPECT_EQ(result.max_null_run, 0u);
    EXPECT_FLOAT_EQ(result.utf8_validity, 0.0f);  // Empty returns 0 from analyze
}

TEST_F(HeuristicsEngineTest, AnalyzeTextData) {
    // "Hello World" - typical text
    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64};
    HeuristicResult result = engine.analyze(data);
    
    EXPECT_GT(result.entropy, 0.0f);
    EXPECT_LE(result.entropy, 8.0f);
    EXPECT_FLOAT_EQ(result.printable_ratio, 1.0f);
    EXPECT_FLOAT_EQ(result.control_char_ratio, 0.0f);
    EXPECT_EQ(result.max_null_run, 0u);
    EXPECT_FLOAT_EQ(result.utf8_validity, 1.0f);
    EXPECT_GT(result.composite_score, 0.0f);
    EXPECT_LE(result.composite_score, 1.0f);
}

TEST_F(HeuristicsEngineTest, AnalyzeBinaryData) {
    // Binary data with nulls and control chars
    std::vector<uint8_t> data = {0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0xFF};
    HeuristicResult result = engine.analyze(data);
    
    EXPECT_GT(result.entropy, 0.0f);
    EXPECT_FLOAT_EQ(result.printable_ratio, 0.0f);
    EXPECT_GT(result.control_char_ratio, 0.0f);
    EXPECT_EQ(result.max_null_run, 4u);
}

TEST_F(HeuristicsEngineTest, AnalyzePointerOverload) {
    std::vector<uint8_t> data = {0x41, 0x42, 0x43};
    HeuristicResult result1 = engine.analyze(data);
    HeuristicResult result2 = engine.analyze(data.data(), data.size());
    
    EXPECT_FLOAT_EQ(result1.entropy, result2.entropy);
    EXPECT_FLOAT_EQ(result1.printable_ratio, result2.printable_ratio);
    EXPECT_FLOAT_EQ(result1.composite_score, result2.composite_score);
}

TEST_F(HeuristicsEngineTest, CompositeScoreInRange) {
    // Various data types should all produce scores in [0, 1]
    std::vector<std::vector<uint8_t>> test_data = {
        {0x00},                                          // Single null
        {0xFF, 0xFF, 0xFF},                              // All 0xFF
        {0x41, 0x42, 0x43, 0x44, 0x45},                  // ASCII text
        {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07}, // Sequential bytes
    };
    
    for (const auto& data : test_data) {
        HeuristicResult result = engine.analyze(data);
        EXPECT_GE(result.composite_score, 0.0f);
        EXPECT_LE(result.composite_score, 1.0f);
    }
}

TEST_F(HeuristicsEngineTest, CustomWeights) {
    HeuristicWeights weights;
    weights.entropy_weight = 1.0f;
    weights.printable_weight = 0.0f;
    weights.control_char_weight = 0.0f;
    weights.null_run_weight = 0.0f;
    weights.utf8_weight = 0.0f;
    
    HeuristicsEngine custom_engine(weights);
    
    std::vector<uint8_t> data = {0x41, 0x42, 0x43};
    HeuristicResult result = custom_engine.analyze(data);
    
    // With only entropy weight, score should be based on entropy quality
    EXPECT_GE(result.composite_score, 0.0f);
    EXPECT_LE(result.composite_score, 1.0f);
}

TEST_F(HeuristicsEngineTest, SetWeights) {
    HeuristicWeights new_weights;
    new_weights.entropy_weight = 0.5f;
    
    engine.set_weights(new_weights);
    
    EXPECT_FLOAT_EQ(engine.get_weights().entropy_weight, 0.5f);
}

TEST_F(HeuristicsEngineTest, TextDataHigherScoreThanBinary) {
    // Text data should generally score higher than binary garbage
    std::vector<uint8_t> text_data = {0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64};
    std::vector<uint8_t> binary_data = {0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0xFF, 0xFE, 0xFD, 0xFC};
    
    HeuristicResult text_result = engine.analyze(text_data);
    HeuristicResult binary_result = engine.analyze(binary_data);
    
    EXPECT_GT(text_result.composite_score, binary_result.composite_score);
}

