#include "etb/prefix_trie.hpp"
#include <algorithm>
#include <stdexcept>
#include <cstring>

namespace etb {

// ============================================================================
// PrefixTrie Implementation
// ============================================================================

PrefixTrie::PrefixTrie() : PrefixTrie(PrefixTrieConfig()) {}

PrefixTrie::PrefixTrie(const PrefixTrieConfig& config)
    : config_(config) {
    nodes_.reserve(config_.initial_capacity);
    // Create root node
    nodes_.emplace_back();
    nodes_[ROOT_INDEX].status = PrefixStatus::VALID;
}

const PrefixTrieNode* PrefixTrie::lookup(const uint8_t* prefix, size_t length) const {
    std::lock_guard<std::mutex> lock(mutex_);
    stats_.total_lookups++;

    if (length == 0) {
        return &nodes_[ROOT_INDEX];
    }

    if (length > config_.max_depth) {
        return nullptr;
    }

    uint32_t current = ROOT_INDEX;
    for (size_t i = 0; i < length; ++i) {
        uint32_t child = get_child_index(current, prefix[i]);
        if (child == INVALID_INDEX) {
            return nullptr;
        }
        current = child;
    }

    stats_.cache_hits++;
    return &nodes_[current];
}

const PrefixTrieNode* PrefixTrie::lookup(const std::vector<uint8_t>& prefix) const {
    return lookup(prefix.data(), prefix.size());
}

uint32_t PrefixTrie::insert(const uint8_t* prefix, size_t length,
                            PrefixStatus status, float score) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (length == 0) {
        nodes_[ROOT_INDEX].status = status;
        nodes_[ROOT_INDEX].best_score = std::max(nodes_[ROOT_INDEX].best_score, score);
        nodes_[ROOT_INDEX].visit_count++;
        return ROOT_INDEX;
    }

    if (length > config_.max_depth) {
        return INVALID_INDEX;
    }

    uint32_t current = ROOT_INDEX;
    for (size_t i = 0; i < length; ++i) {
        current = find_or_create_child(current, prefix[i]);
        
        // Track branch counts at each level
        ensure_level_tracking(static_cast<uint32_t>(i));
    }

    // Update the final node
    PrefixTrieNode& node = nodes_[current];
    
    // Track status changes for branch counting
    PrefixStatus old_status = node.status;
    node.status = status;
    node.best_score = std::max(node.best_score, score);
    node.visit_count++;

    // Update branch tracking
    uint32_t level = static_cast<uint32_t>(length - 1);
    ensure_level_tracking(level);
    
    if (old_status == PrefixStatus::UNKNOWN) {
        if (status == PrefixStatus::VALID) {
            stats_.valid_branches_per_level[level]++;
        } else if (status == PrefixStatus::PRUNED) {
            stats_.pruned_branches_per_level[level]++;
            stats_.nodes_pruned++;
        }
    } else if (old_status == PrefixStatus::VALID && status == PrefixStatus::PRUNED) {
        stats_.valid_branches_per_level[level]--;
        stats_.pruned_branches_per_level[level]++;
        stats_.nodes_pruned++;
    }

    return current;
}

uint32_t PrefixTrie::insert(const std::vector<uint8_t>& prefix,
                            PrefixStatus status, float score) {
    return insert(prefix.data(), prefix.size(), status, score);
}


bool PrefixTrie::update_status(uint32_t node_index, PrefixStatus status) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (node_index >= nodes_.size()) {
        return false;
    }

    PrefixTrieNode& node = nodes_[node_index];
    PrefixStatus old_status = node.status;
    node.status = status;

    // Update statistics if transitioning to PRUNED
    if (old_status != PrefixStatus::PRUNED && status == PrefixStatus::PRUNED) {
        stats_.nodes_pruned++;
    }

    return true;
}

bool PrefixTrie::update_score(uint32_t node_index, float score) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (node_index >= nodes_.size()) {
        return false;
    }

    PrefixTrieNode& node = nodes_[node_index];
    if (score > node.best_score) {
        node.best_score = score;
    }

    return true;
}

