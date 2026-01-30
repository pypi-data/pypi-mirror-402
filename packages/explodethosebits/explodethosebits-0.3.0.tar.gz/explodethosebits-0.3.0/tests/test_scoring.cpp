#include <gtest/gtest.h>
#include "etb/scoring.hpp"
#include <vector>
#include <cstdint>
#include <cmath>

using namespace etb;

// ============================================================================
// ScoringWeights Tests
// ============================================================================

TEST(ScoringWeightsTest, DefaultWeightsAreValid) {
    ScoringWeights weights;
    EXPECT_TRUE(weights.is_valid());
}

TEST(ScoringWeightsTest, DefaultWeightsSumToOne) {
    ScoringWeights weights;
    float sum = weights.signature_weight + weights.heuristic_weight +
                weights.length_weight + weights.structure_weight;
    EXPECT_NEAR(sum, 1.0f, 0.01f);
}

TEST(ScoringWeightsTest, DefaultWeightsMatchSpec) {
    // Requirements 8.1: signature (40%), heuristics (30%), length (15%), structure (15%)
    ScoringWeights weights;
    EXPECT_FLOAT_EQ(weights.signature_weight, 0.40f);
    EXPECT_FLOAT_EQ(weights.heuristic_weight, 0.30f);
    EXPECT_FLOAT_EQ(weights.length_weight, 0.15f);
    EXPECT_FLOAT_EQ(weights.structure_weight, 0.15f);
}

TEST(ScoringWeightsTest, NormalizeWeights) {
    ScoringWeights weights;
    weights.signature_weight = 2.0f;
    weights.heuristic_weight = 1.0f;
    weights.length_weight = 0.5f;
    weights.structure_weight = 0.5f;
    
    EXPECT_FALSE(weights.is_valid());
    
    weights.normalize();
    
    EXPECT_TRUE(weights.is_valid());
    EXPECT_NEAR(weights.signature_weight, 0.5f, 0.01f);
    EXPECT_NEAR(weights.heuristic_weight, 0.25f, 0.01f);
}

// ============================================================================
// ScoreCalculator Tests (Task 12.1)
// ============================================================================

class ScoreCalculatorTest : public ::testing::Test {
protected:
    ScoreCalculator calculator;
};

TEST_F(ScoreCalculatorTest, DefaultConstruction) {
    ScoreCalculator calc;
    const auto& weights = calc.get_weights();
    EXPECT_FLOAT_EQ(weights.signature_weight, 0.40f);
}

TEST_F(ScoreCalculatorTest, CustomWeightsConstruction) {
    ScoringWeights weights;
    weights.signature_weight = 0.5f;
    weights.heuristic_weight = 0.5f;
    weights.length_weight = 0.0f;
    weights.structure_weight = 0.0f;
    
    ScoreCalculator calc(weights);
    EXPECT_FLOAT_EQ(calc.get_weights().signature_weight, 0.5f);
}

TEST_F(ScoreCalculatorTest, SetWeights) {
    ScoringWeights weights;
    weights.signature_weight = 0.25f;
    weights.heuristic_weight = 0.25f;
    weights.length_weight = 0.25f;
    weights.structure_weight = 0.25f;
    
    calculator.set_weights(weights);
    EXPECT_FLOAT_EQ(calculator.get_weights().signature_weight, 0.25f);
}

TEST_F(ScoreCalculatorTest, CalculateAllZeros) {
    float score = calculator.calculate(0.0f, 0.0f, 0.0f, 0.0f);
    EXPECT_FLOAT_EQ(score, 0.0f);
}

TEST_F(ScoreCalculatorTest, CalculateAllOnes) {
    float score = calculator.calculate(1.0f, 1.0f, 1.0f, 1.0f);
    EXPECT_FLOAT_EQ(score, 1.0f);
}

