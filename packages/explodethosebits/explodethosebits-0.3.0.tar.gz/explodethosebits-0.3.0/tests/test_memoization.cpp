#include <gtest/gtest.h>
#include "etb/memoization.hpp"
#include <vector>
#include <cstdint>
#include <thread>

using namespace etb;

class MemoizationTest : public ::testing::Test {
protected:
    std::unique_ptr<PrefixCache> cache;
    MemoizationConfig config;

    void SetUp() override {
        config = MemoizationConfig();
        cache = std::make_unique<PrefixCache>(config);
    }

    HeuristicResult make_heuristic(float entropy, float printable) {
        HeuristicResult h;
        h.entropy = entropy;
        h.printable_ratio = printable;
        h.composite_score = (entropy + printable) / 2.0f;
        return h;
    }
};

// ============================================================================
// Task 10.1: Prefix Result Cache Tests
// ============================================================================

TEST_F(MemoizationTest, DefaultConstruction) {
    PrefixCache default_cache;
    EXPECT_TRUE(default_cache.is_enabled());
    EXPECT_EQ(default_cache.size(), 0u);
    EXPECT_TRUE(default_cache.empty());
}

TEST_F(MemoizationTest, CustomConfiguration) {
    MemoizationConfig custom;
    custom.max_entries = 100;
    custom.max_size_bytes = 1024;
    custom.enabled = true;
    
    PrefixCache custom_cache(custom);
    EXPECT_EQ(custom_cache.get_config().max_entries, 100u);
    EXPECT_EQ(custom_cache.get_config().max_size_bytes, 1024u);
}

TEST_F(MemoizationTest, InsertAndLookup) {
    std::vector<uint8_t> prefix = {0x89, 0x50, 0x4E, 0x47};
    HeuristicResult h = make_heuristic(5.0f, 0.8f);
    
    EXPECT_TRUE(cache->insert(prefix, h, 0.9f, false));
    EXPECT_EQ(cache->size(), 1u);
    
    auto result = cache->lookup(prefix);
    ASSERT_TRUE(result.has_value());
    EXPECT_FLOAT_EQ(result->score, 0.9f);
    EXPECT_FALSE(result->should_prune);
    EXPECT_FLOAT_EQ(result->heuristics.entropy, 5.0f);
}

TEST_F(MemoizationTest, LookupNonExistent) {
    std::vector<uint8_t> prefix = {0x01, 0x02, 0x03};
    auto result = cache->lookup(prefix);
    EXPECT_FALSE(result.has_value());
}

TEST_F(MemoizationTest, InsertMultiplePrefixes) {
    std::vector<uint8_t> p1 = {0x89, 0x50};
    std::vector<uint8_t> p2 = {0xFF, 0xD8};
    std::vector<uint8_t> p3 = {0x25, 0x50};
    
    cache->insert(p1, make_heuristic(5.0f, 0.8f), 0.9f, false);
    cache->insert(p2, make_heuristic(6.0f, 0.7f), 0.85f, false);
    cache->insert(p3, make_heuristic(4.0f, 0.9f), 0.75f, true);
    
    EXPECT_EQ(cache->size(), 3u);
    
    auto r1 = cache->lookup(p1);
    auto r2 = cache->lookup(p2);
    auto r3 = cache->lookup(p3);
    
    ASSERT_TRUE(r1.has_value());
    ASSERT_TRUE(r2.has_value());
    ASSERT_TRUE(r3.has_value());
    
    EXPECT_FLOAT_EQ(r1->score, 0.9f);
    EXPECT_FLOAT_EQ(r2->score, 0.85f);
    EXPECT_FLOAT_EQ(r3->score, 0.75f);
    EXPECT_TRUE(r3->should_prune);
}

TEST_F(MemoizationTest, UpdateExistingEntry) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    auto r1 = cache->lookup(prefix);
    ASSERT_TRUE(r1.has_value());
    EXPECT_FLOAT_EQ(r1->score, 0.5f);
    
    // Update with new values
    cache->insert(prefix, make_heuristic(6.0f, 0.9f), 0.8f, true);
    
    auto r2 = cache->lookup(prefix);
    ASSERT_TRUE(r2.has_value());
    EXPECT_FLOAT_EQ(r2->score, 0.8f);
    EXPECT_TRUE(r2->should_prune);
    
    // Size should still be 1
    EXPECT_EQ(cache->size(), 1u);
}

TEST_F(MemoizationTest, ContainsCheck) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    EXPECT_FALSE(cache->contains(prefix));
    
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    EXPECT_TRUE(cache->contains(prefix));
}