uint64_t PrefixTrie::prune(const uint8_t* prefix, size_t length) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (length == 0 || length > config_.max_depth) {
        return 0;
    }

    // Find the node for this prefix
    uint32_t current = ROOT_INDEX;
    for (size_t i = 0; i < length; ++i) {
        uint32_t child = get_child_index(current, prefix[i]);
        if (child == INVALID_INDEX) {
            return 0;  // Prefix doesn't exist
        }
        current = child;
    }

    // Mark this node as pruned
    PrefixTrieNode& node = nodes_[current];
    if (node.status == PrefixStatus::PRUNED) {
        return 0;  // Already pruned
    }

    node.status = PrefixStatus::PRUNED;
    stats_.nodes_pruned++;

    // Update branch tracking
    uint32_t level = static_cast<uint32_t>(length - 1);
    ensure_level_tracking(level);
    if (stats_.valid_branches_per_level[level] > 0) {
        stats_.valid_branches_per_level[level]--;
    }
    stats_.pruned_branches_per_level[level]++;

    // Recursively prune all descendants
    return prune_descendants(current);
}

uint64_t PrefixTrie::prune(const std::vector<uint8_t>& prefix) {
    return prune(prefix.data(), prefix.size());
}

bool PrefixTrie::is_pruned(const uint8_t* prefix, size_t length) const {
    std::lock_guard<std::mutex> lock(mutex_);

    if (length == 0) {
        return nodes_[ROOT_INDEX].status == PrefixStatus::PRUNED;
    }

    uint32_t current = ROOT_INDEX;
    for (size_t i = 0; i < length; ++i) {
        // Check if current node is pruned (ancestor pruning)
        if (nodes_[current].status == PrefixStatus::PRUNED) {
            return true;
        }

        uint32_t child = get_child_index(current, prefix[i]);
        if (child == INVALID_INDEX) {
            return false;  // Node doesn't exist, not pruned
        }
        current = child;
    }

    return nodes_[current].status == PrefixStatus::PRUNED;
}

bool PrefixTrie::is_pruned(const std::vector<uint8_t>& prefix) const {
    return is_pruned(prefix.data(), prefix.size());
}

uint32_t PrefixTrie::get_valid_branch_count(uint32_t level) const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (level >= stats_.valid_branches_per_level.size()) {
        return 0;
    }
    return stats_.valid_branches_per_level[level];
}

uint32_t PrefixTrie::get_pruned_branch_count(uint32_t level) const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (level >= stats_.pruned_branches_per_level.size()) {
        return 0;
    }
    return stats_.pruned_branches_per_level[level];
}

float PrefixTrie::get_effective_branching_factor() const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (stats_.valid_branches_per_level.empty()) {
        return 0.0f;
    }

    float total_valid = 0.0f;
    uint32_t levels_with_data = 0;

    for (size_t i = 0; i < stats_.valid_branches_per_level.size(); ++i) {
        uint32_t valid = stats_.valid_branches_per_level[i];
        uint32_t pruned = (i < stats_.pruned_branches_per_level.size()) 
                          ? stats_.pruned_branches_per_level[i] : 0;
        uint32_t total = valid + pruned;
        
        if (total > 0) {
            total_valid += static_cast<float>(valid);
            levels_with_data++;
        }
    }

    if (levels_with_data == 0) {
        return 0.0f;
    }

    return total_valid / static_cast<float>(levels_with_data);
}

void PrefixTrie::reset_statistics() {
    std::lock_guard<std::mutex> lock(mutex_);
    stats_.reset();
}

void PrefixTrie::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    nodes_.clear();
    nodes_.reserve(config_.initial_capacity);
    // Recreate root node
    nodes_.emplace_back();
    nodes_[ROOT_INDEX].status = PrefixStatus::VALID;
    stats_.reset();
}

const PrefixTrieNode* PrefixTrie::get_node(uint32_t index) const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (index >= nodes_.size()) {
        return nullptr;
    }
    return &nodes_[index];
}

