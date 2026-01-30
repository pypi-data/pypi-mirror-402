"""
Type stubs for the etb (ExplodeThoseBits) library.

ExplodeThoseBits is a CUDA-accelerated bit extraction library for forensic analysis.
"""

from typing import List, Optional, Tuple, Iterator, Union
from enum import Enum

__version__: str
__author__: str

# ============================================================================
# Core Data Structures
# ============================================================================

class BitCoordinate:
    """Represents a coordinate in the bit extraction space (byte_index, bit_position)."""
    
    byte_index: int
    """Index into the input byte array."""
    
    bit_position: int
    """Position within the byte [0-7], 0 = LSB."""
    
    def __init__(self, byte_index: int = 0, bit_position: int = 0) -> None: ...
    def is_valid(self, input_length: int) -> bool:
        """Check if coordinate is valid for given input length."""
        ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __lt__(self, other: "BitCoordinate") -> bool: ...
    def __repr__(self) -> str: ...


class Path:
    """A forward-only traversal sequence of bit coordinates."""
    
    def __init__(self, capacity: int = 0) -> None: ...
    def add(self, coord: BitCoordinate) -> None:
        """Add a coordinate to the path."""
        ...
    def is_valid(self) -> bool:
        """Check if path maintains forward-only constraint."""
        ...
    def length(self) -> int:
        """Get the number of coordinates in the path."""
        ...
    def empty(self) -> bool:
        """Check if path is empty."""
        ...
    def clear(self) -> None:
        """Clear all coordinates from the path."""
        ...
    def reserve(self, capacity: int) -> None:
        """Reserve capacity for coordinates."""
        ...
    def at(self, index: int) -> BitCoordinate:
        """Get coordinate at index."""
        ...
    def back(self) -> BitCoordinate:
        """Get the last coordinate."""
        ...
    def __getitem__(self, index: int) -> BitCoordinate: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[BitCoordinate]: ...
    def __repr__(self) -> str: ...


# ============================================================================
# Bit Extraction Functions
# ============================================================================

def extract_bit(data: bytes, coord: BitCoordinate) -> int:
    """Extract a single bit from byte data at the given coordinate."""
    ...

def extract_bits_from_path(data: bytes, path: Path) -> List[int]:
    """Extract bits at specified path coordinates from byte data."""
    ...

def bits_to_bytes(bits: List[int]) -> bytes:
    """Convert a sequence of bits to a byte array."""
    ...

def path_to_bytes(source_data: bytes, path: Path) -> bytes:
    """Convert a path with associated bit values to a byte array."""
    ...

def bytes_to_bits(data: bytes) -> List[int]:
    """Convert a byte array to a sequence of bits."""
    ...


# ============================================================================
# Path Generation
# ============================================================================

class PathGeneratorConfig:
    """Configuration for the path generator."""
    
    input_length: int
    max_path_length: int
    starting_byte_index: int
    bit_mask: int
    
    def __init__(self, input_length: int) -> None: ...


class PathGenerator:
    """Lazy path generator using iterator pattern."""
    
    def __init__(self, input_length_or_config: Union[int, PathGeneratorConfig]) -> None: ...
    def has_next(self) -> bool:
        """Check if there are more paths to generate."""
        ...
    def next(self) -> Optional[Path]:
        """Generate the next path."""
        ...
    def reset(self) -> None:
        """Reset the generator to start from the beginning."""
        ...
    def paths_generated(self) -> int:
        """Get the number of paths generated so far."""
        ...
    def __iter__(self) -> "PathGenerator": ...
    def __next__(self) -> Path: ...


class PathCountResult:
    """Result of path count estimation."""
    
    estimated_count: int
    is_exact: bool
    exceeds_threshold: bool
    log_count: float


def estimate_path_count(
    input_length: int,
    bits_per_byte: int = 8,
    threshold: int = 0
) -> PathCountResult:
    """Estimate the path count with overflow detection."""
    ...

