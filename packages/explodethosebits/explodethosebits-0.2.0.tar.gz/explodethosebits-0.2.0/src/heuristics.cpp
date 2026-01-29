#include "etb/heuristics.hpp"
#include <cmath>
#include <algorithm>

namespace etb {

HeuristicsEngine::HeuristicsEngine() : weights_() {}

HeuristicsEngine::HeuristicsEngine(const HeuristicWeights& weights) : weights_(weights) {}

void HeuristicsEngine::set_weights(const HeuristicWeights& weights) {
    weights_ = weights;
}

std::array<uint32_t, 256> HeuristicsEngine::build_histogram(const uint8_t* data, size_t length) {
    std::array<uint32_t, 256> histogram{};
    for (size_t i = 0; i < length; ++i) {
        histogram[data[i]]++;
    }
    return histogram;
}

float HeuristicsEngine::calculate_entropy(const uint8_t* data, size_t length) {
    if (length == 0) {
        return 0.0f;
    }

    // Build frequency histogram
    auto histogram = build_histogram(data, length);

    // Calculate Shannon entropy: H = -Σ p(x) * log2(p(x))
    double entropy = 0.0;
    const double length_d = static_cast<double>(length);

    for (size_t i = 0; i < 256; ++i) {
        if (histogram[i] > 0) {
            double probability = static_cast<double>(histogram[i]) / length_d;
            entropy -= probability * std::log2(probability);
        }
    }

    // Clamp to valid range [0.0, 8.0]
    return static_cast<float>(std::clamp(entropy, 0.0, 8.0));
}

float HeuristicsEngine::calculate_entropy(const std::vector<uint8_t>& data) {
    return calculate_entropy(data.data(), data.size());
}

float HeuristicsEngine::calculate_printable_ratio(const uint8_t* data, size_t length) {
    if (length == 0) {
        return 0.0f;
    }

    uint32_t printable_count = 0;
    for (size_t i = 0; i < length; ++i) {
        // Printable ASCII: 0x20 (space) to 0x7E (~)
        if (data[i] >= 0x20 && data[i] <= 0x7E) {
            printable_count++;
        }
    }

    return static_cast<float>(printable_count) / static_cast<float>(length);
}

float HeuristicsEngine::calculate_control_char_ratio(const uint8_t* data, size_t length) {
    if (length == 0) {
        return 0.0f;
    }

    uint32_t control_count = 0;
    for (size_t i = 0; i < length; ++i) {
        // Control characters: 0x00-0x1F, excluding common whitespace
        // Tab (0x09), Line Feed (0x0A), Carriage Return (0x0D) are not counted
        if (data[i] < 0x20 && data[i] != 0x09 && data[i] != 0x0A && data[i] != 0x0D) {
            control_count++;
        }
    }

    return static_cast<float>(control_count) / static_cast<float>(length);
}

uint32_t HeuristicsEngine::find_max_null_run(const uint8_t* data, size_t length) {
    if (length == 0) {
        return 0;
    }

    uint32_t max_run = 0;
    uint32_t current_run = 0;

    for (size_t i = 0; i < length; ++i) {
        if (data[i] == 0x00) {
            current_run++;
            if (current_run > max_run) {
                max_run = current_run;
            }
        } else {
            current_run = 0;
        }
    }

    return max_run;
}

float HeuristicsEngine::validate_utf8(const uint8_t* data, size_t length) {
    if (length == 0) {
        return 1.0f;  // Empty is considered valid
    }

    size_t valid_sequences = 0;
    size_t total_sequences = 0;
    size_t i = 0;

    while (i < length) {
        total_sequences++;
        uint8_t byte = data[i];

        // Determine expected sequence length based on first byte
        size_t seq_len = 0;
        
        if ((byte & 0x80) == 0x00) {
            // Single byte ASCII (0xxxxxxx)
            seq_len = 1;
            valid_sequences++;
            i++;
            continue;
        } else if ((byte & 0xE0) == 0xC0) {
            // Two-byte sequence (110xxxxx)
            seq_len = 2;
            // Check for overlong encoding (must be >= 0x80)
            if (byte < 0xC2) {
                i++;
                continue;  // Invalid: overlong encoding
            }
        } else if ((byte & 0xF0) == 0xE0) {
            // Three-byte sequence (1110xxxx)
            seq_len = 3;
        } else if ((byte & 0xF8) == 0xF0) {
            // Four-byte sequence (11110xxx)
            seq_len = 4;
            // Check for valid range (must be <= 0xF4 for valid Unicode)
            if (byte > 0xF4) {
                i++;
                continue;  // Invalid: beyond Unicode range
            }
        } else {
            // Invalid start byte (continuation byte or invalid)
            i++;
            continue;
        }

        // Check if we have enough bytes
        if (i + seq_len > length) {
            i++;
            continue;  // Truncated sequence
        }

        // Validate continuation bytes (must be 10xxxxxx)
        bool valid = true;
        for (size_t j = 1; j < seq_len; ++j) {
            if ((data[i + j] & 0xC0) != 0x80) {
                valid = false;
                break;
            }
        }

        if (valid) {
            // Additional checks for overlong encodings and surrogate pairs
            if (seq_len == 3) {
                // Check for overlong 3-byte (must be >= 0x800)
                if (byte == 0xE0 && data[i + 1] < 0xA0) {
                    valid = false;
                }
                // Check for surrogate pairs (0xD800-0xDFFF are invalid)
                if (byte == 0xED && data[i + 1] >= 0xA0) {
                    valid = false;
                }
            } else if (seq_len == 4) {
                // Check for overlong 4-byte (must be >= 0x10000)
                if (byte == 0xF0 && data[i + 1] < 0x90) {
                    valid = false;
                }
                // Check for beyond Unicode range (must be <= 0x10FFFF)
                if (byte == 0xF4 && data[i + 1] > 0x8F) {
                    valid = false;
                }
            }
        }

        if (valid) {
            valid_sequences++;
        }

        i += seq_len;
    }

    if (total_sequences == 0) {
        return 1.0f;
    }

    return static_cast<float>(valid_sequences) / static_cast<float>(total_sequences);
}

float HeuristicsEngine::calculate_composite_score(const HeuristicResult& result, size_t data_length) const {
    // Normalize entropy to [0, 1] range (divide by max entropy of 8.0)
    float entropy_score = result.entropy / 8.0f;
    
    // For text-like data, mid-range entropy (3.5-5.5) is ideal
    // Penalize very low (repeated patterns) and very high (random/encrypted)
    float entropy_quality = 1.0f;
    if (result.entropy < 0.5f) {
        entropy_quality = result.entropy / 0.5f;  // Penalize very low entropy
    } else if (result.entropy > 7.5f) {
        entropy_quality = (8.0f - result.entropy) / 0.5f;  // Penalize very high entropy
    }

    // Printable ratio is already in [0, 1]
    float printable_score = result.printable_ratio;

    // Control char ratio should be low - invert for scoring
    float control_score = 1.0f - result.control_char_ratio;

    // Null run penalty - longer runs are worse
    // Use exponential decay: score = exp(-run_length / threshold)
    const float null_threshold = 16.0f;
    float null_score = std::exp(-static_cast<float>(result.max_null_run) / null_threshold);

    // UTF-8 validity is already in [0, 1]
    float utf8_score = result.utf8_validity;

    // Calculate weighted sum
    float total_weight = weights_.entropy_weight + weights_.printable_weight +
                        weights_.control_char_weight + weights_.null_run_weight +
                        weights_.utf8_weight;

    if (total_weight <= 0.0f) {
        return 0.0f;
    }

    float composite = (entropy_quality * weights_.entropy_weight +
                      printable_score * weights_.printable_weight +
                      control_score * weights_.control_char_weight +
                      null_score * weights_.null_run_weight +
                      utf8_score * weights_.utf8_weight) / total_weight;

    return std::clamp(composite, 0.0f, 1.0f);
}

HeuristicResult HeuristicsEngine::analyze(const uint8_t* data, size_t length) const {
    HeuristicResult result;

    if (length == 0) {
        return result;
    }

    result.entropy = calculate_entropy(data, length);
    result.printable_ratio = calculate_printable_ratio(data, length);
    result.control_char_ratio = calculate_control_char_ratio(data, length);
    result.max_null_run = find_max_null_run(data, length);
    result.utf8_validity = validate_utf8(data, length);
    result.composite_score = calculate_composite_score(result, length);

    return result;
}

HeuristicResult HeuristicsEngine::analyze(const std::vector<uint8_t>& data) const {
    return analyze(data.data(), data.size());
}

} // namespace etb
