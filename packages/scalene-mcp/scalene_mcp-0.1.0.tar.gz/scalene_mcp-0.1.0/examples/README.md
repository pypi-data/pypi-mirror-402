# Scalene-MCP Examples

Practical examples showing how to use Scalene-MCP for real-world performance optimization.

## Quick Start

Run any example to see Scalene profiling in action:

```bash
# Simple example (< 1 second) - no dependencies needed!
python -m scalene 3_c_bindings_profiling.py

# With memory profiling
python -m scalene --memory 4_memory_leak_detection.py

# All examples in sequence
for i in 1 2 3 4 5 6; do python -m scalene ${i}_*.py; done
```

## Examples

### 1. Data Processing Pipeline
**File**: `1_data_processing_pipeline.py`

Profile a data processing pipeline showing the difference between slow Python loops and fast vectorized operations.

**Use when**: Your data pipeline is slow
**Runtime**: ~0.1 seconds
**Scalene shows**: Python time vs C time in NumPy
**Requirements**: numpy only

```bash
python -m scalene 1_data_processing_pipeline.py
```

**Key insight**: 
- `slow_python_processing()` with loops is ~95% Python time
- `fast_vectorized_processing()` with NumPy is ~70% C time (faster!)

---

### 2. Algorithm Comparison
**File**: `2_algorithm_comparison.py`

Compare performance of different sorting algorithms to see why Python's `sorted()` is fast.

**Use when**: Choosing between algorithm implementations
**Runtime**: ~1 second
**Scalene shows**: CPU time distribution, function call overhead

```bash
python -m scalene 2_algorithm_comparison.py
```

**Key insight**:
- Bubble sort (O(n²)): 50% slower, more Python calls
- Quick sort (O(n log n)): 30% slower than builtin
- Python sorted() (Timsort in C): Fastest! Built-in C implementation wins

---

### 3. C Bindings Profiling ⭐ 
**File**: `3_c_bindings_profiling.py`

**Directly demonstrates how Scalene profiles native code** - the answer to "can Scalene profile C/C++/Rust bindings?"

**Use when**: Using NumPy or other C-extension libraries
**Runtime**: ~0.1 seconds
**Scalene shows**: Python time vs C time breakdown
**Requirements**: numpy only

```bash
python -m scalene 3_c_bindings_profiling.py
```

**What you see**:
```
Line 15: result = pure_python_sum(data)
  → Python: 100ms  (pure Python, no C)

Line 16: result = numpy_sum(data)  
  → Python: 1ms, C: 5ms  (C extension does the work!)
```

**Key insight**: Scalene separates **where** time is spent:
- **Python time**: Your code, can optimize
- **C time**: Library code, consider different library or algorithm

---

### 4. Memory Leak Detection
**File**: `4_memory_leak_detection.py`

Find memory leaks by profiling memory allocation patterns.

**Use when**: Your service grows in memory over time
**Runtime**: <1 second
**Scalene shows**: Memory allocation per line, velocity of growth

```bash
python -m scalene --memory 4_memory_leak_detection.py
```

**What you see**:
```
Line 22: cache[key] = expensive_data()
  → Allocated: 50MB, Velocity: 0.5 MB/sec (HIGH - leak!)
  
Line 28: del cache[key]
  → Deallocated: 50MB
```

**Key insight**: High allocation velocity = likely memory leak. Look for growing caches or circular references.

---

### 5. I/O Bound Profiling
**File**: `5_io_bound_profiling.py`

Profile code that waits for I/O (network, files) to understand blocking patterns.

**Use when**: Your code uses requests, file I/O, or database calls
**Runtime**: ~1 second
**Scalene shows**: System time (I/O wait), Python time (processing)

```bash
python -m scalene 5_io_bound_profiling.py
```

**What you see**:
```
Sequential processing:
  → 80% System time (waiting for I/O)
  
Batch processing:
  → 40% System time (less waiting, better batching)
```

**Key insight**: High system time = blocked on I/O. Use async, parallel requests, or batch operations.

---

### 6. GPU Profiling
**File**: `6_gpu_profiling.py`

Pattern for profiling GPU-accelerated code with PyTorch/TensorFlow.