def path_count_exceeds_threshold(
    input_length: int,
    bits_per_byte: int,
    threshold: int
) -> bool:
    """Check if path count exceeds a threshold."""
    ...


# ============================================================================
# Signature Detection
# ============================================================================

class FileSignature:
    """Represents a single file signature (magic bytes)."""
    
    magic_bytes: List[int]
    mask: List[int]
    offset: int
    base_confidence: float
    
    def __init__(self) -> None: ...


class FooterSignature:
    """Represents a footer/trailer signature for a format."""
    
    magic_bytes: List[int]
    required: bool
    
    def __init__(self) -> None: ...


class FormatDefinition:
    """Represents a complete format definition with all its signatures."""
    
    format_name: str
    category: str
    signatures: List[FileSignature]
    format_id: int
    
    def __init__(self) -> None: ...


class SignatureMatch:
    """Result of a signature match operation."""
    
    matched: bool
    format_name: str
    category: str
    format_id: int
    confidence: float
    match_offset: int
    header_matched: bool
    footer_matched: bool
    
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...


class SignatureDictionary:
    """Signature dictionary that loads and manages file signatures."""
    
    def __init__(self) -> None: ...
    def load_from_json(self, filepath: str) -> bool:
        """Load signatures from a JSON file."""
        ...
    def load_from_json_string(self, json_content: str) -> bool:
        """Load signatures from a JSON string."""
        ...
    def add_format(self, format: FormatDefinition) -> None:
        """Add a format definition programmatically."""
        ...
    def get_formats(self) -> List[FormatDefinition]:
        """Get all loaded format definitions."""
        ...
    def format_count(self) -> int:
        """Get the number of loaded formats."""
        ...
    def clear(self) -> None:
        """Clear all loaded signatures."""
        ...
    def empty(self) -> bool:
        """Check if dictionary is empty."""
        ...


class SignatureMatcher:
    """Signature matcher that performs header and footer detection."""
    
    def __init__(self, dictionary: SignatureDictionary) -> None: ...
    def match(self, data: bytes, max_offset: int = 512) -> SignatureMatch:
        """Match signatures against a byte sequence."""
        ...


# ============================================================================
# Heuristics Engine
# ============================================================================

class HeuristicResult:
    """Result of heuristic analysis on a byte sequence."""
    
    entropy: float
    """Shannon entropy [0.0, 8.0]."""
    
    printable_ratio: float
    """Ratio of printable ASCII [0.0, 1.0]."""
    
    control_char_ratio: float
    """Ratio of control characters [0.0, 1.0]."""
    
    max_null_run: int
    """Longest consecutive null byte run."""
    
    utf8_validity: float
    """UTF-8 sequence validity score [0.0, 1.0]."""
    
    composite_score: float
    """Weighted combination [0.0, 1.0]."""
    
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...


class HeuristicWeights:
    """Configurable weights for composite heuristic scoring."""
    
    entropy_weight: float
    printable_weight: float
    control_char_weight: float
    null_run_weight: float
    utf8_weight: float
    
    def __init__(self) -> None: ...


class HeuristicsEngine:
    """Heuristics Engine for analyzing byte sequences."""
    
    def __init__(self, weights: Optional[HeuristicWeights] = None) -> None: ...
    def set_weights(self, weights: HeuristicWeights) -> None: ...
    def get_weights(self) -> HeuristicWeights: ...
    def analyze(self, data: bytes) -> HeuristicResult:
        """Perform full heuristic analysis on byte data."""
        ...
    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        """Calculate Shannon entropy of byte data."""
        ...
    @staticmethod
    def calculate_printable_ratio(data: bytes) -> float:
        """Calculate the ratio of printable ASCII characters."""
        ...
    @staticmethod
    def validate_utf8(data: bytes) -> float:
        """Validate UTF-8 sequences and return a validity score."""
        ...


# ============================================================================
# Early Stopping
# ============================================================================

