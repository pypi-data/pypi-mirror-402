# ExplodeThoseBits! // ETB

Exhaustive bit-tree traversal library. Takes bytes, explodes them into bits, walks every forward-only path through the bit space, reconstructs candidate byte sequences, scores them against known file signatures and heuristics. CUDA-accelerated for Hopper/Blackwell GPUs.

## What it does

Given n input bytes, there are 9^n - 1 possible forward-only paths through the bit coordinate space (each byte has 8 bit positions, plus the choice to skip). The library systematically generates these paths, extracts bits along each path, packs them back into bytes, and evaluates whether the result looks like valid data.

The search space is obviously intractable for any reasonable input size. A 16-byte input has ~1.8 × 10^15 paths. So the library implements multi-level early stopping that prunes branches at 4, 8, and 16 bytes based on:

- Signature prefix matching (does it start like a PNG, JPEG, PDF, etc.)
- Shannon entropy bounds (too low = repeated garbage, too high = random/encrypted)
- Printable ASCII ratio
- UTF-8 validity
- Control character density
- Null byte run length

This reduces effective complexity from O(8^n) to O(k^d) where k is the effective branching factor after pruning and d is the depth at which most paths get killed.

## Installation

```bash
pip install etb
```

Or build from source:

```bash
git clone https://github.com/odinglyn0/etb
cd etb
pip install .
```

Requires CUDA 12.x for GPU acceleration. Falls back to CPU if unavailable.

## Usage

### Basic extraction

```python
import etb

# Extract from bytes
data = open("suspicious.bin", "rb").read()
candidates = etb.extract(data)

for c in candidates:
    print(f"{c.format_name}: {c.confidence:.2%}")
    print(f"  Entropy: {c.heuristics.entropy:.2f}")
    print(f"  Path length: {c.path.length()}")
```

### Extract from file

```python
candidates = etb.extract_from_file("suspicious.bin")
```

### With metrics

```python
result = etb.extract_with_metrics(data)

print(f"Evaluated {result.metrics.paths_evaluated} paths")
print(f"Prune rate: {result.metrics.prune_rate:.1%}")
print(f"Effective branching factor: {result.metrics.effective_branching_factor:.2f}")
print(f"Time: {result.metrics.wall_clock_seconds:.2f}s")
```

### Custom configuration

```python
config = etb.EtbConfig()

# Adjust early stopping thresholds
config.early_stopping.level1_threshold = 0.3  # More aggressive pruning
config.early_stopping.level2_threshold = 0.4
config.early_stopping.adaptive_thresholds = True

# Entropy bounds
config.entropy_min = 0.1  # Below this = repeated pattern
config.entropy_max = 7.9  # Above this = random/encrypted

# Bit pruning mode
config.bit_pruning = etb.BitPruningConfig(etb.BitPruningMode.MSB_ONLY)  # O(4^d) instead of O(8^d)

# Output options
config.output.top_n_results = 20
config.output.include_paths = True

candidates = etb.extract(data, config)
```

### Load config from file

```python
etb.load_config("config.yaml")
config = etb.ConfigManager.instance().get_config()
```

### Low-level API

```python
# Bit coordinates
coord = etb.BitCoordinate(byte_index=0, bit_position=3)

# Paths (forward-only constraint enforced)
path = etb.Path()
path.add(etb.BitCoordinate(0, 3))
path.add(etb.BitCoordinate(1, 5))
path.add(etb.BitCoordinate(2, 1))
assert path.is_valid()  # byte indices must be strictly increasing

# Extract bits along a path
bits = etb.extract_bits_from_path(data, path)

# Pack bits back to bytes
reconstructed = etb.bits_to_bytes(bits)

# Or do both at once
reconstructed = etb.path_to_bytes(data, path)
```

### Path generation

```python
# Generate all paths for small inputs (careful with this)
gen = etb.PathGenerator(input_length=4)
for path in gen:
    # 9^4 - 1 = 6560 paths
    pass

# With bit pruning
config = etb.PathGeneratorConfig(input_length=4)
config.bit_mask = 0xF0  # Only MSB positions
gen = etb.PathGenerator(config)
# Now 5^4 - 1 = 624 paths
```

### Signature matching

```python
# Load signature dictionary
sigs = etb.SignatureDictionary()
sigs.load_from_json("signatures.json")

# Match against data
matcher = etb.SignatureMatcher(sigs)
match = matcher.match(data)

if match.matched:
    print(f"Detected: {match.format_name} ({match.category})")
    print(f"Confidence: {match.confidence:.2%}")
    print(f"Header matched: {match.header_matched}")
    print(f"Footer matched: {match.footer_matched}")
```

### Heuristics analysis

```python
engine = etb.HeuristicsEngine()
result = engine.analyze(data)

print(f"Entropy: {result.entropy:.2f} bits/byte")
print(f"Printable ratio: {result.printable_ratio:.2%}")
print(f"Control char ratio: {result.control_char_ratio:.2%}")
print(f"Max null run: {result.max_null_run}")
print(f"UTF-8 validity: {result.utf8_validity:.2%}")
print(f"Composite score: {result.composite_score:.2f}")
```

### Early stopping

