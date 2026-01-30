#include "etb/config.hpp"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <stdexcept>

namespace etb {

// ============================================================================
// OutputConfig Implementation
// ============================================================================

bool OutputConfig::is_valid() const {
    if (top_n_results == 0) return false;
    if (metrics_verbosity != "minimal" && 
        metrics_verbosity != "standard" && 
        metrics_verbosity != "full") {
        return false;
    }
    return true;
}

// ============================================================================
// PerformanceConfig Implementation
// ============================================================================

bool PerformanceConfig::is_valid() const {
    if (max_parallel_workers == 0) return false;
    if (cuda_streams == 0) return false;
    if (batch_size == 0) return false;
    return true;
}

// ============================================================================
// EtbConfig Implementation
// ============================================================================

EtbConfig::EtbConfig()
    : signature_dictionary_path("signatures.json")
    , entropy_min(0.1f)
    , entropy_max(7.9f)
    , min_printable_ratio(0.95f)
    , max_null_run(16) {}

ConfigResult EtbConfig::validate() const {
    // Validate entropy thresholds
    if (entropy_min < 0.0f || entropy_min > 8.0f) {
        return ConfigResult::fail(ConfigError::OUT_OF_RANGE,
            "entropy_min must be in range [0.0, 8.0]");
    }
    if (entropy_max < 0.0f || entropy_max > 8.0f) {
        return ConfigResult::fail(ConfigError::OUT_OF_RANGE,
            "entropy_max must be in range [0.0, 8.0]");
    }
    if (entropy_min >= entropy_max) {
        return ConfigResult::fail(ConfigError::INVALID_VALUE,
            "entropy_min must be less than entropy_max");
    }

    // Validate printable ratio
    if (min_printable_ratio < 0.0f || min_printable_ratio > 1.0f) {
        return ConfigResult::fail(ConfigError::OUT_OF_RANGE,
            "min_printable_ratio must be in range [0.0, 1.0]");
    }

    // Validate output config
    if (!output.is_valid()) {
        return ConfigResult::fail(ConfigError::INVALID_VALUE,
            "Invalid output configuration");
    }

    // Validate performance config
    if (!performance.is_valid()) {
        return ConfigResult::fail(ConfigError::INVALID_VALUE,
            "Invalid performance configuration");
    }

    // Validate scoring weights
    if (!scoring_weights.is_valid()) {
        return ConfigResult::fail(ConfigError::INVALID_VALUE,
            "Scoring weights must sum to approximately 1.0");
    }

    // Validate bit pruning config
    if (!bit_pruning.is_valid()) {
        return ConfigResult::fail(ConfigError::INVALID_VALUE,
            "Invalid bit pruning configuration");
    }

    return ConfigResult::ok();
}

// ============================================================================
// Simple JSON Parser (minimal implementation without external dependencies)
// ============================================================================

namespace {

// Trim whitespace from string
std::string trim(const std::string& s) {
    size_t start = s.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    size_t end = s.find_last_not_of(" \t\n\r");
    return s.substr(start, end - start + 1);
}

// Skip whitespace in string
size_t skip_whitespace(const std::string& s, size_t pos) {
    while (pos < s.size() && std::isspace(static_cast<unsigned char>(s[pos]))) {
        ++pos;
    }
    return pos;
}

// Parse a JSON string value
std::string parse_json_string(const std::string& s, size_t& pos) {
    pos = skip_whitespace(s, pos);
    if (pos >= s.size() || s[pos] != '"') {
        throw std::runtime_error("Expected '\"' at position " + std::to_string(pos));
    }
    ++pos;
    
    std::string result;
    while (pos < s.size() && s[pos] != '"') {
        if (s[pos] == '\\' && pos + 1 < s.size()) {
            ++pos;
            switch (s[pos]) {
                case '"': result += '"'; break;
                case '\\': result += '\\'; break;
                case 'n': result += '\n'; break;
                case 'r': result += '\r'; break;
                case 't': result += '\t'; break;
                default: result += s[pos]; break;
            }
        } else {
            result += s[pos];
        }
        ++pos;
    }
    
    if (pos >= s.size()) {
        throw std::runtime_error("Unterminated string");
    }
    ++pos; // Skip closing quote
    return result;
}

// Parse a JSON number
double parse_json_number(const std::string& s, size_t& pos) {
    pos = skip_whitespace(s, pos);
    size_t start = pos;
    
    if (pos < s.size() && s[pos] == '-') ++pos;
    while (pos < s.size() && std::isdigit(static_cast<unsigned char>(s[pos]))) ++pos;
    if (pos < s.size() && s[pos] == '.') {
        ++pos;
        while (pos < s.size() && std::isdigit(static_cast<unsigned char>(s[pos]))) ++pos;
    }
    if (pos < s.size() && (s[pos] == 'e' || s[pos] == 'E')) {
        ++pos;
        if (pos < s.size() && (s[pos] == '+' || s[pos] == '-')) ++pos;
        while (pos < s.size() && std::isdigit(static_cast<unsigned char>(s[pos]))) ++pos;
    }
    
    return std::stod(s.substr(start, pos - start));
}

// Parse a JSON boolean
bool parse_json_bool(const std::string& s, size_t& pos) {
    pos = skip_whitespace(s, pos);
    if (s.substr(pos, 4) == "true") {
        pos += 4;
        return true;
    } else if (s.substr(pos, 5) == "false") {
        pos += 5;
        return false;
    }
    throw std::runtime_error("Expected boolean at position " + std::to_string(pos));
}

// Forward declarations for recursive parsing
void skip_json_value(const std::string& s, size_t& pos);

void skip_json_array(const std::string& s, size_t& pos) {
    pos = skip_whitespace(s, pos);
    if (s[pos] != '[') throw std::runtime_error("Expected '['");
    ++pos;
    pos = skip_whitespace(s, pos);
    
    if (s[pos] == ']') {
        ++pos;
        return;
    }
    
    while (true) {
        skip_json_value(s, pos);
        pos = skip_whitespace(s, pos);
        if (s[pos] == ']') {
            ++pos;
            return;
        }
        if (s[pos] != ',') throw std::runtime_error("Expected ',' or ']'");
        ++pos;
    }
}

void skip_json_object(const std::string& s, size_t& pos) {
    pos = skip_whitespace(s, pos);
    if (s[pos] != '{') throw std::runtime_error("Expected '{'");
    ++pos;
    pos = skip_whitespace(s, pos);
    
    if (s[pos] == '}') {
        ++pos;
        return;
    }
    
    while (true) {
        parse_json_string(s, pos); // key
        pos = skip_whitespace(s, pos);
        if (s[pos] != ':') throw std::runtime_error("Expected ':'");
        ++pos;
        skip_json_value(s, pos);
        pos = skip_whitespace(s, pos);
        if (s[pos] == '}') {
            ++pos;
            return;
        }
        if (s[pos] != ',') throw std::runtime_error("Expected ',' or '}'");
        ++pos;
        pos = skip_whitespace(s, pos);
    }
}

void skip_json_value(const std::string& s, size_t& pos) {
    pos = skip_whitespace(s, pos);
    if (pos >= s.size()) throw std::runtime_error("Unexpected end of input");
    
    char c = s[pos];
    if (c == '"') {
        parse_json_string(s, pos);
    } else if (c == '{') {
        skip_json_object(s, pos);
    } else if (c == '[') {
        skip_json_array(s, pos);
    } else if (c == 't' || c == 'f') {
        parse_json_bool(s, pos);
    } else if (c == 'n') {
        if (s.substr(pos, 4) == "null") {
            pos += 4;
        } else {
            throw std::runtime_error("Invalid value at position " + std::to_string(pos));
        }
    } else if (c == '-' || std::isdigit(static_cast<unsigned char>(c))) {
        parse_json_number(s, pos);
    } else {
        throw std::runtime_error("Invalid value at position " + std::to_string(pos));
    }
}

} // anonymous namespace


// ============================================================================
// ConfigManager Implementation
// ============================================================================

ConfigManager& ConfigManager::instance() {
    static ConfigManager instance;
    return instance;
}

ConfigManager::ConfigManager()
    : loaded_(false)
    , next_callback_id_(0) {}

ConfigResult ConfigManager::load_json(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        return ConfigResult::fail(ConfigError::FILE_NOT_FOUND,
            "Could not open configuration file: " + filepath);
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();

    auto result = load_json_string(content);
    if (result.success) {
        std::lock_guard<std::mutex> lock(mutex_);
        loaded_path_ = filepath;
        loaded_.store(true);
    }
    return result;
}

ConfigResult ConfigManager::load_json_string(const std::string& json_content) {
    return parse_json_object(json_content);
}

ConfigResult ConfigManager::parse_json_object(const std::string& json_content) {
    try {
        EtbConfig new_config;
        size_t pos = 0;
        
        pos = skip_whitespace(json_content, pos);
        if (pos >= json_content.size() || json_content[pos] != '{') {
            return ConfigResult::fail(ConfigError::PARSE_ERROR,
                "Expected '{' at start of JSON object");
        }
        ++pos;
        pos = skip_whitespace(json_content, pos);

        while (pos < json_content.size() && json_content[pos] != '}') {
            // Parse key
            std::string key = parse_json_string(json_content, pos);
            pos = skip_whitespace(json_content, pos);
            
            if (json_content[pos] != ':') {
                return ConfigResult::fail(ConfigError::PARSE_ERROR,
                    "Expected ':' after key '" + key + "'");
            }
            ++pos;
            pos = skip_whitespace(json_content, pos);

            // Parse value based on key
            if (key == "signature_dictionary_path") {
                new_config.signature_dictionary_path = parse_json_string(json_content, pos);
            }
            else if (key == "early_stopping") {
                // Parse early_stopping object
                if (json_content[pos] != '{') {
                    return ConfigResult::fail(ConfigError::PARSE_ERROR,
                        "Expected object for 'early_stopping'");
                }
                ++pos;
                pos = skip_whitespace(json_content, pos);
                
                while (json_content[pos] != '}') {
                    std::string subkey = parse_json_string(json_content, pos);
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] != ':') {
                        return ConfigResult::fail(ConfigError::PARSE_ERROR,
                            "Expected ':' in early_stopping");
                    }
                    ++pos;
                    pos = skip_whitespace(json_content, pos);
                    
                    if (subkey == "level1_bytes") {
                        new_config.early_stopping.level1_bytes = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else if (subkey == "level2_bytes") {
                        new_config.early_stopping.level2_bytes = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else if (subkey == "level3_bytes") {
                        new_config.early_stopping.level3_bytes = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else if (subkey == "adaptive_thresholds") {
                        new_config.early_stopping.adaptive_thresholds = parse_json_bool(json_content, pos);
                    } else if (subkey == "level1_threshold") {
                        new_config.early_stopping.level1_threshold = static_cast<float>(parse_json_number(json_content, pos));
                    } else if (subkey == "level2_threshold") {
                        new_config.early_stopping.level2_threshold = static_cast<float>(parse_json_number(json_content, pos));
                    } else if (subkey == "level3_threshold") {
                        new_config.early_stopping.level3_threshold = static_cast<float>(parse_json_number(json_content, pos));
                    } else {
                        skip_json_value(json_content, pos);
                    }
                    
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] == ',') {
                        ++pos;
                        pos = skip_whitespace(json_content, pos);
                    }
                }
                ++pos; // Skip '}'
            }
            else if (key == "entropy_thresholds") {
                // Parse entropy_thresholds object
                if (json_content[pos] != '{') {
                    return ConfigResult::fail(ConfigError::PARSE_ERROR,
                        "Expected object for 'entropy_thresholds'");
                }
                ++pos;
                pos = skip_whitespace(json_content, pos);
                
                while (json_content[pos] != '}') {
                    std::string subkey = parse_json_string(json_content, pos);
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] != ':') {
                        return ConfigResult::fail(ConfigError::PARSE_ERROR,
                            "Expected ':' in entropy_thresholds");
                    }
                    ++pos;
                    pos = skip_whitespace(json_content, pos);
                    
                    if (subkey == "min") {
                        new_config.entropy_min = static_cast<float>(parse_json_number(json_content, pos));
                    } else if (subkey == "max") {
                        new_config.entropy_max = static_cast<float>(parse_json_number(json_content, pos));
                    } else {
                        skip_json_value(json_content, pos);
                    }
                    
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] == ',') {
                        ++pos;
                        pos = skip_whitespace(json_content, pos);
                    }
                }
                ++pos; // Skip '}'
            }
            else if (key == "heuristics") {
                // Parse heuristics object
                if (json_content[pos] != '{') {
                    return ConfigResult::fail(ConfigError::PARSE_ERROR,
                        "Expected object for 'heuristics'");
                }
                ++pos;
                pos = skip_whitespace(json_content, pos);
                
                while (json_content[pos] != '}') {
                    std::string subkey = parse_json_string(json_content, pos);
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] != ':') {
                        return ConfigResult::fail(ConfigError::PARSE_ERROR,
                            "Expected ':' in heuristics");
                    }
                    ++pos;
                    pos = skip_whitespace(json_content, pos);
                    
                    if (subkey == "weights") {
                        // Parse weights sub-object
                        if (json_content[pos] != '{') {
                            skip_json_value(json_content, pos);
                        } else {
                            ++pos;
                            pos = skip_whitespace(json_content, pos);
                            while (json_content[pos] != '}') {
                                std::string wkey = parse_json_string(json_content, pos);
                                pos = skip_whitespace(json_content, pos);
                                if (json_content[pos] != ':') break;
                                ++pos;
                                pos = skip_whitespace(json_content, pos);
                                
                                if (wkey == "signature") {
                                    new_config.scoring_weights.signature_weight = static_cast<float>(parse_json_number(json_content, pos));
                                } else if (wkey == "heuristic") {
                                    new_config.scoring_weights.heuristic_weight = static_cast<float>(parse_json_number(json_content, pos));
                                } else if (wkey == "length") {
                                    new_config.scoring_weights.length_weight = static_cast<float>(parse_json_number(json_content, pos));
                                } else if (wkey == "structure") {
                                    new_config.scoring_weights.structure_weight = static_cast<float>(parse_json_number(json_content, pos));
                                } else {
                                    skip_json_value(json_content, pos);
                                }
                                
                                pos = skip_whitespace(json_content, pos);
                                if (json_content[pos] == ',') {
                                    ++pos;
                                    pos = skip_whitespace(json_content, pos);
                                }
                            }
                            ++pos; // Skip '}'
                        }
                    } else if (subkey == "min_printable_ratio") {
                        new_config.min_printable_ratio = static_cast<float>(parse_json_number(json_content, pos));
                    } else if (subkey == "max_null_run") {
                        new_config.max_null_run = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else {
                        skip_json_value(json_content, pos);
                    }
                    
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] == ',') {
                        ++pos;
                        pos = skip_whitespace(json_content, pos);
                    }
                }
                ++pos; // Skip '}'
            }
            else if (key == "bit_pruning") {
                // Parse bit_pruning object
                if (json_content[pos] != '{') {
                    return ConfigResult::fail(ConfigError::PARSE_ERROR,
                        "Expected object for 'bit_pruning'");
                }
                ++pos;
                pos = skip_whitespace(json_content, pos);
                
                std::string mode_str = "exhaustive";
                std::optional<uint8_t> custom_mask;
                
                while (json_content[pos] != '}') {
                    std::string subkey = parse_json_string(json_content, pos);
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] != ':') {
                        return ConfigResult::fail(ConfigError::PARSE_ERROR,
                            "Expected ':' in bit_pruning");
                    }
                    ++pos;
                    pos = skip_whitespace(json_content, pos);
                    
                    if (subkey == "mode") {
                        mode_str = parse_json_string(json_content, pos);
                    } else if (subkey == "custom_mask") {
                        custom_mask = static_cast<uint8_t>(parse_json_number(json_content, pos));
                    } else {
                        skip_json_value(json_content, pos);
                    }
                    
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] == ',') {
                        ++pos;
                        pos = skip_whitespace(json_content, pos);
                    }
                }
                ++pos; // Skip '}'
                
                auto bp_config = create_bit_pruning_config(mode_str, custom_mask);
                if (bp_config) {
                    new_config.bit_pruning = *bp_config;
                }
            }
            else if (key == "memoization") {
                // Parse memoization object
                if (json_content[pos] != '{') {
                    return ConfigResult::fail(ConfigError::PARSE_ERROR,
                        "Expected object for 'memoization'");
                }
                ++pos;
                pos = skip_whitespace(json_content, pos);
                
                while (json_content[pos] != '}') {
                    std::string subkey = parse_json_string(json_content, pos);
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] != ':') {
                        return ConfigResult::fail(ConfigError::PARSE_ERROR,
                            "Expected ':' in memoization");
                    }
                    ++pos;
                    pos = skip_whitespace(json_content, pos);
                    
                    if (subkey == "enabled") {
                        new_config.memoization.enabled = parse_json_bool(json_content, pos);
                    } else if (subkey == "max_cache_size_mb") {
                        size_t mb = static_cast<size_t>(parse_json_number(json_content, pos));
                        new_config.memoization.max_size_bytes = mb * 1024 * 1024;
                    } else if (subkey == "max_entries") {
                        new_config.memoization.max_entries = static_cast<size_t>(parse_json_number(json_content, pos));
                    } else {
                        skip_json_value(json_content, pos);
                    }
                    
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] == ',') {
                        ++pos;
                        pos = skip_whitespace(json_content, pos);
                    }
                }
                ++pos; // Skip '}'
            }
            else if (key == "performance") {
                // Parse performance object
                if (json_content[pos] != '{') {
                    return ConfigResult::fail(ConfigError::PARSE_ERROR,
                        "Expected object for 'performance'");
                }
                ++pos;
                pos = skip_whitespace(json_content, pos);
                
                while (json_content[pos] != '}') {
                    std::string subkey = parse_json_string(json_content, pos);
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] != ':') {
                        return ConfigResult::fail(ConfigError::PARSE_ERROR,
                            "Expected ':' in performance");
                    }
                    ++pos;
                    pos = skip_whitespace(json_content, pos);
                    
                    if (subkey == "max_parallel_workers") {
                        new_config.performance.max_parallel_workers = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else if (subkey == "cuda_streams") {
                        new_config.performance.cuda_streams = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else if (subkey == "batch_size") {
                        new_config.performance.batch_size = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else {
                        skip_json_value(json_content, pos);
                    }
                    
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] == ',') {
                        ++pos;
                        pos = skip_whitespace(json_content, pos);
                    }
                }
                ++pos; // Skip '}'
            }
            else if (key == "output") {
                // Parse output object
                if (json_content[pos] != '{') {
                    return ConfigResult::fail(ConfigError::PARSE_ERROR,
                        "Expected object for 'output'");
                }
                ++pos;
                pos = skip_whitespace(json_content, pos);
                
                while (json_content[pos] != '}') {
                    std::string subkey = parse_json_string(json_content, pos);
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] != ':') {
                        return ConfigResult::fail(ConfigError::PARSE_ERROR,
                            "Expected ':' in output");
                    }
                    ++pos;
                    pos = skip_whitespace(json_content, pos);
                    
                    if (subkey == "top_n_results") {
                        new_config.output.top_n_results = static_cast<uint32_t>(parse_json_number(json_content, pos));
                    } else if (subkey == "save_partials") {
                        new_config.output.save_partials = parse_json_bool(json_content, pos);
                    } else if (subkey == "include_paths") {
                        new_config.output.include_paths = parse_json_bool(json_content, pos);
                    } else if (subkey == "metrics_verbosity") {
                        new_config.output.metrics_verbosity = parse_json_string(json_content, pos);
                    } else {
                        skip_json_value(json_content, pos);
                    }
                    
                    pos = skip_whitespace(json_content, pos);
                    if (json_content[pos] == ',') {
                        ++pos;
                        pos = skip_whitespace(json_content, pos);
                    }
                }
                ++pos; // Skip '}'
            }
            else {
                // Skip unknown keys
                skip_json_value(json_content, pos);
            }

            pos = skip_whitespace(json_content, pos);
            if (json_content[pos] == ',') {
                ++pos;
                pos = skip_whitespace(json_content, pos);
            }
        }

        // Validate the new configuration
        auto validation = new_config.validate();
        if (!validation.success) {
            return validation;
        }

        // Apply the new configuration
        {
            std::lock_guard<std::mutex> lock(mutex_);
            config_ = new_config;
        }
        notify_callbacks();

        return ConfigResult::ok();
    }
    catch (const std::exception& e) {
        return ConfigResult::fail(ConfigError::PARSE_ERROR,
            std::string("JSON parse error: ") + e.what());
    }
}


