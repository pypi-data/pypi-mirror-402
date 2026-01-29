"""
ExplodeThoseBits (etb) - CUDA-Accelerated exhaustive bit-tree/bit-explosion analysis for digital forensics.

This library provides tools for extracting individual bits from bytes and
systematically reconstructing all possible forward-traversal combinations
to discover hidden/encoded data.

Example:
    >>> import etb
    >>> 
    >>> # Basic extraction from bytes
    >>> candidates = etb.extract(b'\\x89PNG...', etb.EtbConfig())
    >>> for c in candidates:
    ...     print(f"{c.format_name}: {c.confidence:.2f}")
    >>> 
    >>> # Extract from file
    >>> candidates = etb.extract_from_file("data.bin")
    >>> 
    >>> # Custom configuration
    >>> config = etb.EtbConfig()
    >>> config.output.top_n_results = 20
    >>> config.bit_pruning = etb.BitPruningConfig(etb.BitPruningMode.MSB_ONLY)
    >>> candidates = etb.extract(data, config)
"""

# Version from setuptools_scm
try:
    from etb._version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"

__author__ = "Odin Glynn-Martin"

# Import the native extension module
try:
    from etb._etb import *
    from etb._etb import (
        # Core data structures
        BitCoordinate,
        Path,
        # Bit extraction
        extract_bit,
        extract_bits_from_path,
        bits_to_bytes,
        path_to_bytes,
        bytes_to_bits,
        # Path generation
        PathGeneratorConfig,
        PathGenerator,
        PathCountResult,
        estimate_path_count,
        path_count_exceeds_threshold,
        # Signature detection
        FileSignature,
        FooterSignature,
        FormatDefinition,
        SignatureMatch,
        SignatureDictionary,
        SignatureMatcher,
        # Heuristics
        HeuristicResult,
        HeuristicWeights,
        HeuristicsEngine,
        # Early stopping
        StopLevel,
        StopDecision,
        EarlyStoppingConfig,
        EarlyStoppingController,
        # Prefix trie
        PrefixStatus,
        PrefixTrieConfig,
        PrefixTrieStats,
        PrefixTrie,
        # Memoization
        MemoizationConfig,
        MemoizationStats,
        PrefixCacheEntry,
        PrefixCache,
        # Bit pruning
        BitPruningMode,
        BitPruningConfig,
        # Scoring
        ScoringWeights,
        StructuralValidation,
        Candidate,
        ScoreCalculator,
        CandidateQueue,
        # Configuration
        ConfigError,
        ConfigResult,
        OutputConfig,
        PerformanceConfig,
        EtbConfig,
        ConfigManager,
        load_config,
        get_default_config,
        # High-level functions
        extract,
        extract_from_file,
    )
except ImportError as e:
    raise ImportError(
        f"Failed to import etb native extension: {e}\n"
        "Make sure the package was built correctly with CUDA support."
    ) from e


# Additional Python-only utilities
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path as PathLib


@dataclass
class ExtractionResult:
    """
    Complete result of an extraction operation.
    
    Attributes:
        success: Whether extraction found any candidates
        candidates: List of candidate reconstructions sorted by score
        metrics: Extraction metrics and statistics
    """
    success: bool
    candidates: List[Candidate]
    metrics: "ExtractionMetrics"
    
    def __bool__(self) -> bool:
        return self.success and len(self.candidates) > 0
    
    @property
    def best_candidate(self) -> Optional[Candidate]:
        """Get the highest-scoring candidate, or None if no candidates."""
        return self.candidates[0] if self.candidates else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "candidates": [
                {
                    "format_name": c.format_name,
                    "confidence": c.confidence,
                    "composite_score": c.composite_score,
                    "data_length": len(c.data),
                    "path_length": c.path.length(),
                }
                for c in self.candidates
            ],
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }


