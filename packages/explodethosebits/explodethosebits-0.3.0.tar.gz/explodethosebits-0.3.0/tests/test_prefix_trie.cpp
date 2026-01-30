#include <gtest/gtest.h>
#include "etb/prefix_trie.hpp"
#include <vector>
#include <cstdint>

using namespace etb;

class PrefixTrieTest : public ::testing::Test {
protected:
    std::unique_ptr<PrefixTrie> trie;
    PrefixTrieConfig config;

    void SetUp() override {
        config = PrefixTrieConfig();
        trie = std::make_unique<PrefixTrie>(config);
    }
};

// ============================================================================
// Task 8.1: Prefix Trie Data Structure Tests
// ============================================================================

TEST_F(PrefixTrieTest, DefaultConstruction) {
    PrefixTrie default_trie;
    EXPECT_EQ(default_trie.node_count(), 1u);  // Root node
    EXPECT_EQ(default_trie.max_depth(), 16u);
}

TEST_F(PrefixTrieTest, CustomConfiguration) {
    PrefixTrieConfig custom;
    custom.max_depth = 8;
    custom.initial_capacity = 1024;
    custom.prune_threshold = 0.5f;
    
    PrefixTrie custom_trie(custom);
    EXPECT_EQ(custom_trie.max_depth(), 8u);
    EXPECT_EQ(custom_trie.get_config().prune_threshold, 0.5f);
}

TEST_F(PrefixTrieTest, NodeStatusValues) {
    // Verify status enum values match design spec
    EXPECT_EQ(static_cast<uint8_t>(PrefixStatus::UNKNOWN), 0);
    EXPECT_EQ(static_cast<uint8_t>(PrefixStatus::VALID), 1);
    EXPECT_EQ(static_cast<uint8_t>(PrefixStatus::PRUNED), 2);
}

TEST_F(PrefixTrieTest, RootNodeExists) {
    const PrefixTrieNode* root = trie->get_node(0);
    ASSERT_NE(root, nullptr);
    EXPECT_EQ(root->status, PrefixStatus::VALID);
}

TEST_F(PrefixTrieTest, NodeStructureFields) {
    std::vector<uint8_t> prefix = {0x89, 0x50};
    trie->insert(prefix, PrefixStatus::VALID, 0.75f);
    
    const PrefixTrieNode* node = trie->lookup(prefix);
    ASSERT_NE(node, nullptr);
    EXPECT_EQ(node->reconstructed_byte, 0x50);
    EXPECT_EQ(node->status, PrefixStatus::VALID);
    EXPECT_FLOAT_EQ(node->best_score, 0.75f);
    EXPECT_GE(node->visit_count, 1u);
}

// ============================================================================
// Task 8.2: Prefix Lookup and Update Operations Tests
// ============================================================================

TEST_F(PrefixTrieTest, LookupEmptyPrefix) {
    const PrefixTrieNode* node = trie->lookup(nullptr, 0);
    ASSERT_NE(node, nullptr);
    EXPECT_EQ(node->status, PrefixStatus::VALID);  // Root is always valid
}

TEST_F(PrefixTrieTest, LookupNonExistent) {
    std::vector<uint8_t> prefix = {0x01, 0x02, 0x03};
    const PrefixTrieNode* node = trie->lookup(prefix);
    EXPECT_EQ(node, nullptr);
}

TEST_F(PrefixTrieTest, InsertAndLookup) {
    std::vector<uint8_t> prefix = {0x89, 0x50, 0x4E, 0x47};  // PNG header
    uint32_t index = trie->insert(prefix, PrefixStatus::VALID, 0.9f);
    
    EXPECT_NE(index, UINT32_MAX);
    
    const PrefixTrieNode* node = trie->lookup(prefix);
    ASSERT_NE(node, nullptr);
    EXPECT_EQ(node->status, PrefixStatus::VALID);
    EXPECT_FLOAT_EQ(node->best_score, 0.9f);
}