class StopLevel(Enum):
    """Stop levels for multi-level early stopping."""
    LEVEL_1 = 4  # 2-4 bytes: signature prefix + basic heuristics
    LEVEL_2 = 8  # 8 bytes: entropy bounds + checksum validation
    LEVEL_3 = 16  # 16 bytes: structural coherence


class StopDecision:
    """Result of an early stopping check."""
    
    should_stop: bool
    level: StopLevel
    score: float
    reason: str
    
    def __init__(self) -> None: ...


class EarlyStoppingConfig:
    """Configuration for early stopping thresholds."""
    
    level1_bytes: int
    level2_bytes: int
    level3_bytes: int
    min_entropy: float
    max_entropy: float
    level1_threshold: float
    level2_threshold: float
    level3_threshold: float
    adaptive_thresholds: bool
    
    def __init__(self) -> None: ...


class EarlyStoppingController:
    """Early Stopping Controller for reducing search space."""
    
    def __init__(self, config: Optional[EarlyStoppingConfig] = None) -> None: ...
    def should_stop(self, data: bytes) -> StopDecision:
        """Check if a path should be stopped at the current depth."""
        ...
    def update_best_score(self, score: float) -> None: ...
    def get_adaptive_threshold(self) -> float: ...
    @staticmethod
    def is_repeated_byte_pattern(data: bytes) -> bool: ...
    @staticmethod
    def is_all_null(data: bytes) -> bool: ...


# ============================================================================
# Prefix Trie
# ============================================================================

class PrefixStatus(Enum):
    """Status of a prefix trie node."""
    UNKNOWN = 0  # Not yet evaluated
    VALID = 1    # Prefix passed heuristics
    PRUNED = 2   # Prefix failed heuristics


class PrefixTrieConfig:
    """Configuration for the prefix trie."""
    
    max_depth: int
    initial_capacity: int
    prune_threshold: float
    branch_prune_count: int
    
    def __init__(self) -> None: ...


class PrefixTrieStats:
    """Statistics for prefix trie operations."""
    
    total_lookups: int
    cache_hits: int
    nodes_created: int
    nodes_pruned: int
    children_eliminated: int
    
    def __init__(self) -> None: ...


class PrefixTrieNode:
    """Prefix trie node."""
    
    reconstructed_byte: int
    status: PrefixStatus
    best_score: float
    children_offset: int
    visit_count: int
    parent_index: int


class PrefixTrie:
    """GPU-compatible trie for O(1) prefix lookup and pruning."""
    
    def __init__(self, config: Optional[PrefixTrieConfig] = None) -> None: ...
    def lookup(self, prefix: bytes) -> Optional[PrefixTrieNode]:
        """Look up a prefix in the trie."""
        ...
    def insert(self, prefix: bytes, status: PrefixStatus, score: float) -> int:
        """Insert or update a prefix in the trie."""
        ...
    def prune(self, prefix: bytes) -> int:
        """Mark a prefix as pruned and eliminate all children."""
        ...
    def is_pruned(self, prefix: bytes) -> bool:
        """Check if a prefix or any of its ancestors is pruned."""
        ...
    def get_effective_branching_factor(self) -> float: ...
    def node_count(self) -> int: ...
    def get_statistics(self) -> PrefixTrieStats: ...
    def clear(self) -> None: ...


# ============================================================================
# Memoization
# ============================================================================

class MemoizationConfig:
    """Configuration for the memoization cache."""
    
    max_size_bytes: int
    max_entries: int
    enabled: bool
    
    def __init__(self) -> None: ...


class MemoizationStats:
    """Statistics for cache operations."""
    
    hits: int
    misses: int
    insertions: int
    evictions: int
    current_entries: int
    current_size_bytes: int
    
    def __init__(self) -> None: ...
    def hit_rate(self) -> float: ...


class PrefixCacheEntry:
    """Result stored in the prefix cache."""
    
    heuristics: HeuristicResult
    score: float
    should_prune: bool
    access_count: int
    
    def __init__(self) -> None: ...


