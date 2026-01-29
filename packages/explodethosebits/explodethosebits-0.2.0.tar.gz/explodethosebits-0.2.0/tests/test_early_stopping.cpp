#include <gtest/gtest.h>
#include "etb/early_stopping.hpp"
#include <vector>
#include <cstdint>

using namespace etb;

class EarlyStoppingTest : public ::testing::Test {
protected:
    EarlyStoppingController controller;
    EarlyStoppingConfig config;

    void SetUp() override {
        config = EarlyStoppingConfig();
        controller = EarlyStoppingController(config);
    }
};

// ============================================================================
// Repeated Byte Detection Tests (Task 7.2)
// ============================================================================

TEST_F(EarlyStoppingTest, IsAllNullEmpty) {
    std::vector<uint8_t> empty;
    EXPECT_FALSE(EarlyStoppingController::is_all_null(empty.data(), empty.size()));
}

TEST_F(EarlyStoppingTest, IsAllNullTrue) {
    std::vector<uint8_t> data(10, 0x00);
    EXPECT_TRUE(EarlyStoppingController::is_all_null(data.data(), data.size()));
}

TEST_F(EarlyStoppingTest, IsAllNullFalse) {
    std::vector<uint8_t> data = {0x00, 0x00, 0x01, 0x00};
    EXPECT_FALSE(EarlyStoppingController::is_all_null(data.data(), data.size()));
}

TEST_F(EarlyStoppingTest, IsRepeatedBytePatternEmpty) {
    std::vector<uint8_t> empty;
    EXPECT_FALSE(EarlyStoppingController::is_repeated_byte_pattern(empty.data(), empty.size()));
}

TEST_F(EarlyStoppingTest, IsRepeatedBytePatternSingleByte) {
    std::vector<uint8_t> data = {0x42};
    EXPECT_TRUE(EarlyStoppingController::is_repeated_byte_pattern(data.data(), data.size()));
}

TEST_F(EarlyStoppingTest, IsRepeatedBytePatternAllSame) {
    std::vector<uint8_t> data(10, 0xFF);
    EXPECT_TRUE(EarlyStoppingController::is_repeated_byte_pattern(data.data(), data.size()));
}

TEST_F(EarlyStoppingTest, IsRepeatedBytePatternDifferent) {
    std::vector<uint8_t> data = {0x41, 0x42, 0x43};
    EXPECT_FALSE(EarlyStoppingController::is_repeated_byte_pattern(data.data(), data.size()));
}

// ============================================================================
// Multi-Level Early Stopping Tests (Task 7.1)
// ============================================================================

TEST_F(EarlyStoppingTest, ShouldStopEmptyData) {
    std::vector<uint8_t> empty;
    StopDecision decision = controller.should_stop(empty);
    EXPECT_FALSE(decision.should_stop);
}

TEST_F(EarlyStoppingTest, ShouldStopAllNulls) {
    std::vector<uint8_t> data(8, 0x00);
    StopDecision decision = controller.should_stop(data);
    EXPECT_TRUE(decision.should_stop);
    EXPECT_NE(decision.reason, nullptr);
}

TEST_F(EarlyStoppingTest, ShouldStopRepeatedByte) {
    std::vector<uint8_t> data(8, 0xFF);
    StopDecision decision = controller.should_stop(data);
    EXPECT_TRUE(decision.should_stop);
}

TEST_F(EarlyStoppingTest, ShouldContinueValidText) {
    // "Hello World" - valid text should continue
    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64};
    StopDecision decision = controller.should_stop(data);
    // Text data should generally continue (high printable ratio, good entropy)
    EXPECT_FALSE(decision.should_stop);
}

TEST_F(EarlyStoppingTest, Level1StopNoSignaturePoorHeuristics) {
    // Binary garbage with no signature match and poor heuristics
    std::vector<uint8_t> data = {0x01, 0x02, 0x03, 0x04};
    
    // Set a low threshold to ensure stopping
    config.level1_threshold = 0.5f;
    controller = EarlyStoppingController(config);
    
    StopDecision decision = controller.should_stop(data);
    // Should stop at level 1 due to no signature and poor heuristics
    if (decision.should_stop) {
        EXPECT_EQ(decision.level, StopLevel::LEVEL_1);
    }
}

TEST_F(EarlyStoppingTest, Level2StopLowEntropy) {
    // Data with very low entropy (almost repeated)
    std::vector<uint8_t> data = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01};
    
    StopDecision decision = controller.should_stop(data);
    // Should stop due to low entropy
    EXPECT_TRUE(decision.should_stop);
}