// ============================================================================
// YAML Parser (simplified - handles common YAML subset)
// ============================================================================

ConfigResult ConfigManager::load_yaml(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        return ConfigResult::fail(ConfigError::FILE_NOT_FOUND,
            "Could not open configuration file: " + filepath);
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string content = buffer.str();

    auto result = load_yaml_string(content);
    if (result.success) {
        std::lock_guard<std::mutex> lock(mutex_);
        loaded_path_ = filepath;
        loaded_.store(true);
    }
    return result;
}

ConfigResult ConfigManager::load_yaml_string(const std::string& yaml_content) {
    return parse_yaml_content(yaml_content);
}

ConfigResult ConfigManager::parse_yaml_content(const std::string& yaml_content) {
    try {
        EtbConfig new_config;
        std::istringstream stream(yaml_content);
        std::string line;
        std::string current_section;
        std::string current_subsection;
        
        while (std::getline(stream, line)) {
            // Skip comments and empty lines
            std::string trimmed = trim(line);
            if (trimmed.empty() || trimmed[0] == '#') continue;
            
            // Count leading spaces for indentation
            size_t indent = 0;
            while (indent < line.size() && line[indent] == ' ') ++indent;
            
            // Find key-value separator
            size_t colon_pos = trimmed.find(':');
            if (colon_pos == std::string::npos) continue;
            
            std::string key = trim(trimmed.substr(0, colon_pos));
            std::string value = trim(trimmed.substr(colon_pos + 1));
            
            // Remove quotes from string values
            if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
                value = value.substr(1, value.size() - 2);
            }
            if (value.size() >= 2 && value.front() == '\'' && value.back() == '\'') {
                value = value.substr(1, value.size() - 2);
            }
            
            // Handle sections based on indentation
            if (indent == 0) {
                current_section = key;
                current_subsection.clear();
                
                if (!value.empty()) {
                    // Top-level key with value
                    if (key == "signature_dictionary_path") {
                        new_config.signature_dictionary_path = value;
                    }
                }
            }
            else if (indent == 2) {
                current_subsection = key;
                
                // Handle section values
                if (current_section == "early_stopping") {
                    if (key == "level1_bytes") new_config.early_stopping.level1_bytes = std::stoul(value);
                    else if (key == "level2_bytes") new_config.early_stopping.level2_bytes = std::stoul(value);
                    else if (key == "level3_bytes") new_config.early_stopping.level3_bytes = std::stoul(value);
                    else if (key == "adaptive_thresholds") new_config.early_stopping.adaptive_thresholds = (value == "true");
                    else if (key == "level1_threshold") new_config.early_stopping.level1_threshold = std::stof(value);
                    else if (key == "level2_threshold") new_config.early_stopping.level2_threshold = std::stof(value);
                    else if (key == "level3_threshold") new_config.early_stopping.level3_threshold = std::stof(value);
                }
                else if (current_section == "entropy_thresholds") {
                    if (key == "min") new_config.entropy_min = std::stof(value);
                    else if (key == "max") new_config.entropy_max = std::stof(value);
                }
                else if (current_section == "heuristics") {
                    if (key == "min_printable_ratio") new_config.min_printable_ratio = std::stof(value);
                    else if (key == "max_null_run") new_config.max_null_run = std::stoul(value);
                }
                else if (current_section == "bit_pruning") {
                    if (key == "mode") {
                        auto bp_config = create_bit_pruning_config(value);
                        if (bp_config) new_config.bit_pruning = *bp_config;
                    }
                    else if (key == "custom_mask") {
                        new_config.bit_pruning = BitPruningConfig(static_cast<uint8_t>(std::stoul(value)));
                    }
                }
                else if (current_section == "memoization") {
                    if (key == "enabled") new_config.memoization.enabled = (value == "true");
                    else if (key == "max_cache_size_mb") new_config.memoization.max_size_bytes = std::stoull(value) * 1024 * 1024;
                    else if (key == "max_entries") new_config.memoization.max_entries = std::stoull(value);
                }
                else if (current_section == "performance") {
                    if (key == "max_parallel_workers") new_config.performance.max_parallel_workers = std::stoul(value);
                    else if (key == "cuda_streams") new_config.performance.cuda_streams = std::stoul(value);
                    else if (key == "batch_size") new_config.performance.batch_size = std::stoul(value);
                }
                else if (current_section == "output") {
                    if (key == "top_n_results") new_config.output.top_n_results = std::stoul(value);
                    else if (key == "save_partials") new_config.output.save_partials = (value == "true");
                    else if (key == "include_paths") new_config.output.include_paths = (value == "true");
                    else if (key == "metrics_verbosity") new_config.output.metrics_verbosity = value;
                }
            }
            else if (indent == 4) {
                // Handle nested values (e.g., heuristics.weights)
                if (current_section == "heuristics" && current_subsection == "weights") {
                    if (key == "signature") new_config.scoring_weights.signature_weight = std::stof(value);
                    else if (key == "heuristic") new_config.scoring_weights.heuristic_weight = std::stof(value);
                    else if (key == "length") new_config.scoring_weights.length_weight = std::stof(value);
                    else if (key == "structure") new_config.scoring_weights.structure_weight = std::stof(value);
                }
            }
        }

        // Validate the new configuration
        auto validation = new_config.validate();
        if (!validation.success) {
            return validation;
        }

        // Apply the new configuration
        {
            std::lock_guard<std::mutex> lock(mutex_);
            config_ = new_config;
        }
        notify_callbacks();

        return ConfigResult::ok();
    }
    catch (const std::exception& e) {
        return ConfigResult::fail(ConfigError::PARSE_ERROR,
            std::string("YAML parse error: ") + e.what());
    }
}