**Use when**: Training ML models or using GPU acceleration
**Runtime**: <0.5 seconds
**Scalene shows**: CPU vs GPU time distribution (with GPU hardware)

```bash
python -m scalene 6_gpu_profiling.py

# With GPU profiling (if GPU available)
python -m scalene --gpu 6_gpu_profiling.py
```

**What you see** (with GPU):
```
CPU matrix operation:   50% CPU time
GPU matrix operation:   90% GPU time (faster on GPU!)
Data transfer:          10% overhead
```

**Key insight**: GPU helps for large matrix operations. Watch out for data transfer overhead (PCIe bandwidth limited).

---

## Which Example Should I Run?

| Problem | Example |
|---------|---------|
| Data pipeline is slow | 1 - Data Processing |
| Choosing algorithms | 2 - Algorithm Comparison |
| Using NumPy/Pandas | 3 - C Bindings Profiling ⭐ |
| Memory keeps growing | 4 - Memory Leak Detection |
| Code waits on I/O | 5 - I/O Bound Profiling |
| Training ML models | 6 - GPU Profiling |

---

## How to Analyze Results

### Look for hotspots
```bash
# Run with more detail
python -m scalene --detailed 1_data_processing_pipeline.py
```

Each line shows:
- **Line number**: Where the code is
- **Time**: How long that line took (CPU time)
- **%**: Percentage of total time
- **Type**: CPU, Memory, GPU

### Python vs C time
In Example 3, notice:
- Pure Python shows high Python time
- NumPy shows high C time
- This tells you where to optimize

### Memory patterns
In Example 4, notice:
- Growing memory = allocation velocity
- Stable memory = normal pattern
- Deallocations appear as negative allocation

### System time
In Example 5, notice:
- High system time = waiting for I/O
- Low system time = compute-bound
- This tells you whether async helps

---

## Integration with Scalene-MCP

These examples work with both:
1. **Command line**: `python -m scalene example.py`
2. **Scalene-MCP API**: Programmatic profiling

### Using with Scalene-MCP programmatically:

```python
import asyncio
from scalene_mcp.profiler import ScaleneProfiler

async def profile_example():
    profiler = ScaleneProfiler()
    
    result = await profiler.profile(
        type="script",
        script_path="examples/1_data_processing_pipeline.py",
        include_memory=True,
        include_gpu=False
    )
    
    # Get hotspots via unified analyze() tool
    from scalene_mcp.analyzer import ProfileAnalyzer
    analyzer = ProfileAnalyzer(result)
    
    hotspots = analyzer.get_hotspots(metric="cpu", limit=3)
    for hs in hotspots:
        print(f"{hs.file}:{hs.line} - {hs.time_sec:.2f}s")

asyncio.run(profile_example())
```

---

## Performance Expectations

All examples complete in under 1 second:

| Example | Time | Requirements |
|---------|------|--------------|
| 1 | ~0.1s | numpy only |
| 2 | ~0.1s | No dependencies |
| 3 | ~0.1s | numpy only |
| 4 | ~0.04s | No dependencies |
| 5 | ~0.2s | No dependencies |
| 6 | ~0.1s | No dependencies |

This means you can:
- Profile during development
- Run repeatedly
- Use in automated tests
- Include in CI/CD

---

## See Also

- [Phase 8 Examples Guide](../PHASE_8_EXAMPLES.md) - Detailed explanation of each example
- [API Reference](../docs/api.md) - Profile programmatically
- [Architecture](../docs/architecture.md) - How Scalene-MCP works
- [Troubleshooting](../docs/troubleshooting.md) - Common issues

---

## Troubleshooting

**Example doesn't run**:
```bash
# Check Python version
python --version  # Need 3.8+

# Check Scalene installed
python -m pip install scalene
```

**No memory output in Example 4**:
```bash
# Add --memory flag
python -m scalene --memory 4_memory_leak_detection.py
```

**GPU example shows only CPU**:
```bash
# GPU hardware required for GPU profiling
# Example 6 works on CPU (graceful degradation)
# Add --gpu flag if GPU available
python -m scalene --gpu 6_gpu_profiling.py
```

**Not seeing expected output**:
1. Make sure you're running the right example
2. Use `--detailed` flag for more information
3. Check example docstring for what to expect
4. See PHASE_8_EXAMPLES.md for detailed explanation