TEST_F(PrefixTrieTest, InsertMultiplePrefixes) {
    std::vector<uint8_t> png = {0x89, 0x50, 0x4E, 0x47};
    std::vector<uint8_t> jpeg = {0xFF, 0xD8, 0xFF, 0xE0};
    
    trie->insert(png, PrefixStatus::VALID, 0.95f);
    trie->insert(jpeg, PrefixStatus::VALID, 0.90f);
    
    const PrefixTrieNode* png_node = trie->lookup(png);
    const PrefixTrieNode* jpeg_node = trie->lookup(jpeg);
    
    ASSERT_NE(png_node, nullptr);
    ASSERT_NE(jpeg_node, nullptr);
    EXPECT_FLOAT_EQ(png_node->best_score, 0.95f);
    EXPECT_FLOAT_EQ(jpeg_node->best_score, 0.90f);
}

TEST_F(PrefixTrieTest, UpdateStatus) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    uint32_t index = trie->insert(prefix, PrefixStatus::UNKNOWN, 0.5f);
    
    EXPECT_TRUE(trie->update_status(index, PrefixStatus::VALID));
    
    const PrefixTrieNode* node = trie->lookup(prefix);
    ASSERT_NE(node, nullptr);
    EXPECT_EQ(node->status, PrefixStatus::VALID);
}

TEST_F(PrefixTrieTest, UpdateStatusInvalidIndex) {
    EXPECT_FALSE(trie->update_status(9999, PrefixStatus::VALID));
}

TEST_F(PrefixTrieTest, UpdateScoreHigher) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    uint32_t index = trie->insert(prefix, PrefixStatus::VALID, 0.5f);
    
    EXPECT_TRUE(trie->update_score(index, 0.8f));
    
    const PrefixTrieNode* node = trie->lookup(prefix);
    ASSERT_NE(node, nullptr);
    EXPECT_FLOAT_EQ(node->best_score, 0.8f);
}

TEST_F(PrefixTrieTest, UpdateScoreLowerNoChange) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    uint32_t index = trie->insert(prefix, PrefixStatus::VALID, 0.8f);
    
    EXPECT_TRUE(trie->update_score(index, 0.5f));
    
    const PrefixTrieNode* node = trie->lookup(prefix);
    ASSERT_NE(node, nullptr);
    EXPECT_FLOAT_EQ(node->best_score, 0.8f);  // Should not decrease
}

TEST_F(PrefixTrieTest, LookupConsistency) {
    // Property 9: Trie Lookup Consistency - multiple lookups return same result
    std::vector<uint8_t> prefix = {0xAB, 0xCD, 0xEF};
    trie->insert(prefix, PrefixStatus::VALID, 0.7f);
    
    const PrefixTrieNode* lookup1 = trie->lookup(prefix);
    const PrefixTrieNode* lookup2 = trie->lookup(prefix);
    const PrefixTrieNode* lookup3 = trie->lookup(prefix);
    
    ASSERT_NE(lookup1, nullptr);
    EXPECT_EQ(lookup1, lookup2);
    EXPECT_EQ(lookup2, lookup3);
    EXPECT_EQ(lookup1->status, lookup2->status);
    EXPECT_FLOAT_EQ(lookup1->best_score, lookup2->best_score);
}


// ============================================================================
// Task 8.3: Branch Counting and Pruning Logic Tests
// ============================================================================

TEST_F(PrefixTrieTest, PrunePrefix) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    trie->insert(prefix, PrefixStatus::VALID, 0.5f);
    
    uint64_t pruned = trie->prune(prefix);
    
    const PrefixTrieNode* node = trie->lookup(prefix);
    ASSERT_NE(node, nullptr);
    EXPECT_EQ(node->status, PrefixStatus::PRUNED);
}

