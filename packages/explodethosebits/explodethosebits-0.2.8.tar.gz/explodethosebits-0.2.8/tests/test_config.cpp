#include <gtest/gtest.h>
#include "etb/config.hpp"
#include <fstream>
#include <cstdio>

using namespace etb;

class ConfigTest : public ::testing::Test {
protected:
    void SetUp() override {
        ConfigManager::instance().reset_to_defaults();
    }

    void TearDown() override {
        // Clean up any test files
        std::remove("test_config.json");
        std::remove("test_config.yaml");
    }
};

// ============================================================================
// EtbConfig Validation Tests
// ============================================================================

TEST_F(ConfigTest, DefaultConfigIsValid) {
    EtbConfig config;
    auto result = config.validate();
    EXPECT_TRUE(result.success);
}

TEST_F(ConfigTest, InvalidEntropyMinOutOfRange) {
    EtbConfig config;
    config.entropy_min = -1.0f;
    auto result = config.validate();
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::OUT_OF_RANGE);
}

TEST_F(ConfigTest, InvalidEntropyMaxOutOfRange) {
    EtbConfig config;
    config.entropy_max = 9.0f;
    auto result = config.validate();
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::OUT_OF_RANGE);
}

TEST_F(ConfigTest, InvalidEntropyMinGreaterThanMax) {
    EtbConfig config;
    config.entropy_min = 5.0f;
    config.entropy_max = 3.0f;
    auto result = config.validate();
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::INVALID_VALUE);
}

TEST_F(ConfigTest, InvalidPrintableRatioOutOfRange) {
    EtbConfig config;
    config.min_printable_ratio = 1.5f;
    auto result = config.validate();
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::OUT_OF_RANGE);
}

TEST_F(ConfigTest, InvalidOutputConfig) {
    EtbConfig config;
    config.output.top_n_results = 0;
    auto result = config.validate();
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::INVALID_VALUE);
}

TEST_F(ConfigTest, InvalidMetricsVerbosity) {
    EtbConfig config;
    config.output.metrics_verbosity = "invalid";
    auto result = config.validate();
    EXPECT_FALSE(result.success);
}

// ============================================================================
// JSON Parsing Tests
// ============================================================================

TEST_F(ConfigTest, LoadJsonString_ValidConfig) {
    const char* json = R"({
        "signature_dictionary_path": "custom_signatures.json",
        "early_stopping": {
            "level1_bytes": 8,
            "level2_bytes": 16,
            "level3_bytes": 32,
            "adaptive_thresholds": false
        },
        "entropy_thresholds": {
            "min": 0.5,
            "max": 7.5
        },
        "output": {
            "top_n_results": 20,
            "metrics_verbosity": "minimal"
        }
    })";

    auto result = ConfigManager::instance().load_json_string(json);
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.signature_dictionary_path, "custom_signatures.json");
    EXPECT_EQ(config.early_stopping.level1_bytes, 8u);
    EXPECT_EQ(config.early_stopping.level2_bytes, 16u);
    EXPECT_EQ(config.early_stopping.level3_bytes, 32u);
    EXPECT_FALSE(config.early_stopping.adaptive_thresholds);
    EXPECT_FLOAT_EQ(config.entropy_min, 0.5f);
    EXPECT_FLOAT_EQ(config.entropy_max, 7.5f);
    EXPECT_EQ(config.output.top_n_results, 20u);
    EXPECT_EQ(config.output.metrics_verbosity, "minimal");
}

TEST_F(ConfigTest, LoadJsonString_InvalidJson) {
    const char* json = "{ invalid json }";
    auto result = ConfigManager::instance().load_json_string(json);
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::PARSE_ERROR);
}

TEST_F(ConfigTest, LoadJsonString_HeuristicsWeights) {
    const char* json = R"({
        "heuristics": {
            "weights": {
                "signature": 0.50,
                "heuristic": 0.25,
                "length": 0.15,
                "structure": 0.10
            },
            "min_printable_ratio": 0.90,
            "max_null_run": 32
        }
    })";

    auto result = ConfigManager::instance().load_json_string(json);
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_FLOAT_EQ(config.scoring_weights.signature_weight, 0.50f);
    EXPECT_FLOAT_EQ(config.scoring_weights.heuristic_weight, 0.25f);
    EXPECT_FLOAT_EQ(config.scoring_weights.length_weight, 0.15f);
    EXPECT_FLOAT_EQ(config.scoring_weights.structure_weight, 0.10f);
    EXPECT_FLOAT_EQ(config.min_printable_ratio, 0.90f);
    EXPECT_EQ(config.max_null_run, 32u);
}

TEST_F(ConfigTest, LoadJsonString_BitPruning) {
    const char* json = R"({
        "bit_pruning": {
            "mode": "msb_only"
        }
    })";

    auto result = ConfigManager::instance().load_json_string(json);
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.bit_pruning.mode, BitPruningMode::MSB_ONLY);
}

