# API Reference

Complete documentation for Scalene-MCP's tools, models, and programmatic interface.

## Scope & Limitations

Scalene-MCP supports **subprocess-based profiling** of Python scripts and code snippets. This approach was chosen for reliability, security, and clean error handling.

### ✅ Supported Use Cases
- Profile standalone Python scripts
- Profile packages/applications via entry point
- Profile code with custom arguments
- Analyze, compare, and investigate profiles

### ❌ Not Currently Supported
- **In-process profiling**: Using `Scalene.start()`/`stop()` directly
- **Process attachment**: Profiling running processes with `--pid`
- **Function-level profiling**: Profiling individual function calls without subprocess

**Note**: These limitations are intentional design choices. The subprocess model provides better isolation, reliability, and resource cleanup—ideal for LLM-based workflows. If you need in-process profiling, see [Future Enhancements](#future-enhancements) below.

---

## FastMCP Tools

### Core Profiling

#### `profile_script`

Profile a Python script with Scalene.

**Signature:**
```python
profile_script(
    script_path: str,
    args: list[str] | None = None,
    cpu: bool = True,
    memory: bool = True,
    gpu: bool = False,
    stacks: bool = False,
    reduced_profile: bool = False,
    profile_only: str = "",
    profile_exclude: str = "",
    cpu_sampling_rate: float = 0.01,
    cpu_percent_threshold: float = 1.0,
    malloc_threshold: int = 100,
    memory_leak_detector: bool = True,
    use_virtual_time: bool = False,
    timeout: float = 120.0
) -> ProfileResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script_path` | str | required | Path to Python script to profile |
| `args` | list[str] | None | Arguments to pass to the script |
| `cpu` | bool | True | Enable CPU profiling (Python/C/system time) |
| `memory` | bool | True | Enable memory profiling |
| `gpu` | bool | False | Enable GPU profiling (NVIDIA/Apple) |
| `stacks` | bool | False | Collect full stack traces |
| `reduced_profile` | bool | False | Only report lines with significant activity |
| `profile_only` | str | "" | Profile only files matching pattern |
| `profile_exclude` | str | "" | Skip files matching pattern |
| `cpu_sampling_rate` | float | 0.01 | CPU sampling interval (seconds) |
| `cpu_percent_threshold` | float | 1.0 | Minimum CPU% to include in output |
| `malloc_threshold` | int | 100 | Minimum allocation size to track (bytes) |
| `memory_leak_detector` | bool | True | Enable memory leak detection |
| `use_virtual_time` | bool | False | Use virtual time instead of wall time |
| `timeout` | float | 120.0 | Maximum execution time (seconds) |

**Returns:**
```python
ProfileResult(
    summary: SummaryMetrics,
    cpu_profile: CPUMetrics | None,
    memory_profile: MemoryMetrics | None,
    gpu_profile: GPUMetrics | None,
    errors: list[str],
    profile_id: str
)
```

**Example:**
```python
result = await profile_script(
    "fibonacci.py",
    args=["30"],
    cpu=True,
    memory=True,
    gpu=False
)
print(f"Peak memory: {result.summary.max_footprint_mb}MB")
```

**When to use:**
- Profiling standalone Python scripts
- Benchmarking production scripts with arguments
- Identifying bottlenecks in complete applications

---

#### `profile_code`

Profile a code snippet directly without saving to a file.

**Signature:**
```python
profile_code(
    code: str,
    cpu: bool = True,
    memory: bool = True,
    gpu: bool = False,
    stacks: bool = False,
    reduced_profile: bool = False,
    cpu_percent_threshold: float = 1.0,
    malloc_threshold: int = 100,
    timeout: float = 60.0
) -> ProfileResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | str | required | Python code to execute and profile |
| `cpu` | bool | True | Enable CPU profiling |
| `memory` | bool | True | Enable memory profiling |
| `gpu` | bool | False | Enable GPU profiling |
| `stacks` | bool | False | Collect stack traces |
| `reduced_profile` | bool | False | Only report significant lines |
| `cpu_percent_threshold` | float | 1.0 | Minimum CPU% threshold |
| `malloc_threshold` | int | 100 | Minimum allocation size |
| `timeout` | float | 60.0 | Maximum execution time |

**Returns:**
```python
ProfileResult
```

**Example:**
```python
code = """
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(25)
"""

result = await profile_code(code)
print(f"Execution time: {result.summary.elapsed_time_sec}s")
```

**When to use:**
- Testing performance of small code snippets
- Profiling functions without file I/O overhead
- Ad-hoc performance experiments

---

### Analysis

#### `analyze_profile`

Generate comprehensive analysis and insights from a profile.

**Signature:**
```python
analyze_profile(
    profile: ProfileResult,
    focus_area: str = "overall"  # "cpu", "memory", "gpu", "overall"
) -> AnalysisResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile` | ProfileResult | required | Profile to analyze |
| `focus_area` | str | "overall" | What to focus on: "cpu", "memory", "gpu", or "overall" |

**Returns:**
```python
AnalysisResult(
    hotspots: list[Hotspot],
    bottlenecks: list[Bottleneck],
    recommendations: list[str],
    summary: str,
    severity: str  # "critical", "warning", "info"
)
```

**Example:**
```python
analysis = await analyze_profile(profile, focus_area="memory")
for hotspot in analysis.hotspots:
    print(f"{hotspot.file}:{hotspot.line} - {hotspot.metric}%")
```

**When to use:**
- Getting automated insights from profiles
- Identifying most impactful optimization opportunities
- Understanding performance issues at a glance

---

#### `get_cpu_hotspots`

Find the most CPU-intensive lines of code.

**Signature:**
```python
get_cpu_hotspots(
    profile: ProfileResult,
    limit: int = 10,
    include_system: bool = False
) -> list[CPUHotspot]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile` | ProfileResult | required | Profile to analyze |
| `limit` | int | 10 | Number of hotspots to return |
| `include_system` | bool | False | Include system time in analysis |

**Returns:**
```python
list[CPUHotspot(
    file: str,
    line: int,
    content: str,
    python_time_sec: float,
    c_time_sec: float,
    system_time_sec: float,
    percent_of_total: float
)]
```

**Example:**
```python
hotspots = await get_cpu_hotspots(profile, limit=5)
for spot in hotspots:
    total_sec = spot.python_time_sec + spot.c_time_sec
    print(f"{spot.file}:{spot.line} - {total_sec:.2f}s ({spot.percent_of_total:.1f}%)")
```

---

#### `get_memory_hotspots`

Find the most memory-intensive code sections.

**Signature:**
```python
get_memory_hotspots(
    profile: ProfileResult,
    limit: int = 10,
    metric: str = "peak"  # "peak", "average", "allocation"
) -> list[MemoryHotspot]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile` | ProfileResult | required | Profile to analyze |
| `limit` | int | 10 | Number of hotspots to return |
| `metric` | str | "peak" | Which metric: "peak", "average", or "allocation" |

**Returns:**
```python
list[MemoryHotspot(
    file: str,
    line: int,
    content: str,
    peak_mb: float,
    average_mb: float,
    allocations: int,
    percent_of_total: float
)]
```

---

#### `get_gpu_hotspots`

Find GPU-intensive operations (when GPU profiling enabled).

**Signature:**
```python
get_gpu_hotspots(
    profile: ProfileResult,
    limit: int = 10
) -> list[GPUHotspot]
```

**Returns:**
```python
list[GPUHotspot(
    file: str,
    line: int,
    content: str,
    gpu_time_sec: float,
    gpu_percent: float,
    gpu_memory_mb: float
)]
```

---

#### `get_bottlenecks`

Identify top performance bottlenecks ranked by severity.

**Signature:**
```python
get_bottlenecks(
    profile: ProfileResult,
    limit: int = 5
) -> list[Bottleneck]
```

**Returns:**
```python
list[Bottleneck(
    severity: str,  # "critical", "high", "medium", "low"
    location: str,
    issue: str,
    impact: str,
    recommendation: str
)]
```

**Example:**
```python
bottlenecks = await get_bottlenecks(profile)
for bn in bottlenecks:
    print(f"[{bn.severity.upper()}] {bn.location}")
    print(f"  Issue: {bn.issue}")
    print(f"  Fix: {bn.recommendation}")
```

---

#### `get_memory_leaks`

Detect potential memory leaks with velocity metrics.

**Signature:**
```python
get_memory_leaks(
    profile: ProfileResult,
    confidence: str = "medium"  # "high", "medium", "low"
) -> list[MemoryLeak]
```

**Returns:**
```python
list[MemoryLeak(
    file: str,
    line: int,
    content: str,
    velocity_mb_per_sec: float,
    total_leaked_mb: float,
    confidence: str,
    recommendation: str
)]
```

---

#### `get_function_summary`

Aggregate metrics by function.

**Signature:**
```python
get_function_summary(
    profile: ProfileResult,
    limit: int = 20
) -> list[FunctionMetrics]
```

**Returns:**
```python
list[FunctionMetrics(
    function_name: str,
    file: str,
    start_line: int,
    cpu_time_sec: float,
    memory_peak_mb: float,
    memory_average_mb: float,
    num_calls: int,
    percent_of_total_cpu: float
)]
```

---

### Comparison

#### `compare_profiles`

Compare two profiles to identify performance changes.

**Signature:**
```python
compare_profiles(
    profile1: ProfileResult,
    profile2: ProfileResult,
    tolerance: float = 0.05  # 5% tolerance
) -> ComparisonResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile1` | ProfileResult | required | Baseline profile |
| `profile2` | ProfileResult | required | New profile to compare |
| `tolerance` | float | 0.05 | Tolerance for regressions (0.05 = 5%) |

**Returns:**
```python
ComparisonResult(
    summary: ComparisonSummary,
    regressions: list[Regression],
    improvements: list[Improvement],
    unchanged: list[UnchangedLine]
)
```

**Example:**
```python
comparison = await compare_profiles(before, after, tolerance=0.10)
if comparison.summary.has_regressions:
    print("Performance regressions detected:")
    for reg in comparison.regressions:
        print(f"  {reg.location}: {reg.cpu_change_pct:.1f}% slower")
```

---

### Storage

#### `list_profiles`

List all stored profiles in the current session.

**Signature:**
```python
list_profiles() -> list[ProfileMetadata]
```

**Returns:**
```python
list[ProfileMetadata(
    profile_id: str,
    script_name: str,
    timestamp: str,
    elapsed_time_sec: float,
    max_footprint_mb: float
)]
```

---

#### `get_file_details`

Get detailed line-by-line metrics for a specific file.

**Signature:**
```python
get_file_details(
    profile: ProfileResult,
    file_path: str
) -> FileMetrics
```

**Returns:**
```python
FileMetrics(
    file: str,
    lines: list[LineMetrics],
    summary: FileMetricsSummary
)

LineMetrics(
    line_number: int,
    content: str,
    python_time_sec: float,
    c_time_sec: float,
    system_time_sec: float,
    peak_memory_mb: float,
    allocations: int,
    gpu_time_sec: float
)
```

---

## Data Models

### ProfileResult

The main result from profiling operations.

```python
class ProfileResult(BaseModel):
    summary: SummaryMetrics
    cpu_profile: CPUMetrics | None
    memory_profile: MemoryMetrics | None
    gpu_profile: GPUMetrics | None
    errors: list[str]
    profile_id: str
```

### SummaryMetrics

Overall profile statistics.

```python
class SummaryMetrics(BaseModel):
    elapsed_time_sec: float
    max_footprint_mb: float
    average_memory_mb: float
    num_lines: int
    num_functions: int
    cpu_percent_threshold: float
```

### CPUMetrics

CPU profiling details (Python, C, system time).

```python
class CPUMetrics(BaseModel):
    total_python_time_sec: float
    total_c_time_sec: float
    total_system_time_sec: float
    lines: dict[str, LineMetrics]
```

### MemoryMetrics

Memory profiling details.

```python
class MemoryMetrics(BaseModel):
    peak_mb: float
    average_mb: float
    num_allocations: int
    num_deallocations: int
    lines: dict[str, LineMemory]
```

### GPUMetrics

GPU profiling details (when enabled).

```python
class GPUMetrics(BaseModel):
    total_gpu_time_sec: float
    total_gpu_memory_mb: float
    lines: dict[str, LineGPU]
```

---

## Python API

### Using Scalene-MCP Programmatically

#### ScaleneProfiler

Direct access to profiling functionality.

```python
from scalene_mcp.profiler import ScaleneProfiler

profiler = ScaleneProfiler()

# Profile a script
result = await profiler.profile_script(
    "my_script.py",
    cpu=True,
    memory=True,
    gpu=False
)

# Profile code
result = await profiler.profile_code(
    "for i in range(1000): pass",
    cpu=True
)
```

#### ProfileAnalyzer

Analyze profiles programmatically.

```python
from scalene_mcp.analyzer import ProfileAnalyzer

analyzer = ProfileAnalyzer()

# Get hotspots
hotspots = analyzer.get_hotspots(profile, metric="cpu", limit=10)

# Get bottlenecks
bottlenecks = analyzer.get_bottlenecks(profile)

# Get memory leaks
leaks = analyzer.get_memory_leaks(profile)
```

#### ProfileComparator

Compare profiles for regressions.

```python
from scalene_mcp.comparator import ProfileComparator

comparator = ProfileComparator()

# Compare two profiles
comparison = comparator.compare(
    profile1, 
    profile2,
    tolerance=0.05
)

# Check for regressions
if comparison.has_regressions:
    for regression in comparison.regressions:
        print(f"Regression at {regression.location}: {regression.cpu_change_pct}%")
```

#### ProfileParser

Parse Scalene JSON output.

```python
from scalene_mcp.parser import ProfileParser

parser = ProfileParser()

# Parse from file
profile = parser.parse_file("profile.json")

# Parse from JSON string
profile = parser.parse_json(json_string)
```

---

## Logging

Scalene-MCP uses structured logging via Python's `logging` module with `rich` formatting.

```python
from scalene_mcp.logging import get_logger

logger = get_logger(__name__)

logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

Enable debug logging:
```python
from scalene_mcp.logging import configure_logging
import logging

configure_logging(logging.DEBUG)
```

---

## Error Handling

Common exceptions:

```python
from scalene_mcp.exceptions import (
    ScaleneError,
    ProfileError,
    TimeoutError,
    InvalidProfileError
)

try:
    result = await profile_script("script.py")
except TimeoutError:
    print("Profiling took too long")
except ProfileError as e:
    print(f"Profile error: {e}")
except ScaleneError as e:
    print(f"Scalene error: {e}")
```

---

## Best Practices

### Performance Profiling

1. **Use reduced_profile for large codebases**: Reduces output size
2. **Set cpu_percent_threshold appropriately**: Skip minor contributors
3. **Profile in isolation**: Avoid background processes affecting results
4. **Use timeout wisely**: Set based on expected runtime + margin

### Memory Profiling

1. **Enable memory_leak_detector**: Catches potential memory issues
2. **Check malloc_threshold**: Default 100 bytes usually appropriate
3. **Compare profiles**: Track memory usage across versions
4. **Monitor peak vs average**: Peak indicates spikes, average shows steady state

### GPU Profiling

1. **Only enable when needed**: GPU profiling adds overhead
2. **Verify GPU availability**: Some systems don't have NVIDIA/Apple GPU
3. **Check for CUDA issues**: GPU profiling may fail silently on misconfigured systems

### Production Use

1. **Handle timeouts**: Set appropriate timeout values
2. **Log results**: Use structured logging for debugging
3. **Monitor resources**: Profiling uses CPU/memory itself
4. **Cache profiles**: Reuse results when possible

---

## FAQ

**Q: How much overhead does profiling add?**
A: Typical overhead is 2-10x slowdown depending on profiling options. Reduced profile mode minimizes this.

**Q: Can I profile C extensions?**
A: Yes, Scalene includes C-time profiling for native extensions.

**Q: What's the difference between reduced_profile and cpu_percent_threshold?**
A: `reduced_profile` only reports lines with significant activity. `cpu_percent_threshold` filters output by percentage.

**Q: How accurate is memory leak detection?**
A: Leak detection uses allocation velocity. High confidence = strong indicators, but always verify manually.

**Q: Can I use Scalene-MCP in production?**
A: Yes, but profile in development/staging first. Profiling is resource-intensive.

---

## Future Enhancements

### Planned (v1.1+)

#### `profile_function()` - In-Process Function Profiling
Profile individual functions without subprocess overhead.

```python
async def profile_function(
    func: Callable,
    *args,
    **kwargs
) -> ProfileResult:
    """Profile a single function call with Scalene."""
```

**Benefits**:
- Lower latency than subprocess profiling
- Direct code integration
- Ideal for quick micro-profiling

**When to expect**: Phase 8-9 (potential)

---

#### `profile_with_context()` - Context Manager Support
Profile code blocks using context managers.

```python
async with profiler.profile_context("data_processing"):
    # Code to profile
    process_data()
```

**Benefits**:
- Named profiling blocks
- Nested profiling support
- Integration with code workflows

---

### Under Consideration (v2.0+)

#### `profile_process()` - Process Attachment
Attach to and profile running processes.

```python
result = await profiler.profile_process(
    pid=12345,
    duration=30.0
)
```

**Complexity**: High (OS-specific, permissions)  
**Value**: Lower priority for LLM workflows

---

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for detailed version history.

---

## See Also

- [Architecture](./architecture.md) - System design
- [Examples](./examples.md) - Code examples
- [Troubleshooting](./troubleshooting.md) - Solutions
- [README](../README.md) - Quick start