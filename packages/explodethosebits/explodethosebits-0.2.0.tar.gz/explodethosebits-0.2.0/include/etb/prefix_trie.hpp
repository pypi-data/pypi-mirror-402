#ifndef ETB_PREFIX_TRIE_HPP
#define ETB_PREFIX_TRIE_HPP

#include <cstdint>
#include <cstddef>
#include <vector>
#include <atomic>
#include <mutex>

namespace etb {

/**
 * Status of a prefix trie node.
 */
enum class PrefixStatus : uint8_t {
    UNKNOWN = 0,    // Not yet evaluated
    VALID = 1,      // Prefix passed heuristics, continue exploring
    PRUNED = 2      // Prefix failed heuristics, eliminate all children
};

/**
 * Prefix trie node with flat array layout for GPU compatibility.
 * Each node represents a reconstructed byte value at a specific depth.
 */
struct PrefixTrieNode {
    uint8_t reconstructed_byte;     // Byte value at this node
    PrefixStatus status;            // UNKNOWN, VALID, or PRUNED
    float best_score;               // Best heuristic score seen at this prefix
    uint32_t children_offset;       // Offset to children array (256 children max per byte value)
    uint32_t visit_count;           // For adaptive threshold adjustment
    uint32_t parent_index;          // Index of parent node (0 for root)

    PrefixTrieNode()
        : reconstructed_byte(0)
        , status(PrefixStatus::UNKNOWN)
        , best_score(0.0f)
        , children_offset(0)
        , visit_count(0)
        , parent_index(0) {}

    PrefixTrieNode(uint8_t byte_val, uint32_t parent)
        : reconstructed_byte(byte_val)
        , status(PrefixStatus::UNKNOWN)
        , best_score(0.0f)
        , children_offset(0)
        , visit_count(0)
        , parent_index(parent) {}
};

/**
 * Configuration for the prefix trie.
 */
struct PrefixTrieConfig {
    uint32_t max_depth;             // Maximum depth of the trie (default: 16)
    uint32_t initial_capacity;      // Initial node capacity (default: 4096)
    float prune_threshold;          // Score threshold below which to prune (default: 0.3)
    uint32_t branch_prune_count;    // Number of failed branches to trigger level prune (default: 6)

    PrefixTrieConfig()
        : max_depth(16)
        , initial_capacity(4096)
        , prune_threshold(0.3f)
        , branch_prune_count(6) {}
};

/**
 * Statistics for prefix trie operations.
 */
struct PrefixTrieStats {
    uint64_t total_lookups;
    uint64_t cache_hits;
    uint64_t nodes_created;
    uint64_t nodes_pruned;
    uint64_t children_eliminated;
    std::vector<uint32_t> valid_branches_per_level;
    std::vector<uint32_t> pruned_branches_per_level;

    PrefixTrieStats() 
        : total_lookups(0)
        , cache_hits(0)
        , nodes_created(0)
        , nodes_pruned(0)
        , children_eliminated(0) {}

    void reset() {
        total_lookups = 0;
        cache_hits = 0;
        nodes_created = 0;
        nodes_pruned = 0;
        children_eliminated = 0;
        valid_branches_per_level.clear();
        pruned_branches_per_level.clear();
    }
};


/**
 * Prefix Trie - GPU-compatible trie for O(1) prefix lookup and pruning.
 * 
 * Uses a flat array layout with breadth-first ordering for coalesced
 * memory access patterns on GPU. Supports atomic status updates for
 * concurrent access.
 * 
 * Requirements: 5.5 - Trie-based prefix tracking for O(1) prefix lookup
 */
class PrefixTrie {
public:
    /**
     * Construct with default configuration.
     */
    PrefixTrie();

    /**
     * Construct with custom configuration.
     * @param config Trie configuration
     */
    explicit PrefixTrie(const PrefixTrieConfig& config);

    /**
     * Look up a prefix in the trie.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @return Pointer to the node if found, nullptr if not found
     */
    const PrefixTrieNode* lookup(const uint8_t* prefix, size_t length) const;

    /**
     * Look up a prefix in the trie (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @return Pointer to the node if found, nullptr if not found
     */
    const PrefixTrieNode* lookup(const std::vector<uint8_t>& prefix) const;

    /**
     * Insert or update a prefix in the trie.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @param status Status to set for the node
     * @param score Heuristic score for the prefix
     * @return Index of the inserted/updated node
     */
    uint32_t insert(const uint8_t* prefix, size_t length, 
                    PrefixStatus status, float score);

    /**
     * Insert or update a prefix in the trie (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @param status Status to set for the node
     * @param score Heuristic score for the prefix
     * @return Index of the inserted/updated node
     */
    uint32_t insert(const std::vector<uint8_t>& prefix,
                    PrefixStatus status, float score);

    /**
     * Update the status of an existing node atomically.
     * @param node_index Index of the node to update
     * @param status New status
     * @return true if update succeeded, false if node doesn't exist
     */
    bool update_status(uint32_t node_index, PrefixStatus status);