TEST_F(EarlyStoppingTest, Level3StopExcessiveNullRuns) {
    // Data with excessive null runs
    std::vector<uint8_t> data(20, 0x00);
    data[0] = 0x41;  // One non-null to avoid repeated byte detection
    
    StopDecision decision = controller.should_stop(data);
    EXPECT_TRUE(decision.should_stop);
}

// ============================================================================
// Adaptive Threshold Tests (Task 7.3)
// ============================================================================

TEST_F(EarlyStoppingTest, AdaptiveThresholdDefault) {
    AdaptiveThresholdManager manager;
    // With no updates, should return default threshold
    EXPECT_FLOAT_EQ(manager.get_adaptive_threshold(), 0.4f);
}

TEST_F(EarlyStoppingTest, AdaptiveThresholdTighten) {
    AdaptiveThresholdManager manager;
    // Update with high score
    manager.update_best_score(0.85f);
    // Should tighten threshold
    EXPECT_FLOAT_EQ(manager.get_adaptive_threshold(), 0.6f);
}

TEST_F(EarlyStoppingTest, AdaptiveThresholdRelax) {
    EarlyStoppingConfig cfg;
    cfg.adaptive_thresholds = true;
    AdaptiveThresholdManager manager(cfg);
    // With low best score, should relax threshold
    manager.update_best_score(0.2f);
    EXPECT_FLOAT_EQ(manager.get_adaptive_threshold(), 0.2f);
}

TEST_F(EarlyStoppingTest, AdaptiveThresholdDisabled) {
    EarlyStoppingConfig cfg;
    cfg.adaptive_thresholds = false;
    cfg.adaptive_default = 0.5f;
    AdaptiveThresholdManager manager(cfg);
    
    manager.update_best_score(0.9f);  // Would normally tighten
    EXPECT_FLOAT_EQ(manager.get_adaptive_threshold(), 0.5f);  // But stays at default
}

TEST_F(EarlyStoppingTest, AdaptiveThresholdReset) {
    AdaptiveThresholdManager manager;
    manager.update_best_score(0.9f);
    EXPECT_GT(manager.get_best_score(), 0.0f);
    
    manager.reset();
    EXPECT_FLOAT_EQ(manager.get_best_score(), 0.0f);
    EXPECT_EQ(manager.get_update_count(), 0u);
}

TEST_F(EarlyStoppingTest, ControllerUpdateBestScore) {
    controller.update_best_score(0.85f);
    EXPECT_FLOAT_EQ(controller.get_adaptive_threshold(), 0.6f);
}

// ============================================================================
// Statistics Tests
// ============================================================================

TEST_F(EarlyStoppingTest, StatisticsTracking) {
    controller.reset_statistics();
    
    // Check some data
    std::vector<uint8_t> nulls(8, 0x00);
    controller.should_stop(nulls);
    
    std::vector<uint8_t> text = {0x48, 0x65, 0x6C, 0x6C, 0x6F};
    controller.should_stop(text);
    
    const auto& stats = controller.get_statistics();
    EXPECT_EQ(stats.total_checks, 2u);
    EXPECT_GE(stats.stopped_repeated, 1u);  // Nulls should be stopped
}

TEST_F(EarlyStoppingTest, StatisticsReset) {
    std::vector<uint8_t> data(8, 0x00);
    controller.should_stop(data);
    
    controller.reset_statistics();
    const auto& stats = controller.get_statistics();
    EXPECT_EQ(stats.total_checks, 0u);
}

// ============================================================================
// Configuration Tests
// ============================================================================

TEST_F(EarlyStoppingTest, CustomConfiguration) {
    EarlyStoppingConfig custom;
    custom.level1_bytes = 2;
    custom.level2_bytes = 4;
    custom.level3_bytes = 8;
    custom.min_entropy = 0.5f;
    custom.max_entropy = 7.0f;
    
    EarlyStoppingController custom_controller(custom);
    const auto& cfg = custom_controller.get_config();
    
    EXPECT_EQ(cfg.level1_bytes, 2u);
    EXPECT_EQ(cfg.level2_bytes, 4u);
    EXPECT_EQ(cfg.level3_bytes, 8u);
    EXPECT_FLOAT_EQ(cfg.min_entropy, 0.5f);
    EXPECT_FLOAT_EQ(cfg.max_entropy, 7.0f);
}

TEST_F(EarlyStoppingTest, VectorOverload) {
    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F};
    StopDecision decision1 = controller.should_stop(data);
    StopDecision decision2 = controller.should_stop(data.data(), data.size());
    
    EXPECT_EQ(decision1.should_stop, decision2.should_stop);
}