```python
controller = etb.EarlyStoppingController()

# Check if a partial reconstruction should be abandoned
decision = controller.should_stop(partial_data)
if decision.should_stop:
    print(f"Stopped at level {decision.level}: {decision.reason}")
```

### Prefix trie (for deduplication)

```python
trie = etb.PrefixTrie()

# Insert evaluated prefixes
trie.insert(prefix_bytes, etb.PrefixStatus.VALID, score=0.8)
trie.insert(bad_prefix, etb.PrefixStatus.PRUNED, score=0.1)

# Check before evaluating
if trie.is_pruned(candidate_prefix):
    # Skip - ancestor was already pruned
    pass

# Stats
print(f"Effective branching factor: {trie.get_effective_branching_factor():.2f}")
```

### Memoization cache

```python
cache = etb.PrefixCache()

# Check cache before expensive evaluation
entry = cache.lookup(prefix)
if entry is not None:
    score = entry.score
    should_prune = entry.should_prune
else:
    # Evaluate and cache
    result = engine.analyze(prefix)
    cache.insert(prefix, result, score, should_prune)

print(f"Cache hit rate: {cache.hit_rate():.1%}")
```

## How the exhaustive search works

### Bit coordinate system

Each bit in the input is addressed by (byte_index, bit_position) where bit_position ∈ [0,7] and 0 is LSB.

### Forward-only paths

A path is a sequence of bit coordinates where each coordinate's byte_index is strictly greater than the previous. This constraint:

1. Ensures paths are acyclic
2. Limits path length to at most n (input length)
3. Makes the search space finite (though still exponential)

### Path enumeration

For n bytes with 8 bits each, the number of paths is:

```
Σ(k=1 to n) C(n,k) × 8^k = 9^n - 1
```

The library generates paths lazily using depth-first traversal with backtracking.

### Multi-level early stopping

The key to tractability. At each checkpoint depth:

**Level 1 (4 bytes):**
- Check signature prefix (first 4 bytes of PNG, JPEG, etc.)
- Basic entropy check
- Reject repeated byte patterns
- Threshold: 0.2 composite score

**Level 2 (8 bytes):**
- Full entropy bounds check
- Printable ratio for text detection
- Control character density
- Threshold: 0.3 composite score

**Level 3 (16 bytes):**
- Structural coherence
- UTF-8 validity
- Null run length
- Threshold: 0.4 composite score

Paths failing any level are pruned along with all descendants.

### Adaptive thresholds

When a high-scoring candidate is found (>0.8), thresholds tighten to 0.6. When the best score is low (<0.3), thresholds relax to 0.2. This focuses search on promising regions.

### Bit pruning modes

Reduce branching factor by limiting which bit positions are explored:

- **EXHAUSTIVE**: All 8 positions. O(8^d). Most thorough.
- **MSB_ONLY**: Positions 4-7 only. O(4^d). Good for most formats.
- **SINGLE_BIT**: 2 positions. O(2^d). Fastest.
- **CUSTOM**: Arbitrary bitmask.

### Scoring

Candidates are scored by weighted combination:

- Signature match: 40%
- Heuristic score: 30%
- Length score: 15%
- Structural validity: 15%

Top-k candidates are maintained in a min-heap for efficient tracking.

## CUDA acceleration

GPU kernels for:

- **Path generation**: Work-stealing across thread blocks, warp-level cooperative exploration
- **Heuristics**: Shared memory histograms for entropy calculation
- **Signature matching**: Constant memory broadcast for signature data
- **Prefix pruning**: Atomic trie updates

Optimized for SM 90 (Hopper) and SM 100 (Blackwell) with architecture-specific tuning.

## Configuration reference

See `data/config.yaml` for all options with documentation.

Key parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `early_stopping.level1_threshold` | 0.2 | Min score to continue at 4 bytes |
| `early_stopping.level2_threshold` | 0.3 | Min score to continue at 8 bytes |
| `early_stopping.level3_threshold` | 0.4 | Min score to continue at 16 bytes |
| `entropy_min` | 0.1 | Below = repeated pattern |
| `entropy_max` | 7.9 | Above = random/encrypted |
| `bit_pruning.mode` | exhaustive | Bit position selection |
| `memoization.max_cache_size_mb` | 1024 | LRU cache size |
| `output.top_n_results` | 10 | Candidates to return |
| `performance.batch_size` | 65536 | Paths per kernel launch |

## Supported formats

Signature detection for:

- Images: PNG, JPEG, GIF, BMP
- Documents: PDF
- Archives: ZIP, RAR, 7Z
- Executables: ELF, PE
- Audio: MP3
- Video: MP4

Add custom signatures via JSON:

```json
{
  "format": "CUSTOM",
  "category": "custom",
  "signatures": [
    {"magic": "DEADBEEF", "offset": 0, "confidence": 0.9}
  ],
  "footer": {
    "magic": "CAFEBABE",
    "required": false
  }
}
```

## Building from source

```bash
mkdir build && cd build
cmake ..
cmake --build .
ctest --output-on-failure
```

Requirements:
- CMake 3.24+
- CUDA Toolkit 12.x
- C++17 compiler
- Python 3.8+ (for bindings)

## License

MIT // See: LICENSE