EtbConfig ConfigManager::get_config() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_;
}

ConfigResult ConfigManager::set_config(const EtbConfig& config) {
    auto validation = config.validate();
    if (!validation.success) {
        return validation;
    }

    {
        std::lock_guard<std::mutex> lock(mutex_);
        config_ = config;
    }
    notify_callbacks();
    return ConfigResult::ok();
}

ConfigResult ConfigManager::update_value(const std::string& key, const std::string& value) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    try {
        // Parse dot-separated key path
        size_t dot_pos = key.find('.');
        std::string section = (dot_pos != std::string::npos) ? key.substr(0, dot_pos) : key;
        std::string subkey = (dot_pos != std::string::npos) ? key.substr(dot_pos + 1) : "";
        
        // Top-level keys (no dot)
        if (key == "signature_dictionary_path") {
            config_.signature_dictionary_path = value;
        }
        else if (section == "early_stopping") {
            if (subkey == "level1_threshold") {
                config_.early_stopping.level1_threshold = std::stof(value);
            } else if (subkey == "level2_threshold") {
                config_.early_stopping.level2_threshold = std::stof(value);
            } else if (subkey == "level3_threshold") {
                config_.early_stopping.level3_threshold = std::stof(value);
            } else if (subkey == "adaptive_thresholds") {
                config_.early_stopping.adaptive_thresholds = (value == "true" || value == "1");
            } else if (subkey == "level1_bytes") {
                config_.early_stopping.level1_bytes = std::stoul(value);
            } else if (subkey == "level2_bytes") {
                config_.early_stopping.level2_bytes = std::stoul(value);
            } else if (subkey == "level3_bytes") {
                config_.early_stopping.level3_bytes = std::stoul(value);
            } else {
                return ConfigResult::fail(ConfigError::INVALID_VALUE,
                    "Unknown early_stopping key: " + subkey);
            }
        }
        else if (section == "entropy_thresholds") {
            if (subkey == "min") {
                config_.entropy_min = std::stof(value);
            } else if (subkey == "max") {
                config_.entropy_max = std::stof(value);
            } else {
                return ConfigResult::fail(ConfigError::INVALID_VALUE,
                    "Unknown entropy_thresholds key: " + subkey);
            }
        }
        else if (section == "heuristics") {
            if (subkey == "min_printable_ratio") {
                config_.min_printable_ratio = std::stof(value);
            } else if (subkey == "max_null_run") {
                config_.max_null_run = std::stoul(value);
            } else {
                return ConfigResult::fail(ConfigError::INVALID_VALUE,
                    "Unknown heuristics key: " + subkey);
            }
        }
        else if (section == "memoization") {
            if (subkey == "enabled") {
                config_.memoization.enabled = (value == "true" || value == "1");
            } else if (subkey == "max_entries") {
                config_.memoization.max_entries = std::stoull(value);
            } else {
                return ConfigResult::fail(ConfigError::INVALID_VALUE,
                    "Unknown memoization key: " + subkey);
            }
        }
        else if (section == "output") {
            if (subkey == "top_n_results") {
                config_.output.top_n_results = std::stoul(value);
            } else if (subkey == "metrics_verbosity") {
                config_.output.metrics_verbosity = value;
            } else if (subkey == "save_partials") {
                config_.output.save_partials = (value == "true" || value == "1");
            } else if (subkey == "include_paths") {
                config_.output.include_paths = (value == "true" || value == "1");
            } else {
                return ConfigResult::fail(ConfigError::INVALID_VALUE,
                    "Unknown output key: " + subkey);
            }
        }
        else if (section == "performance") {
            if (subkey == "max_parallel_workers") {
                config_.performance.max_parallel_workers = std::stoul(value);
            } else if (subkey == "cuda_streams") {
                config_.performance.cuda_streams = std::stoul(value);
            } else if (subkey == "batch_size") {
                config_.performance.batch_size = std::stoul(value);
            } else {
                return ConfigResult::fail(ConfigError::INVALID_VALUE,
                    "Unknown performance key: " + subkey);
            }
        }
        else {
            return ConfigResult::fail(ConfigError::INVALID_VALUE,
                "Unknown configuration key: " + key);
        }
        
        // Validate after update
        auto validation = config_.validate();
        if (!validation.success) {
            return validation;
        }
        
    } catch (const std::exception& e) {
        return ConfigResult::fail(ConfigError::PARSE_ERROR,
            std::string("Failed to parse value: ") + e.what());
    }
    
    notify_callbacks();
    return ConfigResult::ok();
}

