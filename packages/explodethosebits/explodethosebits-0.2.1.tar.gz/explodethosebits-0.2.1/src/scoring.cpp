#include "etb/scoring.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace etb {

// ============================================================================
// ScoringWeights Implementation
// ============================================================================

bool ScoringWeights::is_valid() const {
    float sum = signature_weight + heuristic_weight + length_weight + structure_weight;
    return std::abs(sum - 1.0f) < 0.01f;  // Allow small tolerance
}

void ScoringWeights::normalize() {
    float sum = signature_weight + heuristic_weight + length_weight + structure_weight;
    if (sum > 0.0f) {
        signature_weight /= sum;
        heuristic_weight /= sum;
        length_weight /= sum;
        structure_weight /= sum;
    }
}

// ============================================================================
// ScoreCalculator Implementation
// ============================================================================

ScoreCalculator::ScoreCalculator() : weights_() {}

ScoreCalculator::ScoreCalculator(const ScoringWeights& weights) : weights_(weights) {}

void ScoreCalculator::set_weights(const ScoringWeights& weights) {
    weights_ = weights;
}

float ScoreCalculator::calculate(float signature_score, float heuristic_score,
                                  float length_score, float structure_score) const {
    // Clamp all inputs to [0.0, 1.0]
    signature_score = std::max(0.0f, std::min(1.0f, signature_score));
    heuristic_score = std::max(0.0f, std::min(1.0f, heuristic_score));
    length_score = std::max(0.0f, std::min(1.0f, length_score));
    structure_score = std::max(0.0f, std::min(1.0f, structure_score));

    // Calculate weighted sum
    float composite = signature_score * weights_.signature_weight +
                      heuristic_score * weights_.heuristic_weight +
                      length_score * weights_.length_weight +
                      structure_score * weights_.structure_weight;

    // Clamp result to [0.0, 1.0]
    return std::max(0.0f, std::min(1.0f, composite));
}

float ScoreCalculator::calculate(const SignatureMatch& sig_match,
                                  const HeuristicResult& heuristics,
                                  size_t data_length,
                                  size_t expected_length,
                                  const StructuralValidation& structure) const {
    // Extract signature score from match confidence
    float signature_score = sig_match.matched ? sig_match.confidence : 0.0f;

    // Use heuristic composite score
    float heuristic_score = heuristics.composite_score;

    // Calculate length score
    float length_score = calculate_length_score(data_length, expected_length);

    // Use structural validity score
    float structure_score = structure.validity_score;

    return calculate(signature_score, heuristic_score, length_score, structure_score);
}

void ScoreCalculator::score_candidate(Candidate& candidate, size_t expected_length) const {
    candidate.composite_score = calculate(
        candidate.signature_match,
        candidate.heuristics,
        candidate.data.size(),
        expected_length,
        candidate.structure
    );
    
    // Also update confidence based on composite score
    candidate.confidence = candidate.composite_score;
}

float ScoreCalculator::calculate_length_score(size_t actual_length, size_t expected_length) {
    if (expected_length == 0) {
        // No expected length - give neutral score based on having some data
        if (actual_length == 0) return 0.0f;
        if (actual_length < 4) return 0.3f;
        if (actual_length < 16) return 0.5f;
        return 0.7f;  // Longer data gets higher base score
    }

    // Calculate ratio of actual to expected
    float ratio = static_cast<float>(actual_length) / static_cast<float>(expected_length);

    if (ratio >= 1.0f) {
        // At or above expected length - perfect or slight penalty for excess
        if (ratio <= 1.1f) return 1.0f;  // Within 10% over
        if (ratio <= 1.5f) return 0.8f;  // Within 50% over
        return 0.5f;  // Significantly over
    } else {
        // Below expected length - score based on completeness
        return ratio;  // Linear scaling from 0 to 1
    }
}

// ============================================================================
// CandidateQueue Implementation
// ============================================================================

CandidateQueue::CandidateQueue(size_t capacity)
    : capacity_(capacity > 0 ? capacity : 1)
    , min_score_(0.0f) {}

bool CandidateQueue::push(const Candidate& candidate) {
    Candidate copy = candidate;
    return push(std::move(copy));
}