    /**
     * Update the best score of an existing node.
     * @param node_index Index of the node to update
     * @param score New score (only updates if higher than current)
     * @return true if update succeeded
     */
    bool update_score(uint32_t node_index, float score);

    /**
     * Mark a prefix as pruned and eliminate all children.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @return Number of children eliminated
     */
    uint64_t prune(const uint8_t* prefix, size_t length);

    /**
     * Mark a prefix as pruned and eliminate all children (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @return Number of children eliminated
     */
    uint64_t prune(const std::vector<uint8_t>& prefix);

    /**
     * Check if a prefix or any of its ancestors is pruned.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @return true if the prefix should be skipped due to pruning
     */
    bool is_pruned(const uint8_t* prefix, size_t length) const;

    /**
     * Check if a prefix or any of its ancestors is pruned (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @return true if the prefix should be skipped due to pruning
     */
    bool is_pruned(const std::vector<uint8_t>& prefix) const;

    /**
     * Get the number of valid branches at a specific level.
     * @param level Depth level (0 = root children)
     * @return Number of valid (non-pruned) branches
     */
    uint32_t get_valid_branch_count(uint32_t level) const;

    /**
     * Get the number of pruned branches at a specific level.
     * @param level Depth level (0 = root children)
     * @return Number of pruned branches
     */
    uint32_t get_pruned_branch_count(uint32_t level) const;

    /**
     * Calculate the effective branching factor.
     * @return Average number of valid branches per level
     */
    float get_effective_branching_factor() const;

    /**
     * Get the total number of nodes in the trie.
     */
    size_t node_count() const { return nodes_.size(); }

    /**
     * Get the maximum depth of the trie.
     */
    uint32_t max_depth() const { return config_.max_depth; }

    /**
     * Get the configuration.
     */
    const PrefixTrieConfig& get_config() const { return config_; }

    /**
     * Get statistics about trie operations.
     */
    const PrefixTrieStats& get_statistics() const { return stats_; }

    /**
     * Reset statistics.
     */
    void reset_statistics();

    /**
     * Clear all nodes and reset the trie.
     */
    void clear();

    /**
     * Get read-only access to the underlying node array.
     * Useful for GPU memory transfer.
     */
    const std::vector<PrefixTrieNode>& nodes() const { return nodes_; }

    /**
     * Get a node by index.
     * @param index Node index
     * @return Pointer to node or nullptr if invalid index
     */
    const PrefixTrieNode* get_node(uint32_t index) const;

    /**
     * Check if a level should trigger aggressive pruning based on failure rate.
     * When branch_prune_count (default 6) out of 8 branches fail at a level,
     * this returns true to indicate the level should be more aggressively pruned.
     * @param level Depth level to check
     * @return true if pruning threshold exceeded at this level
     */
    bool should_prune_level(uint32_t level) const;

    /**
     * Evaluate a prefix and automatically prune if score is below threshold.
     * @param prefix Byte sequence representing the prefix
     * @param length Length of the prefix
     * @param score Heuristic score for the prefix
     * @return true if prefix was pruned, false if it remains valid
     */
    bool evaluate_and_prune(const uint8_t* prefix, size_t length, float score);

    /**
     * Evaluate a prefix and automatically prune if score is below threshold (vector overload).
     * @param prefix Byte sequence representing the prefix
     * @param score Heuristic score for the prefix
     * @return true if prefix was pruned, false if it remains valid
     */
    bool evaluate_and_prune(const std::vector<uint8_t>& prefix, float score);

    /**
     * Get the total number of branches (valid + pruned) at a level.
     * @param level Depth level
     * @return Total branch count
     */
    uint32_t get_total_branch_count(uint32_t level) const;

private:
    PrefixTrieConfig config_;
    std::vector<PrefixTrieNode> nodes_;
    mutable PrefixTrieStats stats_;
    mutable std::mutex mutex_;  // For thread-safe operations

    // Root node is at index 0, children start at index 1
    static constexpr uint32_t ROOT_INDEX = 0;
    static constexpr uint32_t INVALID_INDEX = UINT32_MAX;
    static constexpr uint32_t CHILDREN_PER_NODE = 256;  // One for each byte value

    /**
     * Find or create a child node for a given byte value.
     * @param parent_index Index of the parent node
     * @param byte_value Byte value for the child
     * @return Index of the child node
     */
    uint32_t find_or_create_child(uint32_t parent_index, uint8_t byte_value);

    /**
     * Get the child index for a given parent and byte value.
     * @param parent_index Index of the parent node
     * @param byte_value Byte value for the child
     * @return Index of the child node or INVALID_INDEX if not found
     */
    uint32_t get_child_index(uint32_t parent_index, uint8_t byte_value) const;

    /**
     * Recursively mark all descendants as pruned.
     * @param node_index Index of the node whose children to prune
     * @return Number of nodes pruned
     */
    uint64_t prune_descendants(uint32_t node_index);

    /**
     * Ensure branch tracking vectors are sized for the given level.
     */
    void ensure_level_tracking(uint32_t level);
};

} // namespace etb

#endif // ETB_PREFIX_TRIE_HPP