class PrefixCache:
    """Prefix Result Cache with LRU Eviction."""
    
    def __init__(self, config: Optional[MemoizationConfig] = None) -> None: ...
    def lookup(self, prefix: bytes) -> Optional[PrefixCacheEntry]:
        """Look up a prefix in the cache."""
        ...
    def insert(
        self,
        prefix: bytes,
        heuristics: HeuristicResult,
        score: float,
        should_prune: bool
    ) -> bool:
        """Insert or update a prefix result in the cache."""
        ...
    def contains(self, prefix: bytes) -> bool: ...
    def size(self) -> int: ...
    def empty(self) -> bool: ...
    def clear(self) -> None: ...
    def hit_rate(self) -> float: ...
    def get_statistics(self) -> MemoizationStats: ...
    def set_enabled(self, enabled: bool) -> None: ...
    def is_enabled(self) -> bool: ...


# ============================================================================
# Bit Pruning
# ============================================================================

class BitPruningMode(Enum):
    """Bit pruning modes that control which bit positions are explored."""
    EXHAUSTIVE = 0  # All 8 bit positions (O(8^d))
    MSB_ONLY = 1    # Only bits 4-7 (O(4^d))
    SINGLE_BIT = 2  # Only 2 configured bit positions (O(2^d))
    CUSTOM = 3      # User-defined bit mask


class BitPruningConfig:
    """Configuration for the bit pruning system."""
    
    mode: BitPruningMode
    bit_mask: int
    
    def __init__(
        self,
        mode_or_mask: Union[BitPruningMode, int, None] = None,
        bit2: Optional[int] = None
    ) -> None: ...
    def is_bit_allowed(self, bit_pos: int) -> bool: ...
    def allowed_bit_count(self) -> int: ...
    def get_allowed_positions(self) -> List[int]: ...
    def branching_factor(self) -> int: ...
    def description(self) -> str: ...
    def is_valid(self) -> bool: ...
    def get_mask(self) -> int: ...


# ============================================================================
# Scoring System
# ============================================================================

class ScoringWeights:
    """Configurable weights for composite scoring."""
    
    signature_weight: float
    heuristic_weight: float
    length_weight: float
    structure_weight: float
    
    def __init__(self) -> None: ...
    def is_valid(self) -> bool: ...
    def normalize(self) -> None: ...


class StructuralValidation:
    """Structural validation result for a candidate."""
    
    validity_score: float
    has_valid_length: bool
    has_valid_checksum: bool
    has_valid_pointers: bool
    
    def __init__(self) -> None: ...


class Candidate:
    """A candidate reconstruction with all associated metadata."""
    
    path: Path
    data: List[int]
    format_id: int
    format_name: str
    confidence: float
    heuristics: HeuristicResult
    signature_match: SignatureMatch
    structure: StructuralValidation
    composite_score: float
    
    def __init__(self) -> None: ...
    def get_data_bytes(self) -> bytes:
        """Get reconstructed data as Python bytes."""
        ...
    def __repr__(self) -> str: ...


class ScoreCalculator:
    """Composite score calculator."""
    
    def __init__(self, weights: Optional[ScoringWeights] = None) -> None: ...
    def set_weights(self, weights: ScoringWeights) -> None: ...
    def get_weights(self) -> ScoringWeights: ...
    def calculate(
        self,
        signature_score: float,
        heuristic_score: float,
        length_score: float,
        structure_score: float
    ) -> float:
        """Calculate composite score from component scores."""
        ...
    def score_candidate(self, candidate: Candidate, expected_length: int = 0) -> None:
        """Calculate and populate a Candidate's composite score."""
        ...