TEST_F(ConfigTest, LoadJsonString_Memoization) {
    const char* json = R"({
        "memoization": {
            "enabled": false,
            "max_cache_size_mb": 512,
            "max_entries": 500000
        }
    })";

    auto result = ConfigManager::instance().load_json_string(json);
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_FALSE(config.memoization.enabled);
    EXPECT_EQ(config.memoization.max_size_bytes, 512u * 1024 * 1024);
    EXPECT_EQ(config.memoization.max_entries, 500000u);
}

TEST_F(ConfigTest, LoadJsonString_Performance) {
    const char* json = R"({
        "performance": {
            "max_parallel_workers": 16,
            "cuda_streams": 8,
            "batch_size": 131072
        }
    })";

    auto result = ConfigManager::instance().load_json_string(json);
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.performance.max_parallel_workers, 16u);
    EXPECT_EQ(config.performance.cuda_streams, 8u);
    EXPECT_EQ(config.performance.batch_size, 131072u);
}

// ============================================================================
// YAML Parsing Tests
// ============================================================================

TEST_F(ConfigTest, LoadYamlString_ValidConfig) {
    const char* yaml = R"(
signature_dictionary_path: "custom_signatures.json"

early_stopping:
  level1_bytes: 8
  level2_bytes: 16
  level3_bytes: 32
  adaptive_thresholds: false

entropy_thresholds:
  min: 0.5
  max: 7.5

output:
  top_n_results: 20
  metrics_verbosity: minimal
)";

    auto result = ConfigManager::instance().load_yaml_string(yaml);
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.signature_dictionary_path, "custom_signatures.json");
    EXPECT_EQ(config.early_stopping.level1_bytes, 8u);
    EXPECT_FLOAT_EQ(config.entropy_min, 0.5f);
    EXPECT_EQ(config.output.top_n_results, 20u);
}

TEST_F(ConfigTest, LoadYamlString_WithComments) {
    const char* yaml = R"(
# This is a comment
signature_dictionary_path: "sigs.json"  # inline comment

early_stopping:
  level1_bytes: 4  # default value
)";

    auto result = ConfigManager::instance().load_yaml_string(yaml);
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.signature_dictionary_path, "sigs.json");
}

// ============================================================================
// File I/O Tests
// ============================================================================

TEST_F(ConfigTest, LoadJsonFile) {
    // Create a test JSON file
    std::ofstream file("test_config.json");
    file << R"({
        "signature_dictionary_path": "file_test.json",
        "output": {
            "top_n_results": 5
        }
    })";
    file.close();

    auto result = ConfigManager::instance().load_json("test_config.json");
    EXPECT_TRUE(result.success) << result.message;

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.signature_dictionary_path, "file_test.json");
    EXPECT_EQ(config.output.top_n_results, 5u);
}

TEST_F(ConfigTest, LoadJsonFile_NotFound) {
    auto result = ConfigManager::instance().load_json("nonexistent.json");
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::FILE_NOT_FOUND);
}

TEST_F(ConfigTest, SaveAndLoadJson) {
    // Set custom config
    EtbConfig config;
    config.signature_dictionary_path = "saved_test.json";
    config.output.top_n_results = 42;
    config.entropy_min = 0.2f;
    ConfigManager::instance().set_config(config);

    // Save to file
    auto save_result = ConfigManager::instance().save_json("test_config.json");
    EXPECT_TRUE(save_result.success);

    // Reset and reload
    ConfigManager::instance().reset_to_defaults();
    auto load_result = ConfigManager::instance().load_json("test_config.json");
    EXPECT_TRUE(load_result.success);

    // Verify
    auto loaded = ConfigManager::instance().get_config();
    EXPECT_EQ(loaded.signature_dictionary_path, "saved_test.json");
    EXPECT_EQ(loaded.output.top_n_results, 42u);
    EXPECT_FLOAT_EQ(loaded.entropy_min, 0.2f);
}

// ============================================================================
// Runtime Update Tests
// ============================================================================

TEST_F(ConfigTest, UpdateValue_EarlyStopping) {
    auto result = ConfigManager::instance().update_value("early_stopping.level1_threshold", "0.5");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_FLOAT_EQ(config.early_stopping.level1_threshold, 0.5f);
}

TEST_F(ConfigTest, UpdateValue_EntropyThresholds) {
    auto result = ConfigManager::instance().update_value("entropy_thresholds.min", "0.3");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_FLOAT_EQ(config.entropy_min, 0.3f);
}

TEST_F(ConfigTest, UpdateValue_Memoization) {
    auto result = ConfigManager::instance().update_value("memoization.enabled", "false");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_FALSE(config.memoization.enabled);
}

