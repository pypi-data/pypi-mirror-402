#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/numpy.h>

// Core headers
#include "etb/bit_coordinate.hpp"
#include "etb/path.hpp"
#include "etb/bit_extraction.hpp"
#include "etb/path_generator.hpp"
#include "etb/path_count.hpp"

// Signature and heuristics
#include "etb/signature.hpp"
#include "etb/heuristics.hpp"

// Pruning and optimization
#include "etb/early_stopping.hpp"
#include "etb/prefix_trie.hpp"
#include "etb/memoization.hpp"
#include "etb/bit_pruning.hpp"

// Scoring and configuration
#include "etb/scoring.hpp"
#include "etb/config.hpp"

// Reporting
#include "etb/reporting.hpp"

#include <fstream>
#include <sstream>

namespace py = pybind11;

// Helper to convert Python bytes to std::vector<uint8_t>
std::vector<uint8_t> bytes_to_vector(const py::bytes& data) {
    std::string str = data;
    return std::vector<uint8_t>(str.begin(), str.end());
}

// Helper to convert std::vector<uint8_t> to Python bytes
py::bytes vector_to_bytes(const std::vector<uint8_t>& data) {
    return py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
}

// Helper to read file contents
std::vector<uint8_t> read_file_bytes(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }
    return std::vector<uint8_t>(
        std::istreambuf_iterator<char>(file),
        std::istreambuf_iterator<char>()
    );
}