size_t ConfigManager::register_change_callback(ConfigChangeCallback callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t id = next_callback_id_++;
    callbacks_.emplace_back(id, std::move(callback));
    return id;
}

void ConfigManager::unregister_change_callback(size_t id) {
    std::lock_guard<std::mutex> lock(mutex_);
    callbacks_.erase(
        std::remove_if(callbacks_.begin(), callbacks_.end(),
            [id](const auto& pair) { return pair.first == id; }),
        callbacks_.end());
}

ConfigResult ConfigManager::reload() {
    std::string path;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        path = loaded_path_;
    }
    
    if (path.empty()) {
        return ConfigResult::fail(ConfigError::FILE_NOT_FOUND,
            "No configuration file has been loaded");
    }
    
    // Determine format from extension
    size_t dot_pos = path.rfind('.');
    if (dot_pos != std::string::npos) {
        std::string ext = path.substr(dot_pos);
        std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
        
        if (ext == ".yaml" || ext == ".yml") {
            return load_yaml(path);
        }
    }
    
    return load_json(path);
}

std::string ConfigManager::get_loaded_path() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return loaded_path_;
}

void ConfigManager::reset_to_defaults() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        config_ = EtbConfig();
        loaded_path_.clear();
        loaded_.store(false);
    }
    notify_callbacks();
}

