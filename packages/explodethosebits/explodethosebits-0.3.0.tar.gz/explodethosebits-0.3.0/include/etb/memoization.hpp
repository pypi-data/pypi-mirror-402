#ifndef ETB_MEMOIZATION_HPP
#define ETB_MEMOIZATION_HPP

#include <cstdint>
#include <cstddef>
#include <vector>
#include <unordered_map>
#include <list>
#include <mutex>
#include <optional>
#include "heuristics.hpp"

namespace etb {

/**
 * Result stored in the prefix cache.
 * Contains the evaluation result for a specific prefix.
 */
struct PrefixCacheEntry {
    std::vector<uint8_t> prefix;    // The prefix bytes
    HeuristicResult heuristics;     // Heuristic evaluation result
    float score;                    // Composite score
    bool should_prune;              // Whether this prefix should be pruned
    uint64_t access_count;          // Number of times accessed

    PrefixCacheEntry()
        : score(0.0f)
        , should_prune(false)
        , access_count(0) {}

    PrefixCacheEntry(const std::vector<uint8_t>& p, const HeuristicResult& h, 
                     float s, bool prune)
        : prefix(p)
        , heuristics(h)
        , score(s)
        , should_prune(prune)
        , access_count(1) {}
};

/**
 * Configuration for the memoization cache.
 */
struct MemoizationConfig {
    size_t max_size_bytes;          // Maximum cache size in bytes (default: 1GB)
    size_t max_entries;             // Maximum number of entries (default: 1M)
    bool enabled;                   // Whether caching is enabled

    MemoizationConfig()
        : max_size_bytes(1024 * 1024 * 1024)  // 1GB
        , max_entries(1000000)                 // 1M entries
        , enabled(true) {}
};

/**
 * Statistics for cache operations.
 */
struct MemoizationStats {
    uint64_t hits;                  // Number of cache hits
    uint64_t misses;                // Number of cache misses
    uint64_t insertions;            // Number of insertions
    uint64_t evictions;             // Number of evictions
    size_t current_entries;         // Current number of entries
    size_t current_size_bytes;      // Current estimated size in bytes

    MemoizationStats()
        : hits(0)
        , misses(0)
        , insertions(0)
        , evictions(0)
        , current_entries(0)
        , current_size_bytes(0) {}

    void reset() {
        hits = 0;
        misses = 0;
        insertions = 0;
        evictions = 0;
        // Don't reset current_entries and current_size_bytes
    }

    /**
     * Calculate cache hit rate.
     * @return Hit rate in range [0.0, 1.0], or 0.0 if no accesses
     */
    float hit_rate() const {
        uint64_t total = hits + misses;
        if (total == 0) return 0.0f;
        return static_cast<float>(hits) / static_cast<float>(total);
    }
};

/**
 * Prefix Result Cache with LRU Eviction
 * 
 * Stores evaluated prefix results for O(1) lookup on repeated evaluations.
 * Uses LRU (Least Recently Used) eviction policy when cache size exceeds limits.
 * 
 * Requirements: 6.1, 6.2, 6.4, 6.5
 */
class PrefixCache {
public:
    /**
     * Construct with default configuration.
     */
    PrefixCache();

    /**
     * Construct with custom configuration.
     * @param config Cache configuration
     */
    explicit PrefixCache(const MemoizationConfig& config);

    /**
     * Look up a prefix in the cache.
     * Updates LRU order on hit.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @return Optional containing the cached entry if found
     */
    std::optional<PrefixCacheEntry> lookup(const uint8_t* prefix, size_t length);

    /**
     * Look up a prefix in the cache (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @return Optional containing the cached entry if found
     */
    std::optional<PrefixCacheEntry> lookup(const std::vector<uint8_t>& prefix);

    /**
     * Insert or update a prefix result in the cache.
     * May trigger eviction if cache is full.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @param heuristics Heuristic evaluation result
     * @param score Composite score
     * @param should_prune Whether this prefix should be pruned
     * @return true if insertion succeeded
     */
    bool insert(const uint8_t* prefix, size_t length,
                const HeuristicResult& heuristics, float score, bool should_prune);

    /**
     * Insert or update a prefix result in the cache (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @param heuristics Heuristic evaluation result
     * @param score Composite score
     * @param should_prune Whether this prefix should be pruned
     * @return true if insertion succeeded
     */
    bool insert(const std::vector<uint8_t>& prefix,
                const HeuristicResult& heuristics, float score, bool should_prune);

    /**
     * Check if a prefix exists in the cache without updating LRU order.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @return true if prefix is cached
     */
    bool contains(const uint8_t* prefix, size_t length) const;

    /**
     * Check if a prefix exists in the cache (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @return true if prefix is cached
     */
    bool contains(const std::vector<uint8_t>& prefix) const;

    /**
     * Remove a specific prefix from the cache.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @return true if prefix was removed
     */
    bool remove(const uint8_t* prefix, size_t length);

    /**
     * Remove a specific prefix from the cache (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @return true if prefix was removed
     */
    bool remove(const std::vector<uint8_t>& prefix);

    /**
     * Clear all entries from the cache.
     */
    void clear();

    /**
     * Get the current number of entries in the cache.
     */
    size_t size() const;

    /**
     * Check if the cache is empty.
     */
    bool empty() const;

    /**
     * Get the estimated current size in bytes.
     */
    size_t size_bytes() const;

    /**
     * Get the configuration.
     */
    const MemoizationConfig& get_config() const { return config_; }

    /**
     * Get cache statistics.
     */
    const MemoizationStats& get_statistics() const { return stats_; }

    /**
     * Reset statistics (but keep cache contents).
     */
    void reset_statistics();

    /**
     * Enable or disable the cache.
     * @param enabled Whether to enable caching
     */
    void set_enabled(bool enabled);

    /**
     * Check if caching is enabled.
     */
    bool is_enabled() const { return config_.enabled; }

    /**
     * Get the cache hit rate.
     * @return Hit rate in range [0.0, 1.0]
     */
    float hit_rate() const { return stats_.hit_rate(); }

private:
    /**
     * Hash function for prefix vectors.
     */
    struct PrefixHasher {
        size_t operator()(const std::vector<uint8_t>& prefix) const {
            size_t hash = 0;
            for (uint8_t byte : prefix) {
                hash ^= std::hash<uint8_t>{}(byte) + 0x9e3779b9 + (hash << 6) + (hash >> 2);
            }
            return hash;
        }
    };

    MemoizationConfig config_;
    mutable MemoizationStats stats_;
    mutable std::mutex mutex_;

    // LRU list: front = most recently used, back = least recently used
    std::list<std::vector<uint8_t>> lru_list_;
    
    // Map from prefix to (entry, iterator into lru_list)
    using LRUIterator = std::list<std::vector<uint8_t>>::iterator;
    std::unordered_map<std::vector<uint8_t>, 
                       std::pair<PrefixCacheEntry, LRUIterator>,
                       PrefixHasher> cache_;

    /**
     * Estimate the size of an entry in bytes.
     */
    static size_t estimate_entry_size(const PrefixCacheEntry& entry);

    /**
     * Evict least recently used entries until under limits.
     */
    void evict_if_needed();

    /**
     * Move a prefix to the front of the LRU list.
     */
    void touch(const std::vector<uint8_t>& prefix);

    /**
     * Convert raw pointer + length to vector for internal use.
     */
    static std::vector<uint8_t> to_vector(const uint8_t* data, size_t length);
};

} // namespace etb

#endif // ETB_MEMOIZATION_HPP