class CandidateQueue:
    """Priority queue for tracking top-K candidates."""
    
    def __init__(self, capacity: int = 10) -> None: ...
    def push(self, candidate: Candidate) -> bool:
        """Try to add a candidate to the queue."""
        ...
    def top(self) -> Candidate:
        """Get the top candidate (highest score)."""
        ...
    def pop(self) -> Candidate:
        """Remove and return the top candidate."""
        ...
    def get_top_k(self) -> List[Candidate]:
        """Get all candidates sorted by score (descending)."""
        ...
    def min_score(self) -> float: ...
    def would_accept(self, score: float) -> bool: ...
    def size(self) -> int: ...
    def capacity(self) -> int: ...
    def empty(self) -> bool: ...
    def full(self) -> bool: ...
    def clear(self) -> None: ...
    def set_capacity(self, new_capacity: int) -> None: ...


# ============================================================================
# Configuration System
# ============================================================================

class ConfigError(Enum):
    """Error codes for configuration operations."""
    NONE = 0
    FILE_NOT_FOUND = 1
    PARSE_ERROR = 2
    INVALID_VALUE = 3
    MISSING_REQUIRED_FIELD = 4
    TYPE_MISMATCH = 5
    OUT_OF_RANGE = 6


class ConfigResult:
    """Result of a configuration operation."""
    
    success: bool
    error: ConfigError
    message: str
    
    def __init__(self) -> None: ...
    def __bool__(self) -> bool: ...
    def __repr__(self) -> str: ...


class OutputConfig:
    """Output configuration options."""
    
    top_n_results: int
    save_partials: bool
    include_paths: bool
    metrics_verbosity: str
    
    def __init__(self) -> None: ...


class PerformanceConfig:
    """Performance configuration options."""
    
    max_parallel_workers: int
    cuda_streams: int
    batch_size: int
    
    def __init__(self) -> None: ...


class EtbConfig:
    """Complete configuration for the etb library."""
    
    signature_dictionary_path: str
    early_stopping: EarlyStoppingConfig
    heuristic_weights: HeuristicWeights
    scoring_weights: ScoringWeights
    bit_pruning: BitPruningConfig
    memoization: MemoizationConfig
    output: OutputConfig
    performance: PerformanceConfig
    entropy_min: float
    entropy_max: float
    min_printable_ratio: float
    max_null_run: int
    
    def __init__(self) -> None: ...
    def validate(self) -> ConfigResult:
        """Validate the entire configuration."""
        ...


class ConfigManager:
    """Configuration loader and manager."""
    
    @staticmethod
    def instance() -> "ConfigManager":
        """Get the singleton instance."""
        ...
    def load_json(self, filepath: str) -> ConfigResult:
        """Load configuration from a JSON file."""
        ...
    def load_json_string(self, json_content: str) -> ConfigResult:
        """Load configuration from a JSON string."""
        ...
    def load_yaml(self, filepath: str) -> ConfigResult:
        """Load configuration from a YAML file."""
        ...
    def load_yaml_string(self, yaml_content: str) -> ConfigResult:
        """Load configuration from a YAML string."""
        ...
    def get_config(self) -> EtbConfig:
        """Get the current configuration."""
        ...
    def set_config(self, config: EtbConfig) -> ConfigResult:
        """Set the configuration."""
        ...
    def update_value(self, key: str, value: str) -> ConfigResult:
        """Update a specific configuration value at runtime."""
        ...
    def reload(self) -> ConfigResult:
        """Reload configuration from the last loaded file."""
        ...
    def is_loaded(self) -> bool: ...
    def get_loaded_path(self) -> str: ...
    def reset_to_defaults(self) -> None: ...
    def save_json(self, filepath: str) -> ConfigResult: ...
    def save_yaml(self, filepath: str) -> ConfigResult: ...
    def to_json_string(self) -> str: ...
    def to_yaml_string(self) -> str: ...


def load_config(filepath: str) -> ConfigResult:
    """Load configuration from file (auto-detects format)."""
    ...

def get_default_config() -> EtbConfig:
    """Get the default configuration."""
    ...


# ============================================================================
# High-Level Extract Function
# ============================================================================