void ConfigManager::notify_callbacks() {
    EtbConfig config_copy;
    std::vector<ConfigChangeCallback> callbacks_copy;
    
    {
        std::lock_guard<std::mutex> lock(mutex_);
        config_copy = config_;
        for (const auto& pair : callbacks_) {
            callbacks_copy.push_back(pair.second);
        }
    }
    
    for (const auto& callback : callbacks_copy) {
        callback(config_copy);
    }
}

bool ConfigManager::parse_bool(const std::string& value, bool& out) {
    std::string lower = value;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    if (lower == "true" || lower == "1" || lower == "yes") {
        out = true;
        return true;
    }
    if (lower == "false" || lower == "0" || lower == "no") {
        out = false;
        return true;
    }
    return false;
}

bool ConfigManager::parse_float(const std::string& value, float& out) {
    try {
        out = std::stof(value);
        return true;
    } catch (...) {
        return false;
    }
}

bool ConfigManager::parse_uint32(const std::string& value, uint32_t& out) {
    try {
        out = static_cast<uint32_t>(std::stoul(value));
        return true;
    } catch (...) {
        return false;
    }
}

bool ConfigManager::parse_size_t(const std::string& value, size_t& out) {
    try {
        out = static_cast<size_t>(std::stoull(value));
        return true;
    } catch (...) {
        return false;
    }
}


