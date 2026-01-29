#include "etb/memoization.hpp"
#include <algorithm>

namespace etb {

// ============================================================================
// PrefixCache Implementation
// ============================================================================

PrefixCache::PrefixCache()
    : config_()
    , stats_()
    , cache_() {}

PrefixCache::PrefixCache(const MemoizationConfig& config)
    : config_(config)
    , stats_()
    , cache_() {}

std::optional<PrefixCacheEntry> PrefixCache::lookup(const uint8_t* prefix, size_t length) {
    return lookup(to_vector(prefix, length));
}

std::optional<PrefixCacheEntry> PrefixCache::lookup(const std::vector<uint8_t>& prefix) {
    if (!config_.enabled) {
        stats_.misses++;
        return std::nullopt;
    }

    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = cache_.find(prefix);
    if (it == cache_.end()) {
        stats_.misses++;
        return std::nullopt;
    }

    // Cache hit - update LRU order
    stats_.hits++;
    it->second.first.access_count++;
    
    // Move to front of LRU list
    lru_list_.erase(it->second.second);
    lru_list_.push_front(prefix);
    it->second.second = lru_list_.begin();

    return it->second.first;
}

bool PrefixCache::insert(const uint8_t* prefix, size_t length,
                         const HeuristicResult& heuristics, float score, bool should_prune) {
    return insert(to_vector(prefix, length), heuristics, score, should_prune);
}

bool PrefixCache::insert(const std::vector<uint8_t>& prefix,
                         const HeuristicResult& heuristics, float score, bool should_prune) {
    if (!config_.enabled) {
        return false;
    }

    std::lock_guard<std::mutex> lock(mutex_);

    // Check if already exists - update if so
    auto it = cache_.find(prefix);
    if (it != cache_.end()) {
        // Update existing entry
        it->second.first.heuristics = heuristics;
        it->second.first.score = score;
        it->second.first.should_prune = should_prune;
        it->second.first.access_count++;
        
        // Move to front of LRU list
        lru_list_.erase(it->second.second);
        lru_list_.push_front(prefix);
        it->second.second = lru_list_.begin();
        
        return true;
    }

    // Create new entry
    PrefixCacheEntry entry(prefix, heuristics, score, should_prune);
    size_t entry_size = estimate_entry_size(entry);

    // Check if we need to evict
    while ((stats_.current_entries >= config_.max_entries ||
            stats_.current_size_bytes + entry_size > config_.max_size_bytes) &&
           !cache_.empty()) {
        // Evict LRU entry
        const auto& lru_key = lru_list_.back();
        auto cache_it = cache_.find(lru_key);
        if (cache_it != cache_.end()) {
            stats_.current_size_bytes -= estimate_entry_size(cache_it->second.first);
            cache_.erase(cache_it);
            stats_.current_entries--;
            stats_.evictions++;
        }
        lru_list_.pop_back();
    }

    // Insert new entry
    lru_list_.push_front(prefix);
    cache_[prefix] = std::make_pair(entry, lru_list_.begin());
    stats_.current_entries++;
    stats_.current_size_bytes += entry_size;
    stats_.insertions++;

    return true;
}

bool PrefixCache::contains(const uint8_t* prefix, size_t length) const {
    return contains(to_vector(prefix, length));
}

bool PrefixCache::contains(const std::vector<uint8_t>& prefix) const {
    if (!config_.enabled) {
        return false;
    }

    std::lock_guard<std::mutex> lock(mutex_);
    return cache_.find(prefix) != cache_.end();
}

bool PrefixCache::remove(const uint8_t* prefix, size_t length) {
    return remove(to_vector(prefix, length));
}

bool PrefixCache::remove(const std::vector<uint8_t>& prefix) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = cache_.find(prefix);
    if (it == cache_.end()) {
        return false;
    }

    stats_.current_size_bytes -= estimate_entry_size(it->second.first);
    lru_list_.erase(it->second.second);
    cache_.erase(it);
    stats_.current_entries--;

    return true;
}

void PrefixCache::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    cache_.clear();
    lru_list_.clear();
    stats_.current_entries = 0;
    stats_.current_size_bytes = 0;
}

size_t PrefixCache::size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return cache_.size();
}

bool PrefixCache::empty() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return cache_.empty();
}

size_t PrefixCache::size_bytes() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return stats_.current_size_bytes;
}

void PrefixCache::reset_statistics() {
    std::lock_guard<std::mutex> lock(mutex_);
    stats_.reset();
}

void PrefixCache::set_enabled(bool enabled) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.enabled = enabled;
}

size_t PrefixCache::estimate_entry_size(const PrefixCacheEntry& entry) {
    // Estimate: prefix bytes + HeuristicResult + overhead
    return entry.prefix.size() + sizeof(HeuristicResult) + sizeof(PrefixCacheEntry) + 64;
}

void PrefixCache::evict_if_needed() {
    // Called with lock held
    while ((stats_.current_entries >= config_.max_entries ||
            stats_.current_size_bytes > config_.max_size_bytes) &&
           !cache_.empty()) {
        const auto& lru_key = lru_list_.back();
        auto it = cache_.find(lru_key);
        if (it != cache_.end()) {
            stats_.current_size_bytes -= estimate_entry_size(it->second.first);
            cache_.erase(it);
            stats_.current_entries--;
            stats_.evictions++;
        }
        lru_list_.pop_back();
    }
}

void PrefixCache::touch(const std::vector<uint8_t>& prefix) {
    // Called with lock held
    auto it = cache_.find(prefix);
    if (it != cache_.end()) {
        lru_list_.erase(it->second.second);
        lru_list_.push_front(prefix);
        it->second.second = lru_list_.begin();
    }
}

std::vector<uint8_t> PrefixCache::to_vector(const uint8_t* data, size_t length) {
    if (data == nullptr || length == 0) {
        return {};
    }
    return std::vector<uint8_t>(data, data + length);
}

} // namespace etb