@dataclass
class ExtractionMetrics:
    """
    Metrics from an extraction operation.
    
    Attributes:
        total_paths_possible: Theoretical total number of paths
        paths_evaluated: Number of paths actually evaluated
        paths_pruned_level1: Paths pruned at level 1 (2-4 bytes)
        paths_pruned_level2: Paths pruned at level 2 (8 bytes)
        paths_pruned_level3: Paths pruned at level 3 (16 bytes)
        effective_branching_factor: Average branches per level after pruning
        effective_depth: Average depth at which paths were pruned
        cache_hit_rate: Memoization cache hit rate [0.0, 1.0]
        wall_clock_seconds: Total extraction time in seconds
        gpu_utilization: GPU utilization percentage (if CUDA used)
    """
    total_paths_possible: int = 0
    paths_evaluated: int = 0
    paths_pruned_level1: int = 0
    paths_pruned_level2: int = 0
    paths_pruned_level3: int = 0
    effective_branching_factor: float = 0.0
    effective_depth: float = 0.0
    cache_hit_rate: float = 0.0
    wall_clock_seconds: float = 0.0
    gpu_utilization: float = 0.0
    
    @property
    def prune_rate(self) -> float:
        """Calculate overall prune rate."""
        total_pruned = (
            self.paths_pruned_level1 + 
            self.paths_pruned_level2 + 
            self.paths_pruned_level3
        )
        total = self.paths_evaluated + total_pruned
        return total_pruned / total if total > 0 else 0.0
    
    @property
    def complexity_reduction(self) -> str:
        """Get human-readable complexity reduction description."""
        if self.effective_branching_factor > 0 and self.effective_depth > 0:
            return (
                f"Reduced from O(8^n) to O({self.effective_branching_factor:.1f}^"
                f"{self.effective_depth:.1f})"
            )
        return "N/A"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_paths_possible": self.total_paths_possible,
            "paths_evaluated": self.paths_evaluated,
            "paths_pruned_level1": self.paths_pruned_level1,
            "paths_pruned_level2": self.paths_pruned_level2,
            "paths_pruned_level3": self.paths_pruned_level3,
            "effective_branching_factor": self.effective_branching_factor,
            "effective_depth": self.effective_depth,
            "cache_hit_rate": self.cache_hit_rate,
            "wall_clock_seconds": self.wall_clock_seconds,
            "gpu_utilization": self.gpu_utilization,
            "prune_rate": self.prune_rate,
            "complexity_reduction": self.complexity_reduction,
        }


def extract_with_metrics(
    input_data: bytes,
    config: Optional[EtbConfig] = None,
    max_paths: int = 1000000,
) -> ExtractionResult:
    """
    Extract hidden data with detailed metrics.
    
    This is a convenience wrapper around extract() that also returns
    extraction metrics for analysis and debugging.
    
    Args:
        input_data: Input bytes to analyze
        config: Configuration options (uses defaults if None)
        max_paths: Maximum paths to evaluate
    
    Returns:
        ExtractionResult with candidates and metrics
    
    Example:
        >>> result = etb.extract_with_metrics(data)
        >>> if result:
        ...     print(f"Found {len(result.candidates)} candidates")
        ...     print(f"Prune rate: {result.metrics.prune_rate:.1%}")
    """
    import time
    
    if config is None:
        config = EtbConfig()
    
    start_time = time.perf_counter()
    candidates = extract(input_data, config, max_paths)
    elapsed = time.perf_counter() - start_time
    
    # Estimate path count
    path_result = estimate_path_count(len(input_data))
    
    metrics = ExtractionMetrics(
        total_paths_possible=path_result.estimated_count,
        paths_evaluated=len(candidates),  # Simplified - actual would track internally
        wall_clock_seconds=elapsed,
    )
    
    return ExtractionResult(
        success=len(candidates) > 0,
        candidates=candidates,
        metrics=metrics,
    )


# Convenience aliases
Config = EtbConfig
Result = ExtractionResult
Metrics = ExtractionMetrics


__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Core data structures
    "BitCoordinate",
    "Path",
    # Bit extraction
    "extract_bit",
    "extract_bits_from_path",
    "bits_to_bytes",
    "path_to_bytes",
    "bytes_to_bits",
    # Path generation
    "PathGeneratorConfig",
    "PathGenerator",
    "PathCountResult",
    "estimate_path_count",
    "path_count_exceeds_threshold",
    # Signature detection
    "FileSignature",
    "FooterSignature",
    "FormatDefinition",
    "SignatureMatch",
    "SignatureDictionary",
    "SignatureMatcher",
    # Heuristics
    "HeuristicResult",
    "HeuristicWeights",
    "HeuristicsEngine",
    # Early stopping
    "StopLevel",
    "StopDecision",
    "EarlyStoppingConfig",
    "EarlyStoppingController",
    # Prefix trie
    "PrefixStatus",
    "PrefixTrieConfig",
    "PrefixTrieStats",
    "PrefixTrie",
    # Memoization
    "MemoizationConfig",
    "MemoizationStats",
    "PrefixCacheEntry",
    "PrefixCache",
    # Bit pruning
    "BitPruningMode",
    "BitPruningConfig",
    # Scoring
    "ScoringWeights",
    "StructuralValidation",
    "Candidate",
    "ScoreCalculator",
    "CandidateQueue",
    # Configuration
    "ConfigError",
    "ConfigResult",
    "OutputConfig",
    "PerformanceConfig",
    "EtbConfig",
    "ConfigManager",
    "load_config",
    "get_default_config",
    # High-level functions
    "extract",
    "extract_from_file",
    "extract_with_metrics",
    # Python-only classes
    "ExtractionResult",
    "ExtractionMetrics",
    # Aliases
    "Config",
    "Result",
    "Metrics",
]