TEST_F(PrefixTrieTest, PruneEliminatesChildren) {
    // Property 8: Prefix Pruning Eliminates Children
    std::vector<uint8_t> parent = {0x01};
    std::vector<uint8_t> child1 = {0x01, 0x02};
    std::vector<uint8_t> child2 = {0x01, 0x03};
    std::vector<uint8_t> grandchild = {0x01, 0x02, 0x04};
    
    trie->insert(parent, PrefixStatus::VALID, 0.5f);
    trie->insert(child1, PrefixStatus::VALID, 0.6f);
    trie->insert(child2, PrefixStatus::VALID, 0.7f);
    trie->insert(grandchild, PrefixStatus::VALID, 0.8f);
    
    // Prune the parent
    uint64_t eliminated = trie->prune(parent);
    
    // All children should be pruned
    EXPECT_TRUE(trie->is_pruned(child1));
    EXPECT_TRUE(trie->is_pruned(child2));
    EXPECT_TRUE(trie->is_pruned(grandchild));
    EXPECT_GE(eliminated, 2u);  // At least child1 and child2
}

TEST_F(PrefixTrieTest, IsPrunedAncestor) {
    std::vector<uint8_t> parent = {0x01};
    std::vector<uint8_t> child = {0x01, 0x02};
    
    trie->insert(parent, PrefixStatus::VALID, 0.5f);
    trie->insert(child, PrefixStatus::VALID, 0.6f);
    
    // Prune parent
    trie->prune(parent);
    
    // Child should be considered pruned due to ancestor
    EXPECT_TRUE(trie->is_pruned(child));
}

TEST_F(PrefixTrieTest, IsPrunedNonExistent) {
    std::vector<uint8_t> prefix = {0x99, 0x88};
    EXPECT_FALSE(trie->is_pruned(prefix));
}

TEST_F(PrefixTrieTest, ValidBranchCount) {
    std::vector<uint8_t> p1 = {0x01};
    std::vector<uint8_t> p2 = {0x02};
    std::vector<uint8_t> p3 = {0x03};
    
    trie->insert(p1, PrefixStatus::VALID, 0.5f);
    trie->insert(p2, PrefixStatus::VALID, 0.6f);
    trie->insert(p3, PrefixStatus::PRUNED, 0.2f);
    
    EXPECT_EQ(trie->get_valid_branch_count(0), 2u);
    EXPECT_EQ(trie->get_pruned_branch_count(0), 1u);
}

TEST_F(PrefixTrieTest, EffectiveBranchingFactor) {
    // Insert some valid and pruned branches
    for (uint8_t i = 0; i < 8; ++i) {
        std::vector<uint8_t> prefix = {i};
        if (i < 2) {
            trie->insert(prefix, PrefixStatus::VALID, 0.5f);
        } else {
            trie->insert(prefix, PrefixStatus::PRUNED, 0.1f);
        }
    }
    
    float ebf = trie->get_effective_branching_factor();
    // With 2 valid out of 8, effective branching factor should be 2
    EXPECT_FLOAT_EQ(ebf, 2.0f);
}

TEST_F(PrefixTrieTest, PruneNonExistent) {
    std::vector<uint8_t> prefix = {0x99, 0x88};
    uint64_t pruned = trie->prune(prefix);
    EXPECT_EQ(pruned, 0u);
}

TEST_F(PrefixTrieTest, PruneAlreadyPruned) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    trie->insert(prefix, PrefixStatus::PRUNED, 0.1f);
    
    uint64_t pruned = trie->prune(prefix);
    EXPECT_EQ(pruned, 0u);  // Already pruned, no additional work
}

// ============================================================================
// Statistics and Clear Tests
// ============================================================================

TEST_F(PrefixTrieTest, StatisticsTracking) {
    trie->reset_statistics();
    
    std::vector<uint8_t> prefix = {0x01, 0x02};
    trie->insert(prefix, PrefixStatus::VALID, 0.5f);
    trie->lookup(prefix);
    trie->lookup(prefix);
    
    const auto& stats = trie->get_statistics();
    EXPECT_GE(stats.nodes_created, 2u);  // At least 2 nodes for 2-byte prefix
    EXPECT_GE(stats.total_lookups, 2u);
    EXPECT_GE(stats.cache_hits, 2u);
}