def extract(
    input: Union[bytes, str],
    config: EtbConfig = ...,
    max_paths: int = 1000000
) -> List[Candidate]:
    """
    Extract hidden data from input bytes using bit-level reconstruction.
    
    Args:
        input: Input data as bytes or a file path string
        config: EtbConfig object with extraction parameters
        max_paths: Maximum number of paths to evaluate (default: 1,000,000)
    
    Returns:
        List of Candidate objects sorted by score (highest first)
    
    Example:
        >>> import etb
        >>> candidates = etb.extract(b'\\x89PNG...', etb.EtbConfig())
        >>> for c in candidates:
        ...     print(f"{c.format_name}: {c.confidence:.2f}")
    """
    ...

def extract_from_file(
    filepath: str,
    config: EtbConfig = ...,
    max_paths: int = 1000000
) -> List[Candidate]:
    """Extract hidden data from a file."""
    ...


# ============================================================================
# Reporting System
# ============================================================================

class ValidationReport:
    """Validation report for a successful extraction."""
    
    signature_valid: bool
    structure_valid: bool
    heuristics_valid: bool
    overall_validity: float
    validation_notes: str
    
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...


class SuccessResult:
    """Success result containing extracted data and metadata."""
    
    extracted_bytes: List[int]
    detected_format: str
    format_category: str
    confidence: float
    reconstruction_path: Path
    validation: ValidationReport
    heuristics: HeuristicResult
    signature_match: SignatureMatch
    
    def __init__(self) -> None: ...
    def get_data_bytes(self) -> bytes:
        """Get extracted data as Python bytes."""
        ...
    def __repr__(self) -> str: ...


class PartialMatch:
    """Partial match information for failed extractions."""
    
    partial_data: List[int]
    possible_format: str
    partial_score: float
    depth_reached: int
    failure_reason: str
    
    def __init__(self) -> None: ...


class ParameterSuggestion:
    """Suggestion for parameter adjustment when extraction fails."""
    
    parameter_name: str
    current_value: str
    suggested_value: str
    rationale: str
    
    def __init__(
        self,
        parameter_name: str = "",
        current_value: str = "",
        suggested_value: str = "",
        rationale: str = ""
    ) -> None: ...


class FailureResult:
    """Failure result containing diagnostic information."""
    
    paths_explored: int
    effective_depth_reached: int
    best_partials: List[PartialMatch]
    suggestions: List[ParameterSuggestion]
    failure_summary: str
    
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...


class ExtractionMetrics:
    """Extraction metrics for reporting."""
    
    total_paths_possible: int
    paths_evaluated: int
    paths_pruned_level1: int
    paths_pruned_level2: int
    paths_pruned_level3: int
    paths_pruned_prefix: int
    effective_branching_factor: float
    effective_depth: float
    cache_hit_rate: float
    level1_prune_rate: float
    level2_prune_rate: float
    level3_prune_rate: float
    prefix_prune_rate: float
    format_distribution: List[Tuple[str, int]]
    wall_clock_seconds: float
    average_time_per_path_us: float
    gpu_utilization: float
    complexity_reduction: str
    
    def __init__(self) -> None: ...


class ExtractionResult:
    """Complete extraction result combining success/failure with metrics."""
    
    success: bool
    candidates: List[SuccessResult]
    failure: Optional[FailureResult]
    metrics: ExtractionMetrics
    
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...


class SuccessResultBuilder:
    """Builder for success results."""
    
    def __init__(self) -> None: ...
    def set_data(self, data: List[int]) -> "SuccessResultBuilder": ...
    def set_format(self, format_name: str, category: str = "") -> "SuccessResultBuilder": ...
    def set_confidence(self, confidence: float) -> "SuccessResultBuilder": ...
    def set_path(self, path: Path) -> "SuccessResultBuilder": ...
    def set_heuristics(self, heuristics: HeuristicResult) -> "SuccessResultBuilder": ...
    def set_signature_match(self, match: SignatureMatch) -> "SuccessResultBuilder": ...
    def set_structural_validation(self, structure: StructuralValidation) -> "SuccessResultBuilder": ...
    def build_validation_report(self) -> "SuccessResultBuilder": ...
    def build(self) -> SuccessResult: ...
    @staticmethod
    def from_candidate(candidate: Candidate) -> SuccessResult: ...