TEST_F(ConfigTest, UpdateValue_InvalidKey) {
    auto result = ConfigManager::instance().update_value("invalid.key", "value");
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::INVALID_VALUE);
}

TEST_F(ConfigTest, UpdateValue_InvalidValue) {
    auto result = ConfigManager::instance().update_value("early_stopping.level1_threshold", "not_a_number");
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::PARSE_ERROR);
}

TEST_F(ConfigTest, UpdateValue_SignatureDictionaryPath) {
    auto result = ConfigManager::instance().update_value("signature_dictionary_path", "new_signatures.json");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.signature_dictionary_path, "new_signatures.json");
}

TEST_F(ConfigTest, UpdateValue_Performance) {
    auto result = ConfigManager::instance().update_value("performance.batch_size", "262144");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.performance.batch_size, 262144u);
}

TEST_F(ConfigTest, UpdateValue_Heuristics) {
    auto result = ConfigManager::instance().update_value("heuristics.min_printable_ratio", "0.85");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_FLOAT_EQ(config.min_printable_ratio, 0.85f);
}

TEST_F(ConfigTest, UpdateValue_Output) {
    auto result = ConfigManager::instance().update_value("output.save_partials", "true");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_TRUE(config.output.save_partials);
}

// ============================================================================
// Callback Tests
// ============================================================================

TEST_F(ConfigTest, ChangeCallback) {
    bool callback_called = false;
    EtbConfig received_config;

    auto id = ConfigManager::instance().register_change_callback(
        [&](const EtbConfig& config) {
            callback_called = true;
            received_config = config;
        });

    // Trigger a change
    EtbConfig new_config;
    new_config.output.top_n_results = 99;
    ConfigManager::instance().set_config(new_config);

    EXPECT_TRUE(callback_called);
    EXPECT_EQ(received_config.output.top_n_results, 99u);

    // Unregister and verify no more calls
    ConfigManager::instance().unregister_change_callback(id);
    callback_called = false;

    new_config.output.top_n_results = 100;
    ConfigManager::instance().set_config(new_config);

    EXPECT_FALSE(callback_called);
}

// ============================================================================
// Serialization Tests
// ============================================================================

TEST_F(ConfigTest, ToJsonString) {
    auto json = ConfigManager::instance().to_json_string();
    EXPECT_FALSE(json.empty());
    EXPECT_NE(json.find("signature_dictionary_path"), std::string::npos);
    EXPECT_NE(json.find("early_stopping"), std::string::npos);
    EXPECT_NE(json.find("entropy_thresholds"), std::string::npos);
}

TEST_F(ConfigTest, ToYamlString) {
    auto yaml = ConfigManager::instance().to_yaml_string();
    EXPECT_FALSE(yaml.empty());
    EXPECT_NE(yaml.find("signature_dictionary_path:"), std::string::npos);
    EXPECT_NE(yaml.find("early_stopping:"), std::string::npos);
}

// ============================================================================
// Helper Function Tests
// ============================================================================

TEST_F(ConfigTest, LoadConfigAutoDetect_Json) {
    std::ofstream file("test_config.json");
    file << R"({"output": {"top_n_results": 15}})";
    file.close();

    auto result = load_config("test_config.json");
    EXPECT_TRUE(result.success);

    auto config = ConfigManager::instance().get_config();
    EXPECT_EQ(config.output.top_n_results, 15u);
}

TEST_F(ConfigTest, GetDefaultConfig) {
    auto config = get_default_config();
    EXPECT_EQ(config.early_stopping.level1_bytes, 4u);
    EXPECT_EQ(config.early_stopping.level2_bytes, 8u);
    EXPECT_EQ(config.early_stopping.level3_bytes, 16u);
    EXPECT_FLOAT_EQ(config.entropy_min, 0.1f);
    EXPECT_FLOAT_EQ(config.entropy_max, 7.9f);
}

// ============================================================================
// Reload Tests
// ============================================================================

TEST_F(ConfigTest, Reload) {
    // Create initial config file
    std::ofstream file("test_config.json");
    file << R"({"output": {"top_n_results": 10}})";
    file.close();

    auto result = ConfigManager::instance().load_json("test_config.json");
    EXPECT_TRUE(result.success);
    EXPECT_EQ(ConfigManager::instance().get_config().output.top_n_results, 10u);

    // Modify the file
    std::ofstream file2("test_config.json");
    file2 << R"({"output": {"top_n_results": 25}})";
    file2.close();

    // Reload
    result = ConfigManager::instance().reload();
    EXPECT_TRUE(result.success);
    EXPECT_EQ(ConfigManager::instance().get_config().output.top_n_results, 25u);
}

TEST_F(ConfigTest, ReloadWithoutLoad) {
    auto result = ConfigManager::instance().reload();
    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.error, ConfigError::FILE_NOT_FOUND);
}
