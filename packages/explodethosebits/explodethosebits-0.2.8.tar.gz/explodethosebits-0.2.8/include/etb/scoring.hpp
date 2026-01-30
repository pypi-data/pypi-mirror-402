#ifndef ETB_SCORING_HPP
#define ETB_SCORING_HPP

#include "heuristics.hpp"
#include "signature.hpp"
#include "path.hpp"
#include <cstdint>
#include <vector>
#include <queue>
#include <functional>

namespace etb {

/**
 * Configurable weights for composite scoring.
 * Default weights: signature (40%), heuristic (30%), length (15%), structure (15%)
 */
struct ScoringWeights {
    float signature_weight;     // Weight for signature match score
    float heuristic_weight;     // Weight for heuristic analysis score
    float length_weight;        // Weight for length/completeness score
    float structure_weight;     // Weight for structural validity score

    ScoringWeights()
        : signature_weight(0.40f)
        , heuristic_weight(0.30f)
        , length_weight(0.15f)
        , structure_weight(0.15f) {}

    /**
     * Validate that weights sum to approximately 1.0
     * @return true if weights are valid
     */
    bool is_valid() const;

    /**
     * Normalize weights to sum to 1.0
     */
    void normalize();
};

/**
 * Structural validation result for a candidate.
 */
struct StructuralValidation {
    float validity_score;       // Overall structural validity [0.0, 1.0]
    bool has_valid_length;      // Length claims are coherent
    bool has_valid_checksum;    // Checksum validation passed (if applicable)
    bool has_valid_pointers;    // Internal pointers are coherent (if applicable)

    StructuralValidation()
        : validity_score(0.5f)  // Default neutral score
        , has_valid_length(true)
        , has_valid_checksum(true)
        , has_valid_pointers(true) {}
};

/**
 * A candidate reconstruction with all associated metadata.
 */
struct Candidate {
    Path path;                          // The path taken to reconstruct this candidate
    std::vector<uint8_t> data;          // Reconstructed byte sequence
    uint16_t format_id;                 // Detected format ID (0 = unknown)
    std::string format_name;            // Detected format name
    float confidence;                   // Overall confidence score [0.0, 1.0]
    HeuristicResult heuristics;         // Heuristic analysis results
    SignatureMatch signature_match;     // Signature match results
    StructuralValidation structure;     // Structural validation results
    float composite_score;              // Final weighted composite score

    Candidate()
        : format_id(0)
        , confidence(0.0f)
        , composite_score(0.0f) {}

    /**
     * Compare candidates by composite score (for priority queue).
     */
    bool operator<(const Candidate& other) const {
        return composite_score < other.composite_score;
    }

    bool operator>(const Candidate& other) const {
        return composite_score > other.composite_score;
    }
};

/**
 * Composite score calculator.
 * Calculates weighted scores from component scores.
 */
class ScoreCalculator {
public:
    /**
     * Construct with default weights.
     */
    ScoreCalculator();

    /**
     * Construct with custom weights.
     * @param weights Custom scoring weights
     */
    explicit ScoreCalculator(const ScoringWeights& weights);

    /**
     * Set the scoring weights.
     * @param weights New weights to use
     */
    void set_weights(const ScoringWeights& weights);

    /**
     * Get the current scoring weights.
     */
    const ScoringWeights& get_weights() const { return weights_; }

    /**
     * Calculate composite score from component scores.
     * @param signature_score Signature match score [0.0, 1.0]
     * @param heuristic_score Heuristic analysis score [0.0, 1.0]
     * @param length_score Length/completeness score [0.0, 1.0]
     * @param structure_score Structural validity score [0.0, 1.0]
     * @return Weighted composite score [0.0, 1.0]
     */
    float calculate(float signature_score, float heuristic_score,
                   float length_score, float structure_score) const;

    /**
     * Calculate composite score from a SignatureMatch and HeuristicResult.
     * @param sig_match Signature match result
     * @param heuristics Heuristic analysis result
     * @param data_length Length of reconstructed data
     * @param expected_length Expected length (0 = unknown)
     * @param structure Structural validation result
     * @return Weighted composite score [0.0, 1.0]
     */
    float calculate(const SignatureMatch& sig_match,
                   const HeuristicResult& heuristics,
                   size_t data_length,
                   size_t expected_length,
                   const StructuralValidation& structure) const;

    /**
     * Calculate and populate a Candidate's composite score.
     * @param candidate Candidate to score (modified in place)
     * @param expected_length Expected length for length scoring (0 = unknown)
     */
    void score_candidate(Candidate& candidate, size_t expected_length = 0) const;

private:
    ScoringWeights weights_;

    /**
     * Calculate length score based on actual vs expected length.
     */
    static float calculate_length_score(size_t actual_length, size_t expected_length);
};

/**
 * Priority queue for tracking top-K candidates.
 * Maintains a max-heap based on composite score.
 */
class CandidateQueue {
public:
    /**
     * Construct a candidate queue with specified capacity.
     * @param capacity Maximum number of candidates to track (top-K)
     */
    explicit CandidateQueue(size_t capacity = 10);

    /**
     * Try to add a candidate to the queue.
     * If queue is full and candidate scores lower than minimum, it's rejected.
     * @param candidate Candidate to add
     * @return true if candidate was added, false if rejected
     */
    bool push(const Candidate& candidate);

    /**
     * Try to add a candidate to the queue (move version).
     * @param candidate Candidate to add (moved if accepted)
     * @return true if candidate was added, false if rejected
     */
    bool push(Candidate&& candidate);

    /**
     * Get the top candidate (highest score).
     * @return Reference to top candidate
     * @throws std::runtime_error if queue is empty
     */
    const Candidate& top() const;

    /**
     * Remove and return the top candidate.
     * @return Top candidate
     * @throws std::runtime_error if queue is empty
     */
    Candidate pop();

    /**
     * Get all candidates sorted by score (descending).
     * @return Vector of candidates sorted by composite score
     */
    std::vector<Candidate> get_top_k() const;

    /**
     * Get the minimum score currently in the queue.
     * Used for fast rejection of low-scoring candidates.
     * @return Minimum score, or 0.0 if queue is not full
     */
    float min_score() const { return min_score_; }

    /**
     * Check if a score would be accepted into the queue.
     * @param score Score to check
     * @return true if score would be accepted
     */
    bool would_accept(float score) const;

    /**
     * Get the number of candidates in the queue.
     */
    size_t size() const { return heap_.size(); }

    /**
     * Get the capacity of the queue.
     */
    size_t capacity() const { return capacity_; }

    /**
     * Check if the queue is empty.
     */
    bool empty() const { return heap_.empty(); }

    /**
     * Check if the queue is full.
     */
    bool full() const { return heap_.size() >= capacity_; }

    /**
     * Clear all candidates from the queue.
     */
    void clear();

    /**
     * Set a new capacity for the queue.
     * If new capacity is smaller, lowest-scoring candidates are removed.
     * @param new_capacity New capacity
     */
    void set_capacity(size_t new_capacity);

private:
    size_t capacity_;
    float min_score_;
    
    // Min-heap to efficiently track the minimum score for rejection
    // We use a min-heap so we can efficiently remove the lowest-scoring candidate
    // when the queue is full and a better candidate arrives
    std::vector<Candidate> heap_;

    void heapify_up(size_t index);
    void heapify_down(size_t index);
    void update_min_score();
    void rebuild_heap();
};

} // namespace etb

#endif // ETB_SCORING_HPP