TEST_F(ScoreCalculatorTest, CalculateWeightedSum) {
    // With default weights: 0.40, 0.30, 0.15, 0.15
    // Score = 1.0*0.40 + 0.5*0.30 + 0.0*0.15 + 0.0*0.15 = 0.55
    float score = calculator.calculate(1.0f, 0.5f, 0.0f, 0.0f);
    EXPECT_NEAR(score, 0.55f, 0.001f);
}

TEST_F(ScoreCalculatorTest, CalculateClampsInputs) {
    // Inputs outside [0,1] should be clamped
    float score = calculator.calculate(2.0f, -0.5f, 1.5f, -1.0f);
    EXPECT_GE(score, 0.0f);
    EXPECT_LE(score, 1.0f);
}

TEST_F(ScoreCalculatorTest, CalculateWithSignatureMatch) {
    SignatureMatch sig_match;
    sig_match.matched = true;
    sig_match.confidence = 0.9f;
    
    HeuristicResult heuristics;
    heuristics.composite_score = 0.8f;
    
    StructuralValidation structure;
    structure.validity_score = 0.7f;
    
    float score = calculator.calculate(sig_match, heuristics, 100, 100, structure);
    
    EXPECT_GT(score, 0.0f);
    EXPECT_LE(score, 1.0f);
}

TEST_F(ScoreCalculatorTest, CalculateNoSignatureMatch) {
    SignatureMatch sig_match;
    sig_match.matched = false;
    sig_match.confidence = 0.0f;
    
    HeuristicResult heuristics;
    heuristics.composite_score = 0.8f;
    
    StructuralValidation structure;
    structure.validity_score = 0.7f;
    
    float score = calculator.calculate(sig_match, heuristics, 100, 100, structure);
    
    // Without signature match, score should be lower
    EXPECT_GT(score, 0.0f);
    EXPECT_LT(score, 0.8f);  // Less than if signature matched
}

TEST_F(ScoreCalculatorTest, ScoreCandidateUpdatesFields) {
    Candidate candidate;
    candidate.data = {0x41, 0x42, 0x43, 0x44};
    candidate.signature_match.matched = true;
    candidate.signature_match.confidence = 0.9f;
    candidate.heuristics.composite_score = 0.8f;
    candidate.structure.validity_score = 0.7f;
    
    calculator.score_candidate(candidate, 4);
    
    EXPECT_GT(candidate.composite_score, 0.0f);
    EXPECT_LE(candidate.composite_score, 1.0f);
    EXPECT_EQ(candidate.confidence, candidate.composite_score);
}

TEST_F(ScoreCalculatorTest, LengthScoreExactMatch) {
    SignatureMatch sig_match;
    HeuristicResult heuristics;
    StructuralValidation structure;
    
    // Exact length match should give high length score
    float score1 = calculator.calculate(sig_match, heuristics, 100, 100, structure);
    float score2 = calculator.calculate(sig_match, heuristics, 50, 100, structure);
    
    // Exact match should score higher than 50% complete
    EXPECT_GT(score1, score2);
}

// ============================================================================
// CandidateQueue Tests (Task 12.2)
// ============================================================================

class CandidateQueueTest : public ::testing::Test {
protected:
    CandidateQueue queue{5};  // Capacity of 5
    
    Candidate make_candidate(float score) {
        Candidate c;
        c.composite_score = score;
        return c;
    }
};

TEST_F(CandidateQueueTest, DefaultConstruction) {
    CandidateQueue q;
    EXPECT_EQ(q.capacity(), 10);  // Default capacity
    EXPECT_TRUE(q.empty());
    EXPECT_EQ(q.size(), 0);
}

TEST_F(CandidateQueueTest, CustomCapacity) {
    CandidateQueue q(20);
    EXPECT_EQ(q.capacity(), 20);
}

TEST_F(CandidateQueueTest, PushSingleCandidate) {
    EXPECT_TRUE(queue.push(make_candidate(0.5f)));
    EXPECT_EQ(queue.size(), 1);
    EXPECT_FALSE(queue.empty());
}

TEST_F(CandidateQueueTest, PushMultipleCandidates) {
    queue.push(make_candidate(0.3f));
    queue.push(make_candidate(0.7f));
    queue.push(make_candidate(0.5f));
    
    EXPECT_EQ(queue.size(), 3);
}