TEST_F(MemoizationTest, RemoveEntry) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    EXPECT_EQ(cache->size(), 1u);
    
    EXPECT_TRUE(cache->remove(prefix));
    EXPECT_EQ(cache->size(), 0u);
    EXPECT_FALSE(cache->contains(prefix));
}

TEST_F(MemoizationTest, RemoveNonExistent) {
    std::vector<uint8_t> prefix = {0x99, 0x88};
    EXPECT_FALSE(cache->remove(prefix));
}

TEST_F(MemoizationTest, Clear) {
    cache->insert({0x01}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    cache->insert({0x02}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    cache->insert({0x03}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    EXPECT_EQ(cache->size(), 3u);
    
    cache->clear();
    
    EXPECT_EQ(cache->size(), 0u);
    EXPECT_TRUE(cache->empty());
}

TEST_F(MemoizationTest, DisabledCache) {
    MemoizationConfig disabled_config;
    disabled_config.enabled = false;
    PrefixCache disabled_cache(disabled_config);
    
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    // Insert should fail when disabled
    EXPECT_FALSE(disabled_cache.insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false));
    
    // Lookup should return empty
    auto result = disabled_cache.lookup(prefix);
    EXPECT_FALSE(result.has_value());
    
    // Contains should return false
    EXPECT_FALSE(disabled_cache.contains(prefix));
}

TEST_F(MemoizationTest, EnableDisableRuntime) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    EXPECT_TRUE(cache->lookup(prefix).has_value());
    
    cache->set_enabled(false);
    EXPECT_FALSE(cache->is_enabled());
    
    // Lookup should fail when disabled
    auto result = cache->lookup(prefix);
    EXPECT_FALSE(result.has_value());
    
    cache->set_enabled(true);
    // Entry should still be there
    EXPECT_TRUE(cache->lookup(prefix).has_value());
}

TEST_F(MemoizationTest, RawPointerOverloads) {
    uint8_t prefix[] = {0x01, 0x02, 0x03};
    HeuristicResult h = make_heuristic(5.0f, 0.8f);
    
    EXPECT_TRUE(cache->insert(prefix, 3, h, 0.5f, false));
    EXPECT_TRUE(cache->contains(prefix, 3));
    
    auto result = cache->lookup(prefix, 3);
    ASSERT_TRUE(result.has_value());
    EXPECT_FLOAT_EQ(result->score, 0.5f);
    
    EXPECT_TRUE(cache->remove(prefix, 3));
    EXPECT_FALSE(cache->contains(prefix, 3));
}

TEST_F(MemoizationTest, EmptyPrefix) {
    std::vector<uint8_t> empty_prefix;
    
    EXPECT_TRUE(cache->insert(empty_prefix, make_heuristic(5.0f, 0.8f), 0.5f, false));
    
    auto result = cache->lookup(empty_prefix);
    ASSERT_TRUE(result.has_value());
    EXPECT_FLOAT_EQ(result->score, 0.5f);
}

TEST_F(MemoizationTest, ConfigurableMaxSize) {
    MemoizationConfig small_config;
    small_config.max_entries = 3;
    PrefixCache small_cache(small_config);
    
    EXPECT_EQ(small_cache.get_config().max_entries, 3u);
}

// ============================================================================
// Task 10.2: LRU Eviction Policy Tests
// ============================================================================

TEST_F(MemoizationTest, LRUEvictionOnMaxEntries) {
    MemoizationConfig small_config;
    small_config.max_entries = 3;
    PrefixCache small_cache(small_config);
    
    // Insert 3 entries
    small_cache.insert({0x01}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    small_cache.insert({0x02}, make_heuristic(5.0f, 0.8f), 0.6f, false);
    small_cache.insert({0x03}, make_heuristic(5.0f, 0.8f), 0.7f, false);
    
    EXPECT_EQ(small_cache.size(), 3u);
    
    // Insert 4th entry - should evict LRU (0x01)
    small_cache.insert({0x04}, make_heuristic(5.0f, 0.8f), 0.8f, false);
    
    EXPECT_EQ(small_cache.size(), 3u);
    EXPECT_FALSE(small_cache.contains({0x01}));  // Evicted
    EXPECT_TRUE(small_cache.contains({0x02}));
    EXPECT_TRUE(small_cache.contains({0x03}));
    EXPECT_TRUE(small_cache.contains({0x04}));
}

TEST_F(MemoizationTest, LRUOrderUpdatedOnLookup) {
    MemoizationConfig small_config;
    small_config.max_entries = 3;
    PrefixCache small_cache(small_config);
    
    // Insert 3 entries
    small_cache.insert({0x01}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    small_cache.insert({0x02}, make_heuristic(5.0f, 0.8f), 0.6f, false);
    small_cache.insert({0x03}, make_heuristic(5.0f, 0.8f), 0.7f, false);
    
    // Access 0x01 to make it most recently used
    small_cache.lookup({0x01});
    
    // Insert 4th entry - should evict 0x02 (now LRU)
    small_cache.insert({0x04}, make_heuristic(5.0f, 0.8f), 0.8f, false);
    
    EXPECT_TRUE(small_cache.contains({0x01}));   // Recently accessed
    EXPECT_FALSE(small_cache.contains({0x02}));  // Evicted (was LRU)
    EXPECT_TRUE(small_cache.contains({0x03}));
    EXPECT_TRUE(small_cache.contains({0x04}));
}

TEST_F(MemoizationTest, LRUOrderUpdatedOnInsertUpdate) {
    MemoizationConfig small_config;
    small_config.max_entries = 3;
    PrefixCache small_cache(small_config);
    
    // Insert 3 entries
    small_cache.insert({0x01}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    small_cache.insert({0x02}, make_heuristic(5.0f, 0.8f), 0.6f, false);
    small_cache.insert({0x03}, make_heuristic(5.0f, 0.8f), 0.7f, false);
    
    // Update 0x01 to make it most recently used
    small_cache.insert({0x01}, make_heuristic(6.0f, 0.9f), 0.9f, false);
    
    // Insert 4th entry - should evict 0x02 (now LRU)
    small_cache.insert({0x04}, make_heuristic(5.0f, 0.8f), 0.8f, false);
    
    EXPECT_TRUE(small_cache.contains({0x01}));   // Recently updated
    EXPECT_FALSE(small_cache.contains({0x02}));  // Evicted (was LRU)
    EXPECT_TRUE(small_cache.contains({0x03}));
    EXPECT_TRUE(small_cache.contains({0x04}));
}

TEST_F(MemoizationTest, EvictionStatisticsTracked) {
    MemoizationConfig small_config;
    small_config.max_entries = 2;
    PrefixCache small_cache(small_config);
    
    small_cache.insert({0x01}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    small_cache.insert({0x02}, make_heuristic(5.0f, 0.8f), 0.6f, false);
    small_cache.insert({0x03}, make_heuristic(5.0f, 0.8f), 0.7f, false);  // Triggers eviction
    
    const auto& stats = small_cache.get_statistics();
    EXPECT_EQ(stats.evictions, 1u);
    EXPECT_EQ(stats.insertions, 3u);
}

TEST_F(MemoizationTest, MultipleEvictions) {
    MemoizationConfig small_config;
    small_config.max_entries = 2;
    PrefixCache small_cache(small_config);
    
    for (uint8_t i = 0; i < 10; ++i) {
        small_cache.insert({i}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    }
    
    EXPECT_EQ(small_cache.size(), 2u);
    
    const auto& stats = small_cache.get_statistics();
    EXPECT_EQ(stats.evictions, 8u);  // 10 inserts - 2 capacity = 8 evictions
}

// ============================================================================
// Task 10.3: Cache Hit Rate Tracking Tests
// ============================================================================

TEST_F(MemoizationTest, HitRateTracking) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    // 3 hits
    cache->lookup(prefix);
    cache->lookup(prefix);
    cache->lookup(prefix);
    
    // 2 misses
    cache->lookup({0x99});
    cache->lookup({0x88});
    
    const auto& stats = cache->get_statistics();
    EXPECT_EQ(stats.hits, 3u);
    EXPECT_EQ(stats.misses, 2u);
    
    // Hit rate = 3 / 5 = 0.6
    EXPECT_FLOAT_EQ(cache->hit_rate(), 0.6f);
}

TEST_F(MemoizationTest, HitRateZeroAccesses) {
    EXPECT_FLOAT_EQ(cache->hit_rate(), 0.0f);
}

TEST_F(MemoizationTest, HitRateAllHits) {
    std::vector<uint8_t> prefix = {0x01};
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    cache->lookup(prefix);
    cache->lookup(prefix);
    cache->lookup(prefix);
    
    EXPECT_FLOAT_EQ(cache->hit_rate(), 1.0f);
}

TEST_F(MemoizationTest, HitRateAllMisses) {
    cache->lookup({0x01});
    cache->lookup({0x02});
    cache->lookup({0x03});
    
    EXPECT_FLOAT_EQ(cache->hit_rate(), 0.0f);
}

TEST_F(MemoizationTest, StatisticsReset) {
    std::vector<uint8_t> prefix = {0x01};
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    cache->lookup(prefix);
    cache->lookup({0x99});  // Miss
    
    const auto& stats_before = cache->get_statistics();
    EXPECT_EQ(stats_before.hits, 1u);
    EXPECT_EQ(stats_before.misses, 1u);
    
    cache->reset_statistics();
    
    const auto& stats_after = cache->get_statistics();
    EXPECT_EQ(stats_after.hits, 0u);
    EXPECT_EQ(stats_after.misses, 0u);
    
    // Cache contents should still be there
    EXPECT_TRUE(cache->contains(prefix));
}

TEST_F(MemoizationTest, InsertionStatistics) {
    cache->insert({0x01}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    cache->insert({0x02}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    cache->insert({0x03}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    const auto& stats = cache->get_statistics();
    EXPECT_EQ(stats.insertions, 3u);
    EXPECT_EQ(stats.current_entries, 3u);
}

TEST_F(MemoizationTest, SizeBytesTracking) {
    cache->insert({0x01, 0x02, 0x03}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    EXPECT_GT(cache->size_bytes(), 0u);
    
    size_t size_after_one = cache->size_bytes();
    
    cache->insert({0x04, 0x05, 0x06}, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    EXPECT_GT(cache->size_bytes(), size_after_one);
}

TEST_F(MemoizationTest, AccessCountTracking) {
    std::vector<uint8_t> prefix = {0x01, 0x02};
    cache->insert(prefix, make_heuristic(5.0f, 0.8f), 0.5f, false);
    
    auto r1 = cache->lookup(prefix);
    ASSERT_TRUE(r1.has_value());
    EXPECT_EQ(r1->access_count, 2u);  // 1 from insert + 1 from lookup
    
    auto r2 = cache->lookup(prefix);
    ASSERT_TRUE(r2.has_value());
    EXPECT_EQ(r2->access_count, 3u);  // +1 from second lookup
}

TEST_F(MemoizationTest, DisabledCacheMissesTracked) {
    MemoizationConfig disabled_config;
    disabled_config.enabled = false;
    PrefixCache disabled_cache(disabled_config);
    
    disabled_cache.lookup({0x01});
    disabled_cache.lookup({0x02});
    
    const auto& stats = disabled_cache.get_statistics();
    EXPECT_EQ(stats.misses, 2u);
    EXPECT_EQ(stats.hits, 0u);
}

// ============================================================================
// Cache Consistency Tests (Property 10)
// ============================================================================

TEST_F(MemoizationTest, CacheConsistency) {
    // Property 10: Cache Consistency
    // For any prefix P evaluated twice (with no intervening eviction),
    // the cached result must be identical to the original evaluation result.
    
    std::vector<uint8_t> prefix = {0xAB, 0xCD, 0xEF};
    HeuristicResult h = make_heuristic(5.5f, 0.75f);
    
    cache->insert(prefix, h, 0.85f, false);
    
    auto r1 = cache->lookup(prefix);
    auto r2 = cache->lookup(prefix);
    
    ASSERT_TRUE(r1.has_value());
    ASSERT_TRUE(r2.has_value());
    
    // Results should be identical
    EXPECT_FLOAT_EQ(r1->score, r2->score);
    EXPECT_EQ(r1->should_prune, r2->should_prune);
    EXPECT_FLOAT_EQ(r1->heuristics.entropy, r2->heuristics.entropy);
    EXPECT_FLOAT_EQ(r1->heuristics.printable_ratio, r2->heuristics.printable_ratio);
}

TEST_F(MemoizationTest, CacheConsistencyMultiplePrefixes) {
    std::vector<std::vector<uint8_t>> prefixes = {
        {0x01, 0x02},
        {0x03, 0x04},
        {0x05, 0x06}
    };
    
    // Insert all
    for (size_t i = 0; i < prefixes.size(); ++i) {
        cache->insert(prefixes[i], make_heuristic(5.0f + i, 0.8f), 0.5f + i * 0.1f, false);
    }
    
    // Verify consistency for each
    for (size_t i = 0; i < prefixes.size(); ++i) {
        auto r1 = cache->lookup(prefixes[i]);
        auto r2 = cache->lookup(prefixes[i]);
        
        ASSERT_TRUE(r1.has_value());
        ASSERT_TRUE(r2.has_value());
        EXPECT_FLOAT_EQ(r1->score, r2->score);
    }
}