class FailureResultBuilder:
    """Builder for failure results."""
    
    def __init__(self) -> None: ...
    def set_paths_explored(self, count: int) -> "FailureResultBuilder": ...
    def set_effective_depth(self, depth: int) -> "FailureResultBuilder": ...
    def add_partial_match(self, partial: PartialMatch) -> "FailureResultBuilder": ...
    def add_partial_from_candidate(
        self, candidate: Candidate, failure_reason: str
    ) -> "FailureResultBuilder": ...
    def add_suggestion(self, suggestion: ParameterSuggestion) -> "FailureResultBuilder": ...
    def generate_suggestions(self, metrics: ExtractionMetrics) -> "FailureResultBuilder": ...
    def set_summary(self, summary: str) -> "FailureResultBuilder": ...
    def generate_summary(self) -> "FailureResultBuilder": ...
    def build(self) -> FailureResult: ...


class MetricsReporter:
    """Metrics reporter for extraction results."""
    
    def __init__(self) -> None: ...
    def set_total_paths_possible(self, count: int) -> "MetricsReporter": ...
    def set_paths_evaluated(self, count: int) -> "MetricsReporter": ...
    def set_paths_pruned_level1(self, count: int) -> "MetricsReporter": ...
    def set_paths_pruned_level2(self, count: int) -> "MetricsReporter": ...
    def set_paths_pruned_level3(self, count: int) -> "MetricsReporter": ...
    def set_paths_pruned_prefix(self, count: int) -> "MetricsReporter": ...
    def set_effective_branching_factor(self, factor: float) -> "MetricsReporter": ...
    def set_effective_depth(self, depth: float) -> "MetricsReporter": ...
    def set_cache_hit_rate(self, rate: float) -> "MetricsReporter": ...
    def add_format_detection(self, format: str, count: int = 1) -> "MetricsReporter": ...
    def set_wall_clock_time(self, seconds: float) -> "MetricsReporter": ...
    def set_gpu_utilization(self, utilization: float) -> "MetricsReporter": ...
    def calculate_derived_metrics(self) -> "MetricsReporter": ...
    def generate_complexity_reduction(self, input_length: int) -> "MetricsReporter": ...
    def build(self) -> ExtractionMetrics: ...
    def to_string(self, verbosity: str = "full") -> str: ...


class ExtractionResultBuilder:
    """Builder for complete extraction results."""
    
    def __init__(self) -> None: ...
    def set_success(self, success: bool) -> "ExtractionResultBuilder": ...
    def add_candidate(self, result: SuccessResult) -> "ExtractionResultBuilder": ...
    def add_candidates(self, candidates: List[Candidate]) -> "ExtractionResultBuilder": ...
    def set_failure(self, failure: FailureResult) -> "ExtractionResultBuilder": ...
    def set_metrics(self, metrics: ExtractionMetrics) -> "ExtractionResultBuilder": ...
    def build(self) -> ExtractionResult: ...


# Utility functions
def format_path(path: Path, max_coords: int = 10) -> str:
    """Format a path as a human-readable string."""
    ...

def format_bytes_hex(data: bytes, max_bytes: int = 32) -> str:
    """Format bytes as a hex string."""
    ...

def format_confidence(confidence: float) -> str:
    """Format a confidence score as a percentage string."""
    ...

def format_duration(seconds: float) -> str:
    """Format a duration in human-readable form."""
    ...

def format_count(count: int) -> str:
    """Format a large number with appropriate suffix (K, M, B)."""
    ...