TEST_F(CandidateQueueTest, TopReturnsHighestScore) {
    queue.push(make_candidate(0.3f));
    queue.push(make_candidate(0.9f));
    queue.push(make_candidate(0.5f));
    
    EXPECT_FLOAT_EQ(queue.top().composite_score, 0.9f);
}

TEST_F(CandidateQueueTest, PopReturnsHighestScore) {
    queue.push(make_candidate(0.3f));
    queue.push(make_candidate(0.9f));
    queue.push(make_candidate(0.5f));
    
    Candidate top = queue.pop();
    EXPECT_FLOAT_EQ(top.composite_score, 0.9f);
    EXPECT_EQ(queue.size(), 2);
}

TEST_F(CandidateQueueTest, PopInDescendingOrder) {
    queue.push(make_candidate(0.3f));
    queue.push(make_candidate(0.9f));
    queue.push(make_candidate(0.5f));
    queue.push(make_candidate(0.1f));
    queue.push(make_candidate(0.7f));
    
    EXPECT_FLOAT_EQ(queue.pop().composite_score, 0.9f);
    EXPECT_FLOAT_EQ(queue.pop().composite_score, 0.7f);
    EXPECT_FLOAT_EQ(queue.pop().composite_score, 0.5f);
    EXPECT_FLOAT_EQ(queue.pop().composite_score, 0.3f);
    EXPECT_FLOAT_EQ(queue.pop().composite_score, 0.1f);
}

TEST_F(CandidateQueueTest, FullQueueRejectsLowScore) {
    // Fill queue to capacity
    queue.push(make_candidate(0.5f));
    queue.push(make_candidate(0.6f));
    queue.push(make_candidate(0.7f));
    queue.push(make_candidate(0.8f));
    queue.push(make_candidate(0.9f));
    
    EXPECT_TRUE(queue.full());
    
    // Try to add lower score - should be rejected
    EXPECT_FALSE(queue.push(make_candidate(0.4f)));
    EXPECT_EQ(queue.size(), 5);
}

TEST_F(CandidateQueueTest, FullQueueAcceptsHighScore) {
    // Fill queue with low scores
    queue.push(make_candidate(0.1f));
    queue.push(make_candidate(0.2f));
    queue.push(make_candidate(0.3f));
    queue.push(make_candidate(0.4f));
    queue.push(make_candidate(0.5f));
    
    EXPECT_TRUE(queue.full());
    
    // Add higher score - should replace minimum
    EXPECT_TRUE(queue.push(make_candidate(0.9f)));
    EXPECT_EQ(queue.size(), 5);
    
    // Minimum should now be 0.2 (0.1 was replaced)
    EXPECT_GT(queue.min_score(), 0.1f);
}

TEST_F(CandidateQueueTest, MinScoreTracking) {
    EXPECT_FLOAT_EQ(queue.min_score(), 0.0f);  // Not full
    
    queue.push(make_candidate(0.5f));
    queue.push(make_candidate(0.6f));
    queue.push(make_candidate(0.7f));
    queue.push(make_candidate(0.8f));
    queue.push(make_candidate(0.9f));
    
    EXPECT_FLOAT_EQ(queue.min_score(), 0.5f);  // Full, min is 0.5
}

TEST_F(CandidateQueueTest, WouldAccept) {
    queue.push(make_candidate(0.5f));
    queue.push(make_candidate(0.6f));
    queue.push(make_candidate(0.7f));
    queue.push(make_candidate(0.8f));
    queue.push(make_candidate(0.9f));
    
    EXPECT_FALSE(queue.would_accept(0.4f));
    EXPECT_FALSE(queue.would_accept(0.5f));  // Equal to min
    EXPECT_TRUE(queue.would_accept(0.6f));   // Greater than min
}