// ============================================================================
// Serialization (to JSON/YAML)
// ============================================================================

std::string ConfigManager::to_json_string() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::ostringstream ss;
    
    ss << "{\n";
    ss << "  \"signature_dictionary_path\": \"" << config_.signature_dictionary_path << "\",\n";
    
    ss << "  \"early_stopping\": {\n";
    ss << "    \"level1_bytes\": " << config_.early_stopping.level1_bytes << ",\n";
    ss << "    \"level2_bytes\": " << config_.early_stopping.level2_bytes << ",\n";
    ss << "    \"level3_bytes\": " << config_.early_stopping.level3_bytes << ",\n";
    ss << "    \"adaptive_thresholds\": " << (config_.early_stopping.adaptive_thresholds ? "true" : "false") << ",\n";
    ss << "    \"level1_threshold\": " << config_.early_stopping.level1_threshold << ",\n";
    ss << "    \"level2_threshold\": " << config_.early_stopping.level2_threshold << ",\n";
    ss << "    \"level3_threshold\": " << config_.early_stopping.level3_threshold << "\n";
    ss << "  },\n";
    
    ss << "  \"entropy_thresholds\": {\n";
    ss << "    \"min\": " << config_.entropy_min << ",\n";
    ss << "    \"max\": " << config_.entropy_max << "\n";
    ss << "  },\n";
    
    ss << "  \"heuristics\": {\n";
    ss << "    \"weights\": {\n";
    ss << "      \"signature\": " << config_.scoring_weights.signature_weight << ",\n";
    ss << "      \"heuristic\": " << config_.scoring_weights.heuristic_weight << ",\n";
    ss << "      \"length\": " << config_.scoring_weights.length_weight << ",\n";
    ss << "      \"structure\": " << config_.scoring_weights.structure_weight << "\n";
    ss << "    },\n";
    ss << "    \"min_printable_ratio\": " << config_.min_printable_ratio << ",\n";
    ss << "    \"max_null_run\": " << config_.max_null_run << "\n";
    ss << "  },\n";
    
    ss << "  \"bit_pruning\": {\n";
    ss << "    \"mode\": \"" << bit_pruning_mode_to_string(config_.bit_pruning.mode) << "\",\n";
    ss << "    \"custom_mask\": " << static_cast<int>(config_.bit_pruning.bit_mask) << "\n";
    ss << "  },\n";
    
    ss << "  \"memoization\": {\n";
    ss << "    \"enabled\": " << (config_.memoization.enabled ? "true" : "false") << ",\n";
    ss << "    \"max_cache_size_mb\": " << (config_.memoization.max_size_bytes / (1024 * 1024)) << ",\n";
    ss << "    \"max_entries\": " << config_.memoization.max_entries << "\n";
    ss << "  },\n";
    
    ss << "  \"performance\": {\n";
    ss << "    \"max_parallel_workers\": " << config_.performance.max_parallel_workers << ",\n";
    ss << "    \"cuda_streams\": " << config_.performance.cuda_streams << ",\n";
    ss << "    \"batch_size\": " << config_.performance.batch_size << "\n";
    ss << "  },\n";
    
    ss << "  \"output\": {\n";
    ss << "    \"top_n_results\": " << config_.output.top_n_results << ",\n";
    ss << "    \"save_partials\": " << (config_.output.save_partials ? "true" : "false") << ",\n";
    ss << "    \"include_paths\": " << (config_.output.include_paths ? "true" : "false") << ",\n";
    ss << "    \"metrics_verbosity\": \"" << config_.output.metrics_verbosity << "\"\n";
    ss << "  }\n";
    
    ss << "}\n";
    
    return ss.str();
}