TEST_F(PrefixTrieTest, Clear) {
    std::vector<uint8_t> prefix = {0x01, 0x02, 0x03};
    trie->insert(prefix, PrefixStatus::VALID, 0.5f);
    
    EXPECT_GT(trie->node_count(), 1u);
    
    trie->clear();
    
    EXPECT_EQ(trie->node_count(), 1u);  // Only root
    EXPECT_EQ(trie->lookup(prefix), nullptr);
}

TEST_F(PrefixTrieTest, MaxDepthEnforced) {
    PrefixTrieConfig cfg;
    cfg.max_depth = 4;
    PrefixTrie limited_trie(cfg);
    
    std::vector<uint8_t> too_long = {0x01, 0x02, 0x03, 0x04, 0x05};
    uint32_t index = limited_trie.insert(too_long, PrefixStatus::VALID, 0.5f);
    
    EXPECT_EQ(index, UINT32_MAX);  // Should fail due to depth limit
}

TEST_F(PrefixTrieTest, VectorOverloads) {
    std::vector<uint8_t> prefix = {0xAA, 0xBB};
    
    trie->insert(prefix, PrefixStatus::VALID, 0.5f);
    
    const PrefixTrieNode* node = trie->lookup(prefix);
    ASSERT_NE(node, nullptr);
    
    EXPECT_FALSE(trie->is_pruned(prefix));
    
    trie->prune(prefix);
    EXPECT_TRUE(trie->is_pruned(prefix));
}

TEST_F(PrefixTrieTest, NodesAccessForGPU) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    trie->insert(prefix, PrefixStatus::VALID, 0.5f);
    
    const auto& nodes = trie->nodes();
    EXPECT_GT(nodes.size(), 1u);
    
    // Verify flat array layout is accessible
    for (const auto& node : nodes) {
        EXPECT_LE(static_cast<uint8_t>(node.status), 2);
    }
}


// ============================================================================
// Task 8.3: Additional Branch Counting and Threshold Pruning Tests
// ============================================================================

TEST_F(PrefixTrieTest, ShouldPruneLevelThreshold) {
    // Configure with branch_prune_count = 6 (default)
    // Insert 6 pruned and 2 valid branches at level 0
    for (uint8_t i = 0; i < 8; ++i) {
        std::vector<uint8_t> prefix = {i};
        if (i < 6) {
            trie->insert(prefix, PrefixStatus::PRUNED, 0.1f);
        } else {
            trie->insert(prefix, PrefixStatus::VALID, 0.5f);
        }
    }
    
    // Should trigger pruning since 6 out of 8 are pruned
    EXPECT_TRUE(trie->should_prune_level(0));
}

TEST_F(PrefixTrieTest, ShouldNotPruneLevelBelowThreshold) {
    // Insert 4 pruned and 4 valid branches at level 0
    for (uint8_t i = 0; i < 8; ++i) {
        std::vector<uint8_t> prefix = {i};
        if (i < 4) {
            trie->insert(prefix, PrefixStatus::PRUNED, 0.1f);
        } else {
            trie->insert(prefix, PrefixStatus::VALID, 0.5f);
        }
    }
    
    // Should not trigger pruning since only 4 out of 8 are pruned
    EXPECT_FALSE(trie->should_prune_level(0));
}

TEST_F(PrefixTrieTest, ShouldPruneLevelEmptyLevel) {
    EXPECT_FALSE(trie->should_prune_level(5));  // No data at level 5
}