bool CandidateQueue::push(Candidate&& candidate) {
    // If queue is full, check if this candidate beats the minimum
    if (full()) {
        if (candidate.composite_score <= min_score_) {
            return false;  // Rejected - doesn't beat minimum
        }
        // Remove the minimum element (root of min-heap)
        heap_[0] = std::move(candidate);
        heapify_down(0);
    } else {
        // Queue not full - just add
        heap_.push_back(std::move(candidate));
        heapify_up(heap_.size() - 1);
    }

    update_min_score();
    return true;
}

const Candidate& CandidateQueue::top() const {
    if (heap_.empty()) {
        throw std::runtime_error("CandidateQueue::top() called on empty queue");
    }
    
    // Find the maximum element (min-heap doesn't give us max directly)
    size_t max_idx = 0;
    for (size_t i = 1; i < heap_.size(); ++i) {
        if (heap_[i].composite_score > heap_[max_idx].composite_score) {
            max_idx = i;
        }
    }
    return heap_[max_idx];
}

Candidate CandidateQueue::pop() {
    if (heap_.empty()) {
        throw std::runtime_error("CandidateQueue::pop() called on empty queue");
    }

    // Find the maximum element
    size_t max_idx = 0;
    for (size_t i = 1; i < heap_.size(); ++i) {
        if (heap_[i].composite_score > heap_[max_idx].composite_score) {
            max_idx = i;
        }
    }

    Candidate result = std::move(heap_[max_idx]);

    // Replace with last element and rebuild
    if (max_idx != heap_.size() - 1) {
        heap_[max_idx] = std::move(heap_.back());
    }
    heap_.pop_back();

    if (!heap_.empty() && max_idx < heap_.size()) {
        // Rebuild heap from the affected position
        rebuild_heap();
    }

    update_min_score();
    return result;
}

std::vector<Candidate> CandidateQueue::get_top_k() const {
    std::vector<Candidate> result = heap_;
    
    // Sort by composite score in descending order
    std::sort(result.begin(), result.end(),
              [](const Candidate& a, const Candidate& b) {
                  return a.composite_score > b.composite_score;
              });

    return result;
}

bool CandidateQueue::would_accept(float score) const {
    if (!full()) return true;
    return score > min_score_;
}

void CandidateQueue::clear() {
    heap_.clear();
    min_score_ = 0.0f;
}

void CandidateQueue::set_capacity(size_t new_capacity) {
    if (new_capacity == 0) new_capacity = 1;
    
    capacity_ = new_capacity;

    // If we have more elements than new capacity, remove lowest-scoring ones
    while (heap_.size() > capacity_) {
        // Remove root (minimum element)
        heap_[0] = std::move(heap_.back());
        heap_.pop_back();
        if (!heap_.empty()) {
            heapify_down(0);
        }
    }

    update_min_score();
}

void CandidateQueue::heapify_up(size_t index) {
    // Min-heap: parent should be smaller than children
    while (index > 0) {
        size_t parent = (index - 1) / 2;
        if (heap_[index].composite_score < heap_[parent].composite_score) {
            std::swap(heap_[index], heap_[parent]);
            index = parent;
        } else {
            break;
        }
    }
}

void CandidateQueue::heapify_down(size_t index) {
    // Min-heap: parent should be smaller than children
    size_t size = heap_.size();
    while (true) {
        size_t smallest = index;
        size_t left = 2 * index + 1;
        size_t right = 2 * index + 2;

        if (left < size && heap_[left].composite_score < heap_[smallest].composite_score) {
            smallest = left;
        }
        if (right < size && heap_[right].composite_score < heap_[smallest].composite_score) {
            smallest = right;
        }

        if (smallest != index) {
            std::swap(heap_[index], heap_[smallest]);
            index = smallest;
        } else {
            break;
        }
    }
}

void CandidateQueue::update_min_score() {
    if (heap_.empty()) {
        min_score_ = 0.0f;
    } else if (full()) {
        // In a min-heap, the root is the minimum
        min_score_ = heap_[0].composite_score;
    } else {
        min_score_ = 0.0f;  // Not full, accept anything
    }
}

void CandidateQueue::rebuild_heap() {
    // Rebuild heap from scratch
    for (size_t i = heap_.size() / 2; i > 0; --i) {
        heapify_down(i - 1);
    }
    if (!heap_.empty()) {
        heapify_down(0);
    }
}

} // namespace etb