TEST_F(CandidateQueueTest, GetTopKSortedDescending) {
    queue.push(make_candidate(0.3f));
    queue.push(make_candidate(0.9f));
    queue.push(make_candidate(0.5f));
    queue.push(make_candidate(0.1f));
    queue.push(make_candidate(0.7f));
    
    auto top_k = queue.get_top_k();
    
    EXPECT_EQ(top_k.size(), 5);
    EXPECT_FLOAT_EQ(top_k[0].composite_score, 0.9f);
    EXPECT_FLOAT_EQ(top_k[1].composite_score, 0.7f);
    EXPECT_FLOAT_EQ(top_k[2].composite_score, 0.5f);
    EXPECT_FLOAT_EQ(top_k[3].composite_score, 0.3f);
    EXPECT_FLOAT_EQ(top_k[4].composite_score, 0.1f);
}

TEST_F(CandidateQueueTest, Clear) {
    queue.push(make_candidate(0.5f));
    queue.push(make_candidate(0.6f));
    
    queue.clear();
    
    EXPECT_TRUE(queue.empty());
    EXPECT_EQ(queue.size(), 0);
    EXPECT_FLOAT_EQ(queue.min_score(), 0.0f);
}

TEST_F(CandidateQueueTest, SetCapacityIncrease) {
    queue.push(make_candidate(0.5f));
    queue.push(make_candidate(0.6f));
    
    queue.set_capacity(10);
    
    EXPECT_EQ(queue.capacity(), 10);
    EXPECT_EQ(queue.size(), 2);
}

TEST_F(CandidateQueueTest, SetCapacityDecrease) {
    queue.push(make_candidate(0.1f));
    queue.push(make_candidate(0.2f));
    queue.push(make_candidate(0.3f));
    queue.push(make_candidate(0.4f));
    queue.push(make_candidate(0.5f));
    
    queue.set_capacity(3);
    
    EXPECT_EQ(queue.capacity(), 3);
    EXPECT_EQ(queue.size(), 3);
    
    // Should keep highest scores
    auto top_k = queue.get_top_k();
    EXPECT_FLOAT_EQ(top_k[0].composite_score, 0.5f);
    EXPECT_FLOAT_EQ(top_k[1].composite_score, 0.4f);
    EXPECT_FLOAT_EQ(top_k[2].composite_score, 0.3f);
}

TEST_F(CandidateQueueTest, TopOnEmptyThrows) {
    CandidateQueue empty_queue;
    EXPECT_THROW(empty_queue.top(), std::runtime_error);
}

TEST_F(CandidateQueueTest, PopOnEmptyThrows) {
    CandidateQueue empty_queue;
    EXPECT_THROW(empty_queue.pop(), std::runtime_error);
}

TEST_F(CandidateQueueTest, MoveSemantics) {
    Candidate c = make_candidate(0.5f);
    c.data = {0x41, 0x42, 0x43};
    
    EXPECT_TRUE(queue.push(std::move(c)));
    
    const Candidate& top = queue.top();
    EXPECT_EQ(top.data.size(), 3);
}

// ============================================================================
// Integration Tests
// ============================================================================

TEST(ScoringIntegrationTest, FullWorkflow) {
    ScoreCalculator calculator;
    CandidateQueue queue(3);
    
    // Create and score multiple candidates
    for (int i = 0; i < 5; ++i) {
        Candidate c;
        c.data = std::vector<uint8_t>(10, static_cast<uint8_t>(i));
        c.signature_match.matched = (i % 2 == 0);
        c.signature_match.confidence = 0.5f + i * 0.1f;
        c.heuristics.composite_score = 0.3f + i * 0.1f;
        c.structure.validity_score = 0.6f;
        
        calculator.score_candidate(c, 10);
        queue.push(std::move(c));
    }
    
    // Should have top 3 candidates
    EXPECT_EQ(queue.size(), 3);
    
    // Get results sorted by score
    auto results = queue.get_top_k();
    EXPECT_EQ(results.size(), 3);
    
    // Verify descending order
    for (size_t i = 1; i < results.size(); ++i) {
        EXPECT_GE(results[i-1].composite_score, results[i].composite_score);
    }
}