std::string ConfigManager::to_yaml_string() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::ostringstream ss;
    
    ss << "# ExplodeThoseBits (etb) Configuration\n\n";
    
    ss << "signature_dictionary_path: \"" << config_.signature_dictionary_path << "\"\n\n";
    
    ss << "early_stopping:\n";
    ss << "  level1_bytes: " << config_.early_stopping.level1_bytes << "\n";
    ss << "  level2_bytes: " << config_.early_stopping.level2_bytes << "\n";
    ss << "  level3_bytes: " << config_.early_stopping.level3_bytes << "\n";
    ss << "  adaptive_thresholds: " << (config_.early_stopping.adaptive_thresholds ? "true" : "false") << "\n";
    ss << "  level1_threshold: " << config_.early_stopping.level1_threshold << "\n";
    ss << "  level2_threshold: " << config_.early_stopping.level2_threshold << "\n";
    ss << "  level3_threshold: " << config_.early_stopping.level3_threshold << "\n\n";
    
    ss << "entropy_thresholds:\n";
    ss << "  min: " << config_.entropy_min << "  # Below this = repeated pattern garbage\n";
    ss << "  max: " << config_.entropy_max << "  # Above this = random/encrypted\n\n";
    
    ss << "heuristics:\n";
    ss << "  weights:\n";
    ss << "    signature: " << config_.scoring_weights.signature_weight << "\n";
    ss << "    heuristic: " << config_.scoring_weights.heuristic_weight << "\n";
    ss << "    length: " << config_.scoring_weights.length_weight << "\n";
    ss << "    structure: " << config_.scoring_weights.structure_weight << "\n";
    ss << "  min_printable_ratio: " << config_.min_printable_ratio << "  # For text detection\n";
    ss << "  max_null_run: " << config_.max_null_run << "  # Max consecutive nulls before penalty\n\n";
    
    ss << "bit_pruning:\n";
    ss << "  mode: \"" << bit_pruning_mode_to_string(config_.bit_pruning.mode) << "\"  # exhaustive, msb_only, single_bit, custom\n";
    ss << "  custom_mask: " << static_cast<int>(config_.bit_pruning.bit_mask) << "\n\n";
    
    ss << "memoization:\n";
    ss << "  enabled: " << (config_.memoization.enabled ? "true" : "false") << "\n";
    ss << "  max_cache_size_mb: " << (config_.memoization.max_size_bytes / (1024 * 1024)) << "\n";
    ss << "  max_entries: " << config_.memoization.max_entries << "\n\n";
    
    ss << "performance:\n";
    ss << "  max_parallel_workers: " << config_.performance.max_parallel_workers << "  # CPU threads for host coordination\n";
    ss << "  cuda_streams: " << config_.performance.cuda_streams << "  # Concurrent CUDA streams\n";
    ss << "  batch_size: " << config_.performance.batch_size << "  # Paths per kernel launch\n\n";
    
    ss << "output:\n";
    ss << "  top_n_results: " << config_.output.top_n_results << "\n";
    ss << "  save_partials: " << (config_.output.save_partials ? "true" : "false") << "\n";
    ss << "  include_paths: " << (config_.output.include_paths ? "true" : "false") << "\n";
    ss << "  metrics_verbosity: \"" << config_.output.metrics_verbosity << "\"  # minimal, standard, full\n";
    
    return ss.str();
}

ConfigResult ConfigManager::save_json(const std::string& filepath) const {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        return ConfigResult::fail(ConfigError::FILE_NOT_FOUND,
            "Could not open file for writing: " + filepath);
    }
    
    file << to_json_string();
    return ConfigResult::ok();
}

ConfigResult ConfigManager::save_yaml(const std::string& filepath) const {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        return ConfigResult::fail(ConfigError::FILE_NOT_FOUND,
            "Could not open file for writing: " + filepath);
    }
    
    file << to_yaml_string();
    return ConfigResult::ok();
}

// ============================================================================
// Free Functions
// ============================================================================

ConfigResult load_config(const std::string& filepath) {
    // Determine format from extension
    size_t dot_pos = filepath.rfind('.');
    if (dot_pos != std::string::npos) {
        std::string ext = filepath.substr(dot_pos);
        std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
        
        if (ext == ".yaml" || ext == ".yml") {
            return ConfigManager::instance().load_yaml(filepath);
        }
    }
    
    return ConfigManager::instance().load_json(filepath);
}

EtbConfig get_default_config() {
    return EtbConfig();
}

} // namespace etb