TEST_F(PrefixTrieTest, EvaluateAndPruneBelowThreshold) {
    PrefixTrieConfig cfg;
    cfg.prune_threshold = 0.3f;
    PrefixTrie threshold_trie(cfg);
    
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    // Score below threshold should prune
    bool pruned = threshold_trie.evaluate_and_prune(prefix, 0.1f);
    EXPECT_TRUE(pruned);
    EXPECT_TRUE(threshold_trie.is_pruned(prefix));
}

TEST_F(PrefixTrieTest, EvaluateAndPruneAboveThreshold) {
    PrefixTrieConfig cfg;
    cfg.prune_threshold = 0.3f;
    PrefixTrie threshold_trie(cfg);
    
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    // Score above threshold should not prune
    bool pruned = threshold_trie.evaluate_and_prune(prefix, 0.5f);
    EXPECT_FALSE(pruned);
    EXPECT_FALSE(threshold_trie.is_pruned(prefix));
    
    const PrefixTrieNode* node = threshold_trie.lookup(prefix);
    ASSERT_NE(node, nullptr);
    EXPECT_EQ(node->status, PrefixStatus::VALID);
}

TEST_F(PrefixTrieTest, EvaluateAndPruneAtThreshold) {
    PrefixTrieConfig cfg;
    cfg.prune_threshold = 0.3f;
    PrefixTrie threshold_trie(cfg);
    
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    // Score exactly at threshold should not prune (>= threshold is valid)
    bool pruned = threshold_trie.evaluate_and_prune(prefix, 0.3f);
    EXPECT_FALSE(pruned);
}

TEST_F(PrefixTrieTest, GetTotalBranchCount) {
    std::vector<uint8_t> p1 = {0x01};
    std::vector<uint8_t> p2 = {0x02};
    std::vector<uint8_t> p3 = {0x03};
    
    trie->insert(p1, PrefixStatus::VALID, 0.5f);
    trie->insert(p2, PrefixStatus::VALID, 0.6f);
    trie->insert(p3, PrefixStatus::PRUNED, 0.2f);
    
    EXPECT_EQ(trie->get_total_branch_count(0), 3u);
}

TEST_F(PrefixTrieTest, BranchCountingMultipleLevels) {
    // Level 0 branches
    std::vector<uint8_t> l0_1 = {0x01};
    std::vector<uint8_t> l0_2 = {0x02};
    
    // Level 1 branches (children of l0_1)
    std::vector<uint8_t> l1_1 = {0x01, 0x10};
    std::vector<uint8_t> l1_2 = {0x01, 0x20};
    std::vector<uint8_t> l1_3 = {0x01, 0x30};
    
    trie->insert(l0_1, PrefixStatus::VALID, 0.5f);
    trie->insert(l0_2, PrefixStatus::PRUNED, 0.1f);
    trie->insert(l1_1, PrefixStatus::VALID, 0.6f);
    trie->insert(l1_2, PrefixStatus::VALID, 0.7f);
    trie->insert(l1_3, PrefixStatus::PRUNED, 0.2f);
    
    // Level 0: 1 valid, 1 pruned
    EXPECT_EQ(trie->get_valid_branch_count(0), 1u);
    EXPECT_EQ(trie->get_pruned_branch_count(0), 1u);
    
    // Level 1: 2 valid, 1 pruned
    EXPECT_EQ(trie->get_valid_branch_count(1), 2u);
    EXPECT_EQ(trie->get_pruned_branch_count(1), 1u);
}

TEST_F(PrefixTrieTest, CustomBranchPruneCount) {
    PrefixTrieConfig cfg;
    cfg.branch_prune_count = 3;  // Lower threshold
    PrefixTrie custom_trie(cfg);
    
    // Insert 3 pruned branches
    for (uint8_t i = 0; i < 3; ++i) {
        std::vector<uint8_t> prefix = {i};
        custom_trie.insert(prefix, PrefixStatus::PRUNED, 0.1f);
    }
    
    // Should trigger with custom threshold of 3
    EXPECT_TRUE(custom_trie.should_prune_level(0));
}