bool PrefixTrie::should_prune_level(uint32_t level) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (level >= stats_.pruned_branches_per_level.size()) {
        return false;
    }

    uint32_t pruned = stats_.pruned_branches_per_level[level];
    uint32_t valid = (level < stats_.valid_branches_per_level.size()) 
                     ? stats_.valid_branches_per_level[level] : 0;
    uint32_t total = pruned + valid;

    if (total == 0) {
        return false;
    }

    // If pruned count exceeds threshold (e.g., 6 out of 8), trigger aggressive pruning
    return pruned >= config_.branch_prune_count;
}

bool PrefixTrie::evaluate_and_prune(const uint8_t* prefix, size_t length, float score) {
    if (length == 0 || length > config_.max_depth) {
        return false;
    }

    // If score is below threshold, prune this prefix
    if (score < config_.prune_threshold) {
        insert(prefix, length, PrefixStatus::PRUNED, score);
        prune(prefix, length);
        return true;
    }

    // Score is acceptable, mark as valid
    insert(prefix, length, PrefixStatus::VALID, score);
    return false;
}

bool PrefixTrie::evaluate_and_prune(const std::vector<uint8_t>& prefix, float score) {
    return evaluate_and_prune(prefix.data(), prefix.size(), score);
}

uint32_t PrefixTrie::get_total_branch_count(uint32_t level) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    uint32_t valid = (level < stats_.valid_branches_per_level.size()) 
                     ? stats_.valid_branches_per_level[level] : 0;
    uint32_t pruned = (level < stats_.pruned_branches_per_level.size()) 
                      ? stats_.pruned_branches_per_level[level] : 0;
    
    return valid + pruned;
}


// ============================================================================
// Private Helper Methods
// ============================================================================

uint32_t PrefixTrie::find_or_create_child(uint32_t parent_index, uint8_t byte_value) {
    // First, check if child already exists
    uint32_t existing = get_child_index(parent_index, byte_value);
    if (existing != INVALID_INDEX) {
        return existing;
    }

    // Create new child node
    uint32_t new_index = static_cast<uint32_t>(nodes_.size());
    nodes_.emplace_back(byte_value, parent_index);
    stats_.nodes_created++;

    // Update parent's children_offset if this is the first child
    PrefixTrieNode& parent = nodes_[parent_index];
    if (parent.children_offset == 0) {
        parent.children_offset = new_index;
    }

    return new_index;
}

uint32_t PrefixTrie::get_child_index(uint32_t parent_index, uint8_t byte_value) const {
    if (parent_index >= nodes_.size()) {
        return INVALID_INDEX;
    }

    const PrefixTrieNode& parent = nodes_[parent_index];
    if (parent.children_offset == 0) {
        return INVALID_INDEX;  // No children
    }

    // Search through children (they are stored sequentially after children_offset)
    // Children are added dynamically, so we need to search
    for (uint32_t i = parent.children_offset; i < nodes_.size(); ++i) {
        const PrefixTrieNode& node = nodes_[i];
        if (node.parent_index != parent_index) {
            // Moved past this parent's children
            break;
        }
        if (node.reconstructed_byte == byte_value) {
            return i;
        }
    }

    return INVALID_INDEX;
}

uint64_t PrefixTrie::prune_descendants(uint32_t node_index) {
    uint64_t count = 0;

    // Find all children of this node and mark them as pruned
    for (uint32_t i = node_index + 1; i < nodes_.size(); ++i) {
        PrefixTrieNode& node = nodes_[i];
        
        // Check if this node is a descendant by tracing parent chain
        uint32_t current = i;
        bool is_descendant = false;
        
        while (current != ROOT_INDEX && current < nodes_.size()) {
            if (nodes_[current].parent_index == node_index) {
                is_descendant = true;
                break;
            }
            current = nodes_[current].parent_index;
        }

        if (is_descendant && node.status != PrefixStatus::PRUNED) {
            node.status = PrefixStatus::PRUNED;
            count++;
            stats_.children_eliminated++;
        }
    }

    return count;
}

void PrefixTrie::ensure_level_tracking(uint32_t level) {
    if (level >= stats_.valid_branches_per_level.size()) {
        stats_.valid_branches_per_level.resize(level + 1, 0);
    }
    if (level >= stats_.pruned_branches_per_level.size()) {
        stats_.pruned_branches_per_level.resize(level + 1, 0);
    }
}

} // namespace etb