PYBIND11_MODULE(_etb, m) {
    m.doc() = "ExplodeThoseBits (etb) - CUDA-accelerated bit extraction library for forensic analysis";

    // ========================================================================
    // Core Data Structures
    // ========================================================================

    // BitCoordinate binding
    py::class_<etb::BitCoordinate>(m, "BitCoordinate",
        "Represents a coordinate in the bit extraction space (byte_index, bit_position)")
        .def(py::init<>())
        .def(py::init<uint32_t, uint8_t>(), py::arg("byte_index"), py::arg("bit_position"))
        .def_readwrite("byte_index", &etb::BitCoordinate::byte_index,
            "Index into the input byte array")
        .def_readwrite("bit_position", &etb::BitCoordinate::bit_position,
            "Position within the byte [0-7], 0 = LSB")
        .def("is_valid", &etb::BitCoordinate::is_valid, py::arg("input_length"),
            "Check if coordinate is valid for given input length")
        .def("__eq__", &etb::BitCoordinate::operator==)
        .def("__ne__", &etb::BitCoordinate::operator!=)
        .def("__lt__", &etb::BitCoordinate::operator<)
        .def("__repr__", [](const etb::BitCoordinate& c) {
            return "BitCoordinate(byte_index=" + std::to_string(c.byte_index) + 
                   ", bit_position=" + std::to_string(c.bit_position) + ")";
        });

    // Path binding
    py::class_<etb::Path>(m, "Path",
        "A forward-only traversal sequence of bit coordinates")
        .def(py::init<>())
        .def(py::init<size_t>(), py::arg("capacity"))
        .def("add", &etb::Path::add, py::arg("coord"),
            "Add a coordinate to the path")
        .def("is_valid", &etb::Path::is_valid,
            "Check if path maintains forward-only constraint")
        .def("length", &etb::Path::length,
            "Get the number of coordinates in the path")
        .def("empty", &etb::Path::empty,
            "Check if path is empty")
        .def("clear", &etb::Path::clear,
            "Clear all coordinates from the path")
        .def("reserve", &etb::Path::reserve, py::arg("capacity"),
            "Reserve capacity for coordinates")
        .def("at", &etb::Path::at, py::arg("index"),
            "Get coordinate at index")
        .def("back", &etb::Path::back,
            "Get the last coordinate")
        .def("__getitem__", &etb::Path::at)
        .def("__len__", &etb::Path::length)
        .def("__iter__", [](const etb::Path& p) {
            return py::make_iterator(p.begin(), p.end());
        }, py::keep_alive<0, 1>())
        .def("__repr__", [](const etb::Path& p) {
            return "Path(length=" + std::to_string(p.length()) + ")";
        });

    // ========================================================================
    // Bit Extraction Functions
    // ========================================================================

    m.def("extract_bit", 
        [](const py::bytes& data, const etb::BitCoordinate& coord) {
            auto vec = bytes_to_vector(data);
            return etb::extract_bit(vec, coord);
        },
        py::arg("data"), py::arg("coord"),
        "Extract a single bit from byte data at the given coordinate");

    m.def("extract_bits_from_path",
        [](const py::bytes& data, const etb::Path& path) {
            auto vec = bytes_to_vector(data);
            return etb::extract_bits_from_path(vec, path);
        },
        py::arg("data"), py::arg("path"),
        "Extract bits at specified path coordinates from byte data");

    m.def("bits_to_bytes",
        [](const std::vector<uint8_t>& bits) {
            auto result = etb::bits_to_bytes(bits);
            return vector_to_bytes(result);
        },
        py::arg("bits"),
        "Convert a sequence of bits to a byte array");

    m.def("path_to_bytes",
        [](const py::bytes& source_data, const etb::Path& path) {
            auto vec = bytes_to_vector(source_data);
            auto result = etb::path_to_bytes(vec, path);
            return vector_to_bytes(result);
        },
        py::arg("source_data"), py::arg("path"),
        "Convert a path with associated bit values to a byte array");

    m.def("bytes_to_bits",
        [](const py::bytes& data) {
            auto vec = bytes_to_vector(data);
            return etb::bytes_to_bits(vec);
        },
        py::arg("data"),
        "Convert a byte array to a sequence of bits");

    // ========================================================================
    // Path Generation
    // ========================================================================

    // PathGeneratorConfig
    py::class_<etb::PathGeneratorConfig>(m, "PathGeneratorConfig",
        "Configuration for the path generator")
        .def(py::init<uint32_t>(), py::arg("input_length"))
        .def_readwrite("input_length", &etb::PathGeneratorConfig::input_length)
        .def_readwrite("max_path_length", &etb::PathGeneratorConfig::max_path_length)
        .def_readwrite("starting_byte_index", &etb::PathGeneratorConfig::starting_byte_index)
        .def_readwrite("bit_mask", &etb::PathGeneratorConfig::bit_mask);

    // PathGenerator
    py::class_<etb::PathGenerator>(m, "PathGenerator",
        "Lazy path generator using iterator pattern")
        .def(py::init<uint32_t>(), py::arg("input_length"))
        .def(py::init<const etb::PathGeneratorConfig&>(), py::arg("config"))
        .def("has_next", &etb::PathGenerator::has_next,
            "Check if there are more paths to generate")
        .def("next", &etb::PathGenerator::next,
            "Generate the next path")
        .def("reset", &etb::PathGenerator::reset,
            "Reset the generator to start from the beginning")
        .def("paths_generated", &etb::PathGenerator::paths_generated,
            "Get the number of paths generated so far")
        .def("__iter__", [](etb::PathGenerator& gen) -> etb::PathGenerator& {
            return gen;
        })
        .def("__next__", [](etb::PathGenerator& gen) {
            auto path = gen.next();
            if (!path) {
                throw py::stop_iteration();
            }
            return *path;
        });

    // Path count functions
    py::class_<etb::PathCountResult>(m, "PathCountResult",
        "Result of path count estimation")
        .def_readonly("estimated_count", &etb::PathCountResult::estimated_count)
        .def_readonly("is_exact", &etb::PathCountResult::is_exact)
        .def_readonly("exceeds_threshold", &etb::PathCountResult::exceeds_threshold)
        .def_readonly("log_count", &etb::PathCountResult::log_count);

    m.def("estimate_path_count", &etb::estimate_path_count,
        py::arg("input_length"), py::arg("bits_per_byte") = 8, py::arg("threshold") = 0,
        "Estimate the path count with overflow detection");

    m.def("path_count_exceeds_threshold", &etb::path_count_exceeds_threshold,
        py::arg("input_length"), py::arg("bits_per_byte"), py::arg("threshold"),
        "Check if path count exceeds a threshold");

    // ========================================================================
    // Signature Detection
    // ========================================================================

    // FileSignature
    py::class_<etb::FileSignature>(m, "FileSignature",
        "Represents a single file signature (magic bytes)")
        .def(py::init<>())
        .def_readwrite("magic_bytes", &etb::FileSignature::magic_bytes)
        .def_readwrite("mask", &etb::FileSignature::mask)
        .def_readwrite("offset", &etb::FileSignature::offset)
        .def_readwrite("base_confidence", &etb::FileSignature::base_confidence);

    // FooterSignature
    py::class_<etb::FooterSignature>(m, "FooterSignature",
        "Represents a footer/trailer signature for a format")
        .def(py::init<>())
        .def_readwrite("magic_bytes", &etb::FooterSignature::magic_bytes)
        .def_readwrite("required", &etb::FooterSignature::required);

    // FormatDefinition
    py::class_<etb::FormatDefinition>(m, "FormatDefinition",
        "Represents a complete format definition with all its signatures")
        .def(py::init<>())
        .def_readwrite("format_name", &etb::FormatDefinition::format_name)
        .def_readwrite("category", &etb::FormatDefinition::category)
        .def_readwrite("signatures", &etb::FormatDefinition::signatures)
        .def_readwrite("format_id", &etb::FormatDefinition::format_id);

    // SignatureMatch
    py::class_<etb::SignatureMatch>(m, "SignatureMatch",
        "Result of a signature match operation")
        .def(py::init<>())
        .def_readonly("matched", &etb::SignatureMatch::matched)
        .def_readonly("format_name", &etb::SignatureMatch::format_name)
        .def_readonly("category", &etb::SignatureMatch::category)
        .def_readonly("format_id", &etb::SignatureMatch::format_id)
        .def_readonly("confidence", &etb::SignatureMatch::confidence)
        .def_readonly("match_offset", &etb::SignatureMatch::match_offset)
        .def_readonly("header_matched", &etb::SignatureMatch::header_matched)
        .def_readonly("footer_matched", &etb::SignatureMatch::footer_matched)
        .def("__repr__", [](const etb::SignatureMatch& m) {
            if (!m.matched) return std::string("SignatureMatch(matched=False)");
            return "SignatureMatch(format=" + m.format_name + 
                   ", confidence=" + std::to_string(m.confidence) + ")";
        });

    // SignatureDictionary
    py::class_<etb::SignatureDictionary>(m, "SignatureDictionary",
        "Signature dictionary that loads and manages file signatures")
        .def(py::init<>())
        .def("load_from_json", &etb::SignatureDictionary::load_from_json,
            py::arg("filepath"),
            "Load signatures from a JSON file")
        .def("load_from_json_string", &etb::SignatureDictionary::load_from_json_string,
            py::arg("json_content"),
            "Load signatures from a JSON string")
        .def("add_format", &etb::SignatureDictionary::add_format,
            py::arg("format"),
            "Add a format definition programmatically")
        .def("get_formats", &etb::SignatureDictionary::get_formats,
            "Get all loaded format definitions")
        .def("format_count", &etb::SignatureDictionary::format_count,
            "Get the number of loaded formats")
        .def("clear", &etb::SignatureDictionary::clear,
            "Clear all loaded signatures")
        .def("empty", &etb::SignatureDictionary::empty,
            "Check if dictionary is empty");

    // SignatureMatcher
    py::class_<etb::SignatureMatcher>(m, "SignatureMatcher",
        "Signature matcher that performs header and footer detection")
        .def(py::init<const etb::SignatureDictionary&>(), py::arg("dictionary"))
        .def("match",
            [](const etb::SignatureMatcher& matcher, const py::bytes& data, size_t max_offset) {
                auto vec = bytes_to_vector(data);
                return matcher.match(vec, max_offset);
            },
            py::arg("data"), py::arg("max_offset") = 512,
            "Match signatures against a byte sequence");

    // ========================================================================
    // Heuristics Engine
    // ========================================================================

    // HeuristicResult
    py::class_<etb::HeuristicResult>(m, "HeuristicResult",
        "Result of heuristic analysis on a byte sequence")
        .def(py::init<>())
        .def_readwrite("entropy", &etb::HeuristicResult::entropy,
            "Shannon entropy [0.0, 8.0]")
        .def_readwrite("printable_ratio", &etb::HeuristicResult::printable_ratio,
            "Ratio of printable ASCII [0.0, 1.0]")
        .def_readwrite("control_char_ratio", &etb::HeuristicResult::control_char_ratio,
            "Ratio of control characters [0.0, 1.0]")
        .def_readwrite("max_null_run", &etb::HeuristicResult::max_null_run,
            "Longest consecutive null byte run")
        .def_readwrite("utf8_validity", &etb::HeuristicResult::utf8_validity,
            "UTF-8 sequence validity score [0.0, 1.0]")
        .def_readwrite("composite_score", &etb::HeuristicResult::composite_score,
            "Weighted combination [0.0, 1.0]")
        .def("__repr__", [](const etb::HeuristicResult& r) {
            return "HeuristicResult(entropy=" + std::to_string(r.entropy) +
                   ", printable_ratio=" + std::to_string(r.printable_ratio) +
                   ", composite_score=" + std::to_string(r.composite_score) + ")";
        });

    // HeuristicWeights
    py::class_<etb::HeuristicWeights>(m, "HeuristicWeights",
        "Configurable weights for composite heuristic scoring")
        .def(py::init<>())
        .def_readwrite("entropy_weight", &etb::HeuristicWeights::entropy_weight)
        .def_readwrite("printable_weight", &etb::HeuristicWeights::printable_weight)
        .def_readwrite("control_char_weight", &etb::HeuristicWeights::control_char_weight)
        .def_readwrite("null_run_weight", &etb::HeuristicWeights::null_run_weight)
        .def_readwrite("utf8_weight", &etb::HeuristicWeights::utf8_weight);

    // HeuristicsEngine
    py::class_<etb::HeuristicsEngine>(m, "HeuristicsEngine",
        "Heuristics Engine for analyzing byte sequences")
        .def(py::init<>())
        .def(py::init<const etb::HeuristicWeights&>(), py::arg("weights"))
        .def("set_weights", &etb::HeuristicsEngine::set_weights, py::arg("weights"))
        .def("get_weights", &etb::HeuristicsEngine::get_weights)
        .def("analyze",
            [](const etb::HeuristicsEngine& engine, const py::bytes& data) {
                auto vec = bytes_to_vector(data);
                return engine.analyze(vec);
            },
            py::arg("data"),
            "Perform full heuristic analysis on byte data")
        .def_static("calculate_entropy",
            [](const py::bytes& data) {
                auto vec = bytes_to_vector(data);
                return etb::HeuristicsEngine::calculate_entropy(vec);
            },
            py::arg("data"),
            "Calculate Shannon entropy of byte data")
        .def_static("calculate_printable_ratio",
            [](const py::bytes& data) {
                auto vec = bytes_to_vector(data);
                return etb::HeuristicsEngine::calculate_printable_ratio(vec.data(), vec.size());
            },
            py::arg("data"),
            "Calculate the ratio of printable ASCII characters")
        .def_static("validate_utf8",
            [](const py::bytes& data) {
                auto vec = bytes_to_vector(data);
                return etb::HeuristicsEngine::validate_utf8(vec.data(), vec.size());
            },
            py::arg("data"),
            "Validate UTF-8 sequences and return a validity score");

    // ========================================================================
    // Early Stopping
    // ========================================================================

    // StopLevel enum
    py::enum_<etb::StopLevel>(m, "StopLevel",
        "Stop levels for multi-level early stopping")
        .value("LEVEL_1", etb::StopLevel::LEVEL_1, "2-4 bytes: signature prefix + basic heuristics")
        .value("LEVEL_2", etb::StopLevel::LEVEL_2, "8 bytes: entropy bounds + checksum validation")
        .value("LEVEL_3", etb::StopLevel::LEVEL_3, "16 bytes: structural coherence");

    // StopDecision
    py::class_<etb::StopDecision>(m, "StopDecision",
        "Result of an early stopping check")
        .def(py::init<>())
        .def_readonly("should_stop", &etb::StopDecision::should_stop)
        .def_readonly("level", &etb::StopDecision::level)
        .def_readonly("score", &etb::StopDecision::score)
        .def_property_readonly("reason", [](const etb::StopDecision& d) {
            return d.reason ? std::string(d.reason) : std::string();
        });

    // EarlyStoppingConfig
    py::class_<etb::EarlyStoppingConfig>(m, "EarlyStoppingConfig",
        "Configuration for early stopping thresholds")
        .def(py::init<>())
        .def_readwrite("level1_bytes", &etb::EarlyStoppingConfig::level1_bytes)
        .def_readwrite("level2_bytes", &etb::EarlyStoppingConfig::level2_bytes)
        .def_readwrite("level3_bytes", &etb::EarlyStoppingConfig::level3_bytes)
        .def_readwrite("min_entropy", &etb::EarlyStoppingConfig::min_entropy)
        .def_readwrite("max_entropy", &etb::EarlyStoppingConfig::max_entropy)
        .def_readwrite("level1_threshold", &etb::EarlyStoppingConfig::level1_threshold)
        .def_readwrite("level2_threshold", &etb::EarlyStoppingConfig::level2_threshold)
        .def_readwrite("level3_threshold", &etb::EarlyStoppingConfig::level3_threshold)
        .def_readwrite("adaptive_thresholds", &etb::EarlyStoppingConfig::adaptive_thresholds);

    // EarlyStoppingController
    py::class_<etb::EarlyStoppingController>(m, "EarlyStoppingController",
        "Early Stopping Controller for reducing search space")
        .def(py::init<>())
        .def(py::init<const etb::EarlyStoppingConfig&>(), py::arg("config"))
        .def("should_stop",
            [](const etb::EarlyStoppingController& ctrl, const py::bytes& data) {
                auto vec = bytes_to_vector(data);
                return ctrl.should_stop(vec);
            },
            py::arg("data"),
            "Check if a path should be stopped at the current depth")
        .def("update_best_score", &etb::EarlyStoppingController::update_best_score,
            py::arg("score"))
        .def("get_adaptive_threshold", &etb::EarlyStoppingController::get_adaptive_threshold)
        .def_static("is_repeated_byte_pattern",
            [](const py::bytes& data) {
                auto vec = bytes_to_vector(data);
                return etb::EarlyStoppingController::is_repeated_byte_pattern(vec.data(), vec.size());
            },
            py::arg("data"))
        .def_static("is_all_null",
            [](const py::bytes& data) {
                auto vec = bytes_to_vector(data);
                return etb::EarlyStoppingController::is_all_null(vec.data(), vec.size());
            },
            py::arg("data"));

    // ========================================================================
    // Prefix Trie
    // ========================================================================

    // PrefixStatus enum
    py::enum_<etb::PrefixStatus>(m, "PrefixStatus",
        "Status of a prefix trie node")
        .value("UNKNOWN", etb::PrefixStatus::UNKNOWN, "Not yet evaluated")
        .value("VALID", etb::PrefixStatus::VALID, "Prefix passed heuristics")
        .value("PRUNED", etb::PrefixStatus::PRUNED, "Prefix failed heuristics");

    // PrefixTrieConfig
    py::class_<etb::PrefixTrieConfig>(m, "PrefixTrieConfig",
        "Configuration for the prefix trie")
        .def(py::init<>())
        .def_readwrite("max_depth", &etb::PrefixTrieConfig::max_depth)
        .def_readwrite("initial_capacity", &etb::PrefixTrieConfig::initial_capacity)
        .def_readwrite("prune_threshold", &etb::PrefixTrieConfig::prune_threshold)
        .def_readwrite("branch_prune_count", &etb::PrefixTrieConfig::branch_prune_count);

    // PrefixTrieStats
    py::class_<etb::PrefixTrieStats>(m, "PrefixTrieStats",
        "Statistics for prefix trie operations")
        .def(py::init<>())
        .def_readonly("total_lookups", &etb::PrefixTrieStats::total_lookups)
        .def_readonly("cache_hits", &etb::PrefixTrieStats::cache_hits)
        .def_readonly("nodes_created", &etb::PrefixTrieStats::nodes_created)
        .def_readonly("nodes_pruned", &etb::PrefixTrieStats::nodes_pruned)
        .def_readonly("children_eliminated", &etb::PrefixTrieStats::children_eliminated);

    // PrefixTrie
    py::class_<etb::PrefixTrie>(m, "PrefixTrie",
        "GPU-compatible trie for O(1) prefix lookup and pruning")
        .def(py::init<>())
        .def(py::init<const etb::PrefixTrieConfig&>(), py::arg("config"))
        .def("lookup",
            [](const etb::PrefixTrie& trie, const py::bytes& prefix) -> py::object {
                auto vec = bytes_to_vector(prefix);
                auto node = trie.lookup(vec);
                if (!node) return py::none();
                return py::cast(*node);
            },
            py::arg("prefix"),
            "Look up a prefix in the trie")
        .def("insert",
            [](etb::PrefixTrie& trie, const py::bytes& prefix, etb::PrefixStatus status, float score) {
                auto vec = bytes_to_vector(prefix);
                return trie.insert(vec, status, score);
            },
            py::arg("prefix"), py::arg("status"), py::arg("score"),
            "Insert or update a prefix in the trie")
        .def("prune",
            [](etb::PrefixTrie& trie, const py::bytes& prefix) {
                auto vec = bytes_to_vector(prefix);
                return trie.prune(vec);
            },
            py::arg("prefix"),
            "Mark a prefix as pruned and eliminate all children")
        .def("is_pruned",
            [](const etb::PrefixTrie& trie, const py::bytes& prefix) {
                auto vec = bytes_to_vector(prefix);
                return trie.is_pruned(vec);
            },
            py::arg("prefix"),
            "Check if a prefix or any of its ancestors is pruned")
        .def("get_effective_branching_factor", &etb::PrefixTrie::get_effective_branching_factor)
        .def("node_count", &etb::PrefixTrie::node_count)
        .def("get_statistics", &etb::PrefixTrie::get_statistics)
        .def("clear", &etb::PrefixTrie::clear);

    // ========================================================================
    // Memoization
    // ========================================================================

    // MemoizationConfig
    py::class_<etb::MemoizationConfig>(m, "MemoizationConfig",
        "Configuration for the memoization cache")
        .def(py::init<>())
        .def_readwrite("max_size_bytes", &etb::MemoizationConfig::max_size_bytes)
        .def_readwrite("max_entries", &etb::MemoizationConfig::max_entries)
        .def_readwrite("enabled", &etb::MemoizationConfig::enabled);

    // MemoizationStats
    py::class_<etb::MemoizationStats>(m, "MemoizationStats",
        "Statistics for cache operations")
        .def(py::init<>())
        .def_readonly("hits", &etb::MemoizationStats::hits)
        .def_readonly("misses", &etb::MemoizationStats::misses)
        .def_readonly("insertions", &etb::MemoizationStats::insertions)
        .def_readonly("evictions", &etb::MemoizationStats::evictions)
        .def_readonly("current_entries", &etb::MemoizationStats::current_entries)
        .def_readonly("current_size_bytes", &etb::MemoizationStats::current_size_bytes)
        .def("hit_rate", &etb::MemoizationStats::hit_rate);

    // PrefixCacheEntry
    py::class_<etb::PrefixCacheEntry>(m, "PrefixCacheEntry",
        "Result stored in the prefix cache")
        .def(py::init<>())
        .def_readonly("heuristics", &etb::PrefixCacheEntry::heuristics)
        .def_readonly("score", &etb::PrefixCacheEntry::score)
        .def_readonly("should_prune", &etb::PrefixCacheEntry::should_prune)
        .def_readonly("access_count", &etb::PrefixCacheEntry::access_count);

    // PrefixCache
    py::class_<etb::PrefixCache>(m, "PrefixCache",
        "Prefix Result Cache with LRU Eviction")
        .def(py::init<>())
        .def(py::init<const etb::MemoizationConfig&>(), py::arg("config"))
        .def("lookup",
            [](etb::PrefixCache& cache, const py::bytes& prefix) -> py::object {
                auto vec = bytes_to_vector(prefix);
                auto entry = cache.lookup(vec);
                if (!entry) return py::none();
                return py::cast(*entry);
            },
            py::arg("prefix"),
            "Look up a prefix in the cache")
        .def("insert",
            [](etb::PrefixCache& cache, const py::bytes& prefix,
               const etb::HeuristicResult& heuristics, float score, bool should_prune) {
                auto vec = bytes_to_vector(prefix);
                return cache.insert(vec, heuristics, score, should_prune);
            },
            py::arg("prefix"), py::arg("heuristics"), py::arg("score"), py::arg("should_prune"),
            "Insert or update a prefix result in the cache")
        .def("contains",
            [](const etb::PrefixCache& cache, const py::bytes& prefix) {
                auto vec = bytes_to_vector(prefix);
                return cache.contains(vec);
            },
            py::arg("prefix"))
        .def("size", &etb::PrefixCache::size)
        .def("empty", &etb::PrefixCache::empty)
        .def("clear", &etb::PrefixCache::clear)
        .def("hit_rate", &etb::PrefixCache::hit_rate)
        .def("get_statistics", &etb::PrefixCache::get_statistics)
        .def("set_enabled", &etb::PrefixCache::set_enabled, py::arg("enabled"))
        .def("is_enabled", &etb::PrefixCache::is_enabled);

    // ========================================================================
    // Bit Pruning
    // ========================================================================

    // BitPruningMode enum
    py::enum_<etb::BitPruningMode>(m, "BitPruningMode",
        "Bit pruning modes that control which bit positions are explored")
        .value("EXHAUSTIVE", etb::BitPruningMode::EXHAUSTIVE, "All 8 bit positions (O(8^d))")
        .value("MSB_ONLY", etb::BitPruningMode::MSB_ONLY, "Only bits 4-7 (O(4^d))")
        .value("SINGLE_BIT", etb::BitPruningMode::SINGLE_BIT, "Only 2 configured bit positions (O(2^d))")
        .value("CUSTOM", etb::BitPruningMode::CUSTOM, "User-defined bit mask");

    // BitPruningConfig
    py::class_<etb::BitPruningConfig>(m, "BitPruningConfig",
        "Configuration for the bit pruning system")
        .def(py::init<>())
        .def(py::init<etb::BitPruningMode>(), py::arg("mode"))
        .def(py::init<uint8_t>(), py::arg("custom_mask"))
        .def(py::init<uint8_t, uint8_t>(), py::arg("bit1"), py::arg("bit2"))
        .def_readwrite("mode", &etb::BitPruningConfig::mode)
        .def_readwrite("bit_mask", &etb::BitPruningConfig::bit_mask)
        .def("is_bit_allowed", &etb::BitPruningConfig::is_bit_allowed, py::arg("bit_pos"))
        .def("allowed_bit_count", &etb::BitPruningConfig::allowed_bit_count)
        .def("get_allowed_positions", &etb::BitPruningConfig::get_allowed_positions)
        .def("branching_factor", &etb::BitPruningConfig::branching_factor)
        .def("description", &etb::BitPruningConfig::description)
        .def("is_valid", &etb::BitPruningConfig::is_valid)
        .def("get_mask", &etb::BitPruningConfig::get_mask);

    // ========================================================================
    // Scoring System
    // ========================================================================

    // ScoringWeights
    py::class_<etb::ScoringWeights>(m, "ScoringWeights",
        "Configurable weights for composite scoring")
        .def(py::init<>())
        .def_readwrite("signature_weight", &etb::ScoringWeights::signature_weight)
        .def_readwrite("heuristic_weight", &etb::ScoringWeights::heuristic_weight)
        .def_readwrite("length_weight", &etb::ScoringWeights::length_weight)
        .def_readwrite("structure_weight", &etb::ScoringWeights::structure_weight)
        .def("is_valid", &etb::ScoringWeights::is_valid)
        .def("normalize", &etb::ScoringWeights::normalize);

    // StructuralValidation
    py::class_<etb::StructuralValidation>(m, "StructuralValidation",
        "Structural validation result for a candidate")
        .def(py::init<>())
        .def_readwrite("validity_score", &etb::StructuralValidation::validity_score)
        .def_readwrite("has_valid_length", &etb::StructuralValidation::has_valid_length)
        .def_readwrite("has_valid_checksum", &etb::StructuralValidation::has_valid_checksum)
        .def_readwrite("has_valid_pointers", &etb::StructuralValidation::has_valid_pointers);

    // Candidate
    py::class_<etb::Candidate>(m, "Candidate",
        "A candidate reconstruction with all associated metadata")
        .def(py::init<>())
        .def_readwrite("path", &etb::Candidate::path)
        .def_readwrite("data", &etb::Candidate::data)
        .def_readwrite("format_id", &etb::Candidate::format_id)
        .def_readwrite("format_name", &etb::Candidate::format_name)
        .def_readwrite("confidence", &etb::Candidate::confidence)
        .def_readwrite("heuristics", &etb::Candidate::heuristics)
        .def_readwrite("signature_match", &etb::Candidate::signature_match)
        .def_readwrite("structure", &etb::Candidate::structure)
        .def_readwrite("composite_score", &etb::Candidate::composite_score)
        .def("get_data_bytes", [](const etb::Candidate& c) {
            return vector_to_bytes(c.data);
        }, "Get reconstructed data as Python bytes")
        .def("__repr__", [](const etb::Candidate& c) {
            return "Candidate(format=" + c.format_name + 
                   ", confidence=" + std::to_string(c.confidence) +
                   ", score=" + std::to_string(c.composite_score) + ")";
        });

    // ScoreCalculator
    py::class_<etb::ScoreCalculator>(m, "ScoreCalculator",
        "Composite score calculator")
        .def(py::init<>())
        .def(py::init<const etb::ScoringWeights&>(), py::arg("weights"))
        .def("set_weights", &etb::ScoreCalculator::set_weights, py::arg("weights"))
        .def("get_weights", &etb::ScoreCalculator::get_weights)
        .def("calculate",
            py::overload_cast<float, float, float, float>(&etb::ScoreCalculator::calculate, py::const_),
            py::arg("signature_score"), py::arg("heuristic_score"),
            py::arg("length_score"), py::arg("structure_score"),
            "Calculate composite score from component scores")
        .def("score_candidate", &etb::ScoreCalculator::score_candidate,
            py::arg("candidate"), py::arg("expected_length") = 0,
            "Calculate and populate a Candidate's composite score");

    // CandidateQueue
    py::class_<etb::CandidateQueue>(m, "CandidateQueue",
        "Priority queue for tracking top-K candidates")
        .def(py::init<size_t>(), py::arg("capacity") = 10)
        .def("push", py::overload_cast<const etb::Candidate&>(&etb::CandidateQueue::push),
            py::arg("candidate"),
            "Try to add a candidate to the queue")
        .def("top", &etb::CandidateQueue::top,
            "Get the top candidate (highest score)")
        .def("pop", &etb::CandidateQueue::pop,
            "Remove and return the top candidate")
        .def("get_top_k", &etb::CandidateQueue::get_top_k,
            "Get all candidates sorted by score (descending)")
        .def("min_score", &etb::CandidateQueue::min_score)
        .def("would_accept", &etb::CandidateQueue::would_accept, py::arg("score"))
        .def("size", &etb::CandidateQueue::size)
        .def("capacity", &etb::CandidateQueue::capacity)
        .def("empty", &etb::CandidateQueue::empty)
        .def("full", &etb::CandidateQueue::full)
        .def("clear", &etb::CandidateQueue::clear)
        .def("set_capacity", &etb::CandidateQueue::set_capacity, py::arg("new_capacity"));

    // ========================================================================
    // Configuration System
    // ========================================================================

    // ConfigError enum
    py::enum_<etb::ConfigError>(m, "ConfigError",
        "Error codes for configuration operations")
        .value("NONE", etb::ConfigError::NONE)
        .value("FILE_NOT_FOUND", etb::ConfigError::FILE_NOT_FOUND)
        .value("PARSE_ERROR", etb::ConfigError::PARSE_ERROR)
        .value("INVALID_VALUE", etb::ConfigError::INVALID_VALUE)
        .value("MISSING_REQUIRED_FIELD", etb::ConfigError::MISSING_REQUIRED_FIELD)
        .value("TYPE_MISMATCH", etb::ConfigError::TYPE_MISMATCH)
        .value("OUT_OF_RANGE", etb::ConfigError::OUT_OF_RANGE);

    // ConfigResult
    py::class_<etb::ConfigResult>(m, "ConfigResult",
        "Result of a configuration operation")
        .def(py::init<>())
        .def_readonly("success", &etb::ConfigResult::success)
        .def_readonly("error", &etb::ConfigResult::error)
        .def_readonly("message", &etb::ConfigResult::message)
        .def("__bool__", [](const etb::ConfigResult& r) { return r.success; })
        .def("__repr__", [](const etb::ConfigResult& r) {
            if (r.success) return std::string("ConfigResult(success=True)");
            return "ConfigResult(success=False, message=" + r.message + ")";
        });

    // OutputConfig
    py::class_<etb::OutputConfig>(m, "OutputConfig",
        "Output configuration options")
        .def(py::init<>())
        .def_readwrite("top_n_results", &etb::OutputConfig::top_n_results)
        .def_readwrite("save_partials", &etb::OutputConfig::save_partials)
        .def_readwrite("include_paths", &etb::OutputConfig::include_paths)
        .def_readwrite("metrics_verbosity", &etb::OutputConfig::metrics_verbosity);

    // PerformanceConfig
    py::class_<etb::PerformanceConfig>(m, "PerformanceConfig",
        "Performance configuration options")
        .def(py::init<>())
        .def_readwrite("max_parallel_workers", &etb::PerformanceConfig::max_parallel_workers)
        .def_readwrite("cuda_streams", &etb::PerformanceConfig::cuda_streams)
        .def_readwrite("batch_size", &etb::PerformanceConfig::batch_size);

    // EtbConfig
    py::class_<etb::EtbConfig>(m, "EtbConfig",
        "Complete configuration for the etb library")
        .def(py::init<>())
        .def_readwrite("signature_dictionary_path", &etb::EtbConfig::signature_dictionary_path)
        .def_readwrite("early_stopping", &etb::EtbConfig::early_stopping)
        .def_readwrite("heuristic_weights", &etb::EtbConfig::heuristic_weights)
        .def_readwrite("scoring_weights", &etb::EtbConfig::scoring_weights)
        .def_readwrite("bit_pruning", &etb::EtbConfig::bit_pruning)
        .def_readwrite("memoization", &etb::EtbConfig::memoization)
        .def_readwrite("output", &etb::EtbConfig::output)
        .def_readwrite("performance", &etb::EtbConfig::performance)
        .def_readwrite("entropy_min", &etb::EtbConfig::entropy_min)
        .def_readwrite("entropy_max", &etb::EtbConfig::entropy_max)
        .def_readwrite("min_printable_ratio", &etb::EtbConfig::min_printable_ratio)
        .def_readwrite("max_null_run", &etb::EtbConfig::max_null_run)
        .def("validate", &etb::EtbConfig::validate,
            "Validate the entire configuration");

    // ConfigManager (singleton access)
    py::class_<etb::ConfigManager, std::unique_ptr<etb::ConfigManager, py::nodelete>>(m, "ConfigManager",
        "Configuration loader and manager")
        .def_static("instance", &etb::ConfigManager::instance, py::return_value_policy::reference,
            "Get the singleton instance")
        .def("load_json", &etb::ConfigManager::load_json, py::arg("filepath"),
            "Load configuration from a JSON file")
        .def("load_json_string", &etb::ConfigManager::load_json_string, py::arg("json_content"),
            "Load configuration from a JSON string")
        .def("load_yaml", &etb::ConfigManager::load_yaml, py::arg("filepath"),
            "Load configuration from a YAML file")
        .def("load_yaml_string", &etb::ConfigManager::load_yaml_string, py::arg("yaml_content"),
            "Load configuration from a YAML string")
        .def("get_config", &etb::ConfigManager::get_config,
            "Get the current configuration")
        .def("set_config", &etb::ConfigManager::set_config, py::arg("config"),
            "Set the configuration")
        .def("update_value", &etb::ConfigManager::update_value,
            py::arg("key"), py::arg("value"),
            "Update a specific configuration value at runtime")
        .def("reload", &etb::ConfigManager::reload,
            "Reload configuration from the last loaded file")
        .def("is_loaded", &etb::ConfigManager::is_loaded)
        .def("get_loaded_path", &etb::ConfigManager::get_loaded_path)
        .def("reset_to_defaults", &etb::ConfigManager::reset_to_defaults)
        .def("save_json", &etb::ConfigManager::save_json, py::arg("filepath"))
        .def("save_yaml", &etb::ConfigManager::save_yaml, py::arg("filepath"))
        .def("to_json_string", &etb::ConfigManager::to_json_string)
        .def("to_yaml_string", &etb::ConfigManager::to_yaml_string);

    // Helper functions
    m.def("load_config", &etb::load_config, py::arg("filepath"),
        "Load configuration from file (auto-detects format)");
    m.def("get_default_config", &etb::get_default_config,
        "Get the default configuration");

    // ========================================================================
    // High-Level Extract Function
    // ========================================================================

    m.def("extract",
        [](const py::object& input,
           const etb::EtbConfig& config,
           size_t max_paths) -> std::vector<etb::Candidate> {
            
            std::vector<uint8_t> data;
            
            // Handle different input types
            if (py::isinstance<py::bytes>(input)) {
                data = bytes_to_vector(input.cast<py::bytes>());
            } else if (py::isinstance<py::str>(input)) {
                // Treat as file path
                std::string filepath = input.cast<std::string>();
                data = read_file_bytes(filepath);
            } else {
                throw std::runtime_error("Input must be bytes or a file path string");
            }
            
            if (data.empty()) {
                return {};
            }
            
            // Initialize components
            etb::SignatureDictionary dictionary;
            if (!config.signature_dictionary_path.empty()) {
                dictionary.load_from_json(config.signature_dictionary_path);
            }
            
            etb::SignatureMatcher matcher(dictionary);
            etb::HeuristicsEngine heuristics(config.heuristic_weights);
            etb::EarlyStoppingController early_stop(config.early_stopping, &dictionary);
            etb::ScoreCalculator scorer(config.scoring_weights);
            etb::CandidateQueue queue(config.output.top_n_results);
            etb::PrefixCache cache(config.memoization);
            
            // Create path generator with bit pruning
            etb::PathGeneratorConfig gen_config(static_cast<uint32_t>(data.size()));
            gen_config.apply_bit_pruning(config.bit_pruning);
            etb::PathGenerator generator(gen_config);
            
            size_t paths_evaluated = 0;
            
            // Generate and evaluate paths
            while (generator.has_next() && paths_evaluated < max_paths) {
                auto path_opt = generator.next();
                if (!path_opt) break;
                
                const auto& path = *path_opt;
                paths_evaluated++;
                
                // Extract bytes from path
                auto reconstructed = etb::path_to_bytes(data, path);
                
                // Check early stopping
                auto stop_decision = early_stop.should_stop(reconstructed);
                if (stop_decision.should_stop) {
                    continue;
                }
                
                // Analyze heuristics
                auto heuristic_result = heuristics.analyze(reconstructed);
                
                // Match signatures
                auto sig_match = matcher.match(reconstructed);
                
                // Create candidate
                etb::Candidate candidate;
                candidate.path = path;
                candidate.data = reconstructed;
                candidate.heuristics = heuristic_result;
                candidate.signature_match = sig_match;
                candidate.format_id = sig_match.format_id;
                candidate.format_name = sig_match.format_name;
                candidate.confidence = sig_match.confidence;
                
                // Score candidate
                scorer.score_candidate(candidate);
                
                // Add to queue
                queue.push(candidate);
                
                // Update adaptive threshold
                early_stop.update_best_score(candidate.composite_score);
            }
            
            return queue.get_top_k();
        },
        py::arg("input"),
        py::arg("config") = etb::EtbConfig(),
        py::arg("max_paths") = 1000000,
        R"doc(
Extract hidden data from input bytes using bit-level reconstruction.

Args:
    input: Input data as bytes or a file path string
    config: EtbConfig object with extraction parameters
    max_paths: Maximum number of paths to evaluate (default: 1,000,000)

Returns:
    List of Candidate objects sorted by score (highest first)

Example:
    >>> import etb
    >>> candidates = etb.extract(b'\x89PNG...', etb.EtbConfig())
    >>> for c in candidates:
    ...     print(f"{c.format_name}: {c.confidence:.2f}")
)doc");

    // ========================================================================
    // Reporting System
    // ========================================================================

    // ValidationReport
    py::class_<etb::ValidationReport>(m, "ValidationReport",
        "Validation report for a successful extraction")
        .def(py::init<>())
        .def_readwrite("signature_valid", &etb::ValidationReport::signature_valid)
        .def_readwrite("structure_valid", &etb::ValidationReport::structure_valid)
        .def_readwrite("heuristics_valid", &etb::ValidationReport::heuristics_valid)
        .def_readwrite("overall_validity", &etb::ValidationReport::overall_validity)
        .def_readwrite("validation_notes", &etb::ValidationReport::validation_notes)
        .def("__repr__", [](const etb::ValidationReport& r) {
            return "ValidationReport(validity=" + std::to_string(r.overall_validity) + ")";
        });

    // SuccessResult
    py::class_<etb::SuccessResult>(m, "SuccessResult",
        "Success result containing extracted data and metadata")
        .def(py::init<>())
        .def_readwrite("extracted_bytes", &etb::SuccessResult::extracted_bytes)
        .def_readwrite("detected_format", &etb::SuccessResult::detected_format)
        .def_readwrite("format_category", &etb::SuccessResult::format_category)
        .def_readwrite("confidence", &etb::SuccessResult::confidence)
        .def_readwrite("reconstruction_path", &etb::SuccessResult::reconstruction_path)
        .def_readwrite("validation", &etb::SuccessResult::validation)
        .def_readwrite("heuristics", &etb::SuccessResult::heuristics)
        .def_readwrite("signature_match", &etb::SuccessResult::signature_match)
        .def("get_data_bytes", [](const etb::SuccessResult& r) {
            return vector_to_bytes(r.extracted_bytes);
        }, "Get extracted data as Python bytes")
        .def("__repr__", [](const etb::SuccessResult& r) {
            return "SuccessResult(format=" + r.detected_format + 
                   ", confidence=" + std::to_string(r.confidence) + ")";
        });

    // PartialMatch
    py::class_<etb::PartialMatch>(m, "PartialMatch",
        "Partial match information for failed extractions")
        .def(py::init<>())
        .def_readwrite("partial_data", &etb::PartialMatch::partial_data)
        .def_readwrite("possible_format", &etb::PartialMatch::possible_format)
        .def_readwrite("partial_score", &etb::PartialMatch::partial_score)
        .def_readwrite("depth_reached", &etb::PartialMatch::depth_reached)
        .def_readwrite("failure_reason", &etb::PartialMatch::failure_reason);

    // ParameterSuggestion
    py::class_<etb::ParameterSuggestion>(m, "ParameterSuggestion",
        "Suggestion for parameter adjustment when extraction fails")
        .def(py::init<>())
        .def(py::init<const std::string&, const std::string&, const std::string&, const std::string&>(),
            py::arg("parameter_name"), py::arg("current_value"),
            py::arg("suggested_value"), py::arg("rationale"))
        .def_readwrite("parameter_name", &etb::ParameterSuggestion::parameter_name)
        .def_readwrite("current_value", &etb::ParameterSuggestion::current_value)
        .def_readwrite("suggested_value", &etb::ParameterSuggestion::suggested_value)
        .def_readwrite("rationale", &etb::ParameterSuggestion::rationale);

    // FailureResult
    py::class_<etb::FailureResult>(m, "FailureResult",
        "Failure result containing diagnostic information")
        .def(py::init<>())
        .def_readwrite("paths_explored", &etb::FailureResult::paths_explored)
        .def_readwrite("effective_depth_reached", &etb::FailureResult::effective_depth_reached)
        .def_readwrite("best_partials", &etb::FailureResult::best_partials)
        .def_readwrite("suggestions", &etb::FailureResult::suggestions)
        .def_readwrite("failure_summary", &etb::FailureResult::failure_summary)
        .def("__repr__", [](const etb::FailureResult& r) {
            return "FailureResult(paths_explored=" + std::to_string(r.paths_explored) + ")";
        });

    // ExtractionMetrics
    py::class_<etb::ExtractionMetrics>(m, "ExtractionMetrics",
        "Extraction metrics for reporting")
        .def(py::init<>())
        .def_readwrite("total_paths_possible", &etb::ExtractionMetrics::total_paths_possible)
        .def_readwrite("paths_evaluated", &etb::ExtractionMetrics::paths_evaluated)
        .def_readwrite("paths_pruned_level1", &etb::ExtractionMetrics::paths_pruned_level1)
        .def_readwrite("paths_pruned_level2", &etb::ExtractionMetrics::paths_pruned_level2)
        .def_readwrite("paths_pruned_level3", &etb::ExtractionMetrics::paths_pruned_level3)
        .def_readwrite("paths_pruned_prefix", &etb::ExtractionMetrics::paths_pruned_prefix)
        .def_readwrite("effective_branching_factor", &etb::ExtractionMetrics::effective_branching_factor)
        .def_readwrite("effective_depth", &etb::ExtractionMetrics::effective_depth)
        .def_readwrite("cache_hit_rate", &etb::ExtractionMetrics::cache_hit_rate)
        .def_readwrite("level1_prune_rate", &etb::ExtractionMetrics::level1_prune_rate)
        .def_readwrite("level2_prune_rate", &etb::ExtractionMetrics::level2_prune_rate)
        .def_readwrite("level3_prune_rate", &etb::ExtractionMetrics::level3_prune_rate)
        .def_readwrite("prefix_prune_rate", &etb::ExtractionMetrics::prefix_prune_rate)
        .def_readwrite("format_distribution", &etb::ExtractionMetrics::format_distribution)
        .def_readwrite("wall_clock_seconds", &etb::ExtractionMetrics::wall_clock_seconds)
        .def_readwrite("average_time_per_path_us", &etb::ExtractionMetrics::average_time_per_path_us)
        .def_readwrite("gpu_utilization", &etb::ExtractionMetrics::gpu_utilization)
        .def_readwrite("complexity_reduction", &etb::ExtractionMetrics::complexity_reduction);

    // ExtractionResult
    py::class_<etb::ExtractionResult>(m, "ExtractionResult",
        "Complete extraction result combining success/failure with metrics")
        .def(py::init<>())
        .def_readwrite("success", &etb::ExtractionResult::success)
        .def_readwrite("candidates", &etb::ExtractionResult::candidates)
        .def_readwrite("metrics", &etb::ExtractionResult::metrics)
        .def_property("failure",
            [](const etb::ExtractionResult& r) -> py::object {
                if (r.failure.has_value()) {
                    return py::cast(r.failure.value());
                }
                return py::none();
            },
            [](etb::ExtractionResult& r, const etb::FailureResult& f) {
                r.failure = f;
            })
        .def("__repr__", [](const etb::ExtractionResult& r) {
            return "ExtractionResult(success=" + std::string(r.success ? "True" : "False") +
                   ", candidates=" + std::to_string(r.candidates.size()) + ")";
        });

    // SuccessResultBuilder
    py::class_<etb::SuccessResultBuilder>(m, "SuccessResultBuilder",
        "Builder for success results")
        .def(py::init<>())
        .def("set_data", py::overload_cast<const std::vector<uint8_t>&>(&etb::SuccessResultBuilder::set_data),
            py::arg("data"))
        .def("set_format", &etb::SuccessResultBuilder::set_format,
            py::arg("format_name"), py::arg("category") = "")
        .def("set_confidence", &etb::SuccessResultBuilder::set_confidence, py::arg("confidence"))
        .def("set_path", py::overload_cast<const etb::Path&>(&etb::SuccessResultBuilder::set_path),
            py::arg("path"))
        .def("set_heuristics", &etb::SuccessResultBuilder::set_heuristics, py::arg("heuristics"))
        .def("set_signature_match", &etb::SuccessResultBuilder::set_signature_match, py::arg("match"))
        .def("set_structural_validation", &etb::SuccessResultBuilder::set_structural_validation,
            py::arg("structure"))
        .def("build_validation_report", &etb::SuccessResultBuilder::build_validation_report)
        .def("build", &etb::SuccessResultBuilder::build)
        .def_static("from_candidate", &etb::SuccessResultBuilder::from_candidate, py::arg("candidate"));

    // FailureResultBuilder
    py::class_<etb::FailureResultBuilder>(m, "FailureResultBuilder",
        "Builder for failure results")
        .def(py::init<>())
        .def("set_paths_explored", &etb::FailureResultBuilder::set_paths_explored, py::arg("count"))
        .def("set_effective_depth", &etb::FailureResultBuilder::set_effective_depth, py::arg("depth"))
        .def("add_partial_match", py::overload_cast<const etb::PartialMatch&>(
            &etb::FailureResultBuilder::add_partial_match), py::arg("partial"))
        .def("add_partial_from_candidate", &etb::FailureResultBuilder::add_partial_from_candidate,
            py::arg("candidate"), py::arg("failure_reason"))
        .def("add_suggestion", py::overload_cast<const etb::ParameterSuggestion&>(
            &etb::FailureResultBuilder::add_suggestion), py::arg("suggestion"))
        .def("generate_suggestions", &etb::FailureResultBuilder::generate_suggestions, py::arg("metrics"))
        .def("set_summary", &etb::FailureResultBuilder::set_summary, py::arg("summary"))
        .def("generate_summary", &etb::FailureResultBuilder::generate_summary)
        .def("build", &etb::FailureResultBuilder::build);

    // MetricsReporter
    py::class_<etb::MetricsReporter>(m, "MetricsReporter",
        "Metrics reporter for extraction results")
        .def(py::init<>())
        .def("set_total_paths_possible", &etb::MetricsReporter::set_total_paths_possible, py::arg("count"))
        .def("set_paths_evaluated", &etb::MetricsReporter::set_paths_evaluated, py::arg("count"))
        .def("set_paths_pruned_level1", &etb::MetricsReporter::set_paths_pruned_level1, py::arg("count"))
        .def("set_paths_pruned_level2", &etb::MetricsReporter::set_paths_pruned_level2, py::arg("count"))
        .def("set_paths_pruned_level3", &etb::MetricsReporter::set_paths_pruned_level3, py::arg("count"))
        .def("set_paths_pruned_prefix", &etb::MetricsReporter::set_paths_pruned_prefix, py::arg("count"))
        .def("set_effective_branching_factor", &etb::MetricsReporter::set_effective_branching_factor,
            py::arg("factor"))
        .def("set_effective_depth", &etb::MetricsReporter::set_effective_depth, py::arg("depth"))
        .def("set_cache_hit_rate", &etb::MetricsReporter::set_cache_hit_rate, py::arg("rate"))
        .def("add_format_detection", &etb::MetricsReporter::add_format_detection,
            py::arg("format"), py::arg("count") = 1)
        .def("set_wall_clock_time", &etb::MetricsReporter::set_wall_clock_time, py::arg("seconds"))
        .def("set_gpu_utilization", &etb::MetricsReporter::set_gpu_utilization, py::arg("utilization"))
        .def("calculate_derived_metrics", &etb::MetricsReporter::calculate_derived_metrics)
        .def("generate_complexity_reduction", &etb::MetricsReporter::generate_complexity_reduction,
            py::arg("input_length"))
        .def("build", &etb::MetricsReporter::build)
        .def("to_string", &etb::MetricsReporter::to_string, py::arg("verbosity") = "full");

    // ExtractionResultBuilder
    py::class_<etb::ExtractionResultBuilder>(m, "ExtractionResultBuilder",
        "Builder for complete extraction results")
        .def(py::init<>())
        .def("set_success", &etb::ExtractionResultBuilder::set_success, py::arg("success"))
        .def("add_candidate", py::overload_cast<const etb::SuccessResult&>(
            &etb::ExtractionResultBuilder::add_candidate), py::arg("result"))
        .def("add_candidates", &etb::ExtractionResultBuilder::add_candidates, py::arg("candidates"))
        .def("set_failure", py::overload_cast<const etb::FailureResult&>(
            &etb::ExtractionResultBuilder::set_failure), py::arg("failure"))
        .def("set_metrics", py::overload_cast<const etb::ExtractionMetrics&>(
            &etb::ExtractionResultBuilder::set_metrics), py::arg("metrics"))
        .def("build", &etb::ExtractionResultBuilder::build);

    // Utility functions
    m.def("format_path", &etb::format_path,
        py::arg("path"), py::arg("max_coords") = 10,
        "Format a path as a human-readable string");

    m.def("format_bytes_hex",
        [](const py::bytes& data, size_t max_bytes) {
            auto vec = bytes_to_vector(data);
            return etb::format_bytes_hex(vec, max_bytes);
        },
        py::arg("data"), py::arg("max_bytes") = 32,
        "Format bytes as a hex string");

    m.def("format_confidence", &etb::format_confidence,
        py::arg("confidence"),
        "Format a confidence score as a percentage string");

    m.def("format_duration", &etb::format_duration,
        py::arg("seconds"),
        "Format a duration in human-readable form");

    m.def("format_count", &etb::format_count,
        py::arg("count"),
        "Format a large number with appropriate suffix (K, M, B)");

    // ========================================================================
    // Module-level utilities
    // ========================================================================

    m.def("extract_from_file",
        [](const std::string& filepath,
           const etb::EtbConfig& config,
           size_t max_paths) -> std::vector<etb::Candidate> {
            auto data = read_file_bytes(filepath);
            return py::module_::import("etb").attr("extract")(
                vector_to_bytes(data), config, max_paths
            ).cast<std::vector<etb::Candidate>>();
        },
        py::arg("filepath"),
        py::arg("config") = etb::EtbConfig(),
        py::arg("max_paths") = 1000000,
        "Extract hidden data from a file");

    // Version info
    m.attr("__version__") = "0.1.0";
    m.attr("__author__") = "ETB Team";
}
