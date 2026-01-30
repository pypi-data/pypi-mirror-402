#ifndef ETB_CONFIG_HPP
#define ETB_CONFIG_HPP

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>
#include <optional>
#include <mutex>
#include <functional>
#include <atomic>
#include "heuristics.hpp"
#include "early_stopping.hpp"
#include "bit_pruning.hpp"
#include "scoring.hpp"
#include "memoization.hpp"

namespace etb {

/**
 * Error codes for configuration operations.
 */
enum class ConfigError {
    NONE = 0,
    FILE_NOT_FOUND,
    PARSE_ERROR,
    INVALID_VALUE,
    MISSING_REQUIRED_FIELD,
    TYPE_MISMATCH,
    OUT_OF_RANGE
};

/**
 * Result of a configuration operation.
 */
struct ConfigResult {
    bool success;
    ConfigError error;
    std::string message;

    ConfigResult() : success(true), error(ConfigError::NONE) {}
    ConfigResult(ConfigError err, const std::string& msg)
        : success(false), error(err), message(msg) {}

    static ConfigResult ok() { return ConfigResult(); }
    static ConfigResult fail(ConfigError err, const std::string& msg) {
        return ConfigResult(err, msg);
    }
};

/**
 * Output configuration options.
 */
struct OutputConfig {
    uint32_t top_n_results;         // Number of top results to return (default: 10)
    bool save_partials;             // Save partial matches (default: false)
    bool include_paths;             // Include reconstruction paths in output (default: true)
    std::string metrics_verbosity;  // "minimal", "standard", "full" (default: "full")

    OutputConfig()
        : top_n_results(10)
        , save_partials(false)
        , include_paths(true)
        , metrics_verbosity("full") {}

    bool is_valid() const;
};

/**
 * Performance configuration options.
 */
struct PerformanceConfig {
    uint32_t max_parallel_workers;  // CPU threads for host coordination (default: 8)
    uint32_t cuda_streams;          // Concurrent CUDA streams (default: 4)
    uint32_t batch_size;            // Paths per kernel launch (default: 65536)

    PerformanceConfig()
        : max_parallel_workers(8)
        , cuda_streams(4)
        , batch_size(65536) {}

    bool is_valid() const;
};


/**
 * Complete configuration for the etb library.
 * Aggregates all component configurations.
 */
struct EtbConfig {
    // Paths
    std::string signature_dictionary_path;

    // Component configurations
    EarlyStoppingConfig early_stopping;
    HeuristicWeights heuristic_weights;
    ScoringWeights scoring_weights;
    BitPruningConfig bit_pruning;
    MemoizationConfig memoization;
    OutputConfig output;
    PerformanceConfig performance;

    // Entropy thresholds (separate from early stopping for clarity)
    float entropy_min;              // Below this = repeated pattern garbage (default: 0.1)
    float entropy_max;              // Above this = random/encrypted (default: 7.9)

    // Text detection thresholds
    float min_printable_ratio;      // For text detection (default: 0.95)
    uint32_t max_null_run;          // Max consecutive nulls before penalty (default: 16)

    EtbConfig();

    /**
     * Validate the entire configuration.
     * @return ConfigResult with success/failure and error details
     */
    ConfigResult validate() const;
};

/**
 * Callback type for configuration change notifications.
 */
using ConfigChangeCallback = std::function<void(const EtbConfig&)>;

/**
 * Configuration loader and manager.
 * Supports JSON and YAML formats, runtime updates, and hot-reload.
 * 
 * Requirements: 11.1, 11.2, 11.3, 11.4, 2.7
 */
class ConfigManager {
public:
    /**
     * Get the singleton instance.
     */
    static ConfigManager& instance();

    /**
     * Load configuration from a JSON file.
     * @param filepath Path to the JSON configuration file
     * @return ConfigResult with success/failure and error details
     */
    ConfigResult load_json(const std::string& filepath);

    /**
     * Load configuration from a JSON string.
     * @param json_content JSON content as string
     * @return ConfigResult with success/failure and error details
     */
    ConfigResult load_json_string(const std::string& json_content);

    /**
     * Load configuration from a YAML file.
     * @param filepath Path to the YAML configuration file
     * @return ConfigResult with success/failure and error details
     */
    ConfigResult load_yaml(const std::string& filepath);

    /**
     * Load configuration from a YAML string.
     * @param yaml_content YAML content as string
     * @return ConfigResult with success/failure and error details
     */
    ConfigResult load_yaml_string(const std::string& yaml_content);

    /**
     * Get the current configuration (thread-safe read).
     * @return Copy of the current configuration
     */
    EtbConfig get_config() const;

    /**
     * Set the configuration (thread-safe write).
     * @param config New configuration to set
     * @return ConfigResult with validation result
     */
    ConfigResult set_config(const EtbConfig& config);

    /**
     * Update a specific configuration value at runtime.
     * Only certain parameters support hot-reload.
     * @param key Configuration key (e.g., "early_stopping.level1_threshold")
     * @param value New value as string
     * @return ConfigResult with success/failure
     */
    ConfigResult update_value(const std::string& key, const std::string& value);

    /**
     * Register a callback for configuration changes.
     * @param callback Function to call when configuration changes
     * @return ID for unregistering the callback
     */
    size_t register_change_callback(ConfigChangeCallback callback);

    /**
     * Unregister a configuration change callback.
     * @param id Callback ID returned by register_change_callback
     */
    void unregister_change_callback(size_t id);

    /**
     * Reload configuration from the last loaded file.
     * @return ConfigResult with success/failure
     */
    ConfigResult reload();

    /**
     * Check if a configuration file has been loaded.
     */
    bool is_loaded() const { return loaded_.load(); }

    /**
     * Get the path of the last loaded configuration file.
     */
    std::string get_loaded_path() const;

    /**
     * Reset to default configuration.
     */
    void reset_to_defaults();

    /**
     * Save current configuration to a JSON file.
     * @param filepath Path to save to
     * @return ConfigResult with success/failure
     */
    ConfigResult save_json(const std::string& filepath) const;

    /**
     * Save current configuration to a YAML file.
     * @param filepath Path to save to
     * @return ConfigResult with success/failure
     */
    ConfigResult save_yaml(const std::string& filepath) const;

    /**
     * Get configuration as JSON string.
     */
    std::string to_json_string() const;

    /**
     * Get configuration as YAML string.
     */
    std::string to_yaml_string() const;

private:
    ConfigManager();
    ~ConfigManager() = default;
    ConfigManager(const ConfigManager&) = delete;
    ConfigManager& operator=(const ConfigManager&) = delete;

    mutable std::mutex mutex_;
    EtbConfig config_;
    std::string loaded_path_;
    std::atomic<bool> loaded_;
    std::vector<std::pair<size_t, ConfigChangeCallback>> callbacks_;
    size_t next_callback_id_;

    void notify_callbacks();
    ConfigResult parse_json_object(const std::string& json_content);
    ConfigResult parse_yaml_content(const std::string& yaml_content);
    
    // Helper functions for parsing
    static bool parse_bool(const std::string& value, bool& out);
    static bool parse_float(const std::string& value, float& out);
    static bool parse_uint32(const std::string& value, uint32_t& out);
    static bool parse_size_t(const std::string& value, size_t& out);
};

/**
 * Helper function to load configuration from file (auto-detects format).
 * @param filepath Path to configuration file (.json or .yaml/.yml)
 * @return ConfigResult with success/failure
 */
ConfigResult load_config(const std::string& filepath);

/**
 * Get the default configuration.
 */
EtbConfig get_default_config();

} // namespace etb

#endif // ETB_CONFIG_HPP
