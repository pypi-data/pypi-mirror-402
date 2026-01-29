# Scalene MCP Tools Reference

Quick reference for the 7 tools provided by the Scalene MCP Server.

## Discovery Tools

These help the LLM understand your project context.

### `get_project_root()`

Get the detected project root and structure type.

**Returns:**
```json
{
  "root": "/absolute/path/to/project",
  "type": "python|node|mixed|unknown",
  "markers_found": "pyproject.toml, .git, setup.py"
}
```

---

### `list_project_files(pattern="*.py", max_depth=3, exclude_patterns="...")`

List project files matching a glob pattern.

**Parameters:**
- `pattern`: Glob pattern like `*.py`, `src/**/*.py`, `tests/**`
- `max_depth`: Maximum directory depth to search (default: 3)
- `exclude_patterns`: Comma-separated patterns to skip

**Returns:**
```json
[
  "src/main.py",
  "src/utils.py",
  "tests/test_main.py"
]
```

---

### `set_project_context(project_root)`

Explicitly set project root (overrides auto-detection).

**Parameters:**
- `project_root`: Absolute path to project directory

**Returns:**
```json
{
  "project_root": "/path/to/project",
  "status": "set"
}
```

---

## Profiling Tool

### `profile(type, script_path=None, code=None, cpu_only=False, include_memory=True, include_gpu=False, ...)`

Profile Python code - single tool handles both scripts and snippets.

**Parameters:**
- `type`: **"script"** or **"code"** (required)
- `script_path`: Required if `type="script"`. Path to script (relative or absolute)
- `code`: Required if `type="code"`. Python code as string
- `cpu_only`: Skip memory/GPU profiling
- `include_memory`: Profile memory allocations (default: true)
- `include_gpu`: Profile GPU usage, requires NVIDIA CUDA
- `reduced_profile`: Show only significant lines
- `profile_only`: Comma-separated paths to include
- `profile_exclude`: Comma-separated paths to exclude
- `use_virtual_time`: Exclude I/O wait time
- `cpu_percent_threshold`: Minimum CPU % to report
- `malloc_threshold`: Minimum allocation bytes to report
- `script_args`: Command-line arguments for the script

**Returns:**
```json
{
  "profile_id": "profile_0",
  "summary": {
    "total_cpu_percent": 100.0,
    "total_memory_mb": 256.5,
    "runtime_seconds": 5.23
  },
  "text_summary": "..."
}
```

**Examples:**
```
profile(type="script", script_path="main.py")
profile(type="code", code="for i in range(1000): x = i * 2")
profile(type="script", script_path="train.py", include_gpu=True, script_args=["--batch-size", "32"])
```

---

## Analysis Tool (Mega Tool)

### `analyze(profile_id, metric_type="all", top_n=10, cpu_threshold=5.0, memory_threshold_mb=10.0, filename=None)`

Flexible analysis tool - single interface for all analysis types.

**Parameters:**
- `profile_id`: Required. Profile ID from `profile()`
- `metric_type`: Choose analysis type (required):
  - `"all"` - Comprehensive analysis
  - `"cpu"` - CPU hotspots
  - `"memory"` - Memory hotspots
  - `"gpu"` - GPU hotspots
  - `"bottlenecks"` - Lines exceeding thresholds
  - `"leaks"` - Memory leak detection
  - `"file"` - File-level metrics (requires `filename`)
  - `"functions"` - Function-level metrics
  - `"recommendations"` - Optimization suggestions
- `top_n`: Number of items to return (default: 10)
- `cpu_threshold`: Minimum CPU % for bottleneck flagging (default: 5.0)
- `memory_threshold_mb`: Minimum MB for bottleneck flagging (default: 10.0)
- `filename`: Required if `metric_type="file"`. File to analyze

**Returns: Varies by metric_type**

```json
{
  "metric_type": "cpu",
  "data": [
    {
      "type": "cpu",
      "filename": "src/compute.py",
      "lineno": 45,
      "line": "result = expensive_function(data)",
      "cpu_percent": 45.3
    }
  ]
}
```

**Examples:**
```
analyze(profile_id, metric_type="all")           # Everything
analyze(profile_id, metric_type="cpu", top_n=5)  # Top 5 CPU lines
analyze(profile_id, metric_type="memory")        # Memory hotspots
analyze(profile_id, metric_type="bottlenecks", cpu_threshold=10.0)
analyze(profile_id, metric_type="leaks")         # Memory leaks
analyze(profile_id, metric_type="file", filename="src/main.py")
analyze(profile_id, metric_type="functions", top_n=10)
analyze(profile_id, metric_type="recommendations")
```

---

## Comparison Tool

### `compare_profiles(before_id, after_id)`

Compare two profiles to measure optimization impact.

**Parameters:**
- `before_id`: Profile ID from original code
- `after_id`: Profile ID from optimized code

**Returns:**
```json
{
  "runtime_change_pct": -25.3,
  "memory_change_pct": -15.2,
  "improvements": [
    "Runtime decreased by 25.3%",
    "Memory usage decreased by 15.2%"
  ],
  "regressions": [],
  "summary_text": "✅ Optimization successful..."
}
```

---

## Utility Tool

### `list_profiles()`

List all profiles captured in this session.

**Returns:**
```json
["profile_0", "profile_1", "profile_2"]
```

---

## Typical Workflows

### Quick Profile & Analyze
```
1. profile(type="script", script_path="main.py")
2. analyze(profile_id, metric_type="all")
```

### Find CPU Issues
```
1. profile(type="script", script_path="main.py")
2. analyze(profile_id, metric_type="cpu", top_n=5)
```

### Find Memory Problems
```
1. profile(type="script", script_path="app.py", include_memory=True)
2. analyze(profile_id, metric_type="memory", top_n=5)
3. analyze(profile_id, metric_type="leaks")
```

### Debug Performance
```
1. profile(type="script", script_path="main.py")
2. analyze(profile_id, metric_type="bottlenecks")
3. analyze(profile_id, metric_type="recommendations")
4. analyze(profile_id, metric_type="functions", top_n=5)
```

### GPU Optimization
```
1. profile(type="script", script_path="train.py", include_gpu=True)
2. analyze(profile_id, metric_type="gpu", top_n=5)
3. analyze(profile_id, metric_type="functions")
```

### Validate Optimization
```
1. profile(type="script", script_path="main.py")  # before: profile_id_1
2. # Make optimizations...
3. profile(type="script", script_path="main.py")  # after: profile_id_2
4. compare_profiles(profile_id_1, profile_id_2)
```

### Zoom Into Specific File
```
1. profile(type="script", script_path="main.py")
2. analyze(profile_id, metric_type="file", filename="src/utils.py")
```

---

## Design Philosophy

**Why Fewer, Bigger Tools?**

- ✅ **Clearer intent** - LLMs reason better with 5-7 tools vs 16 tools
- ✅ **Less decision paralysis** - Arguments control behavior, not tool selection
- ✅ **Consistent API** - `analyze()` always returns `{metric_type, data}` structure
- ✅ **More flexible** - Easy to add new analysis types without new tools
- ✅ **Better help text** - Single comprehensive docstring vs 8 similar ones

---

## API Summary

| Tool | Purpose | Key Args |
|------|---------|----------|
| `get_project_root()` | Discover project structure | - |
| `list_project_files()` | Find files | `pattern`, `max_depth` |
| `set_project_context()` | Override auto-detection | `project_root` |
| `profile()` | Profile code | `type`, `script_path`/`code` |
| `analyze()` | Analyze profiles | `profile_id`, `metric_type` |
| `compare_profiles()` | Compare two profiles | `before_id`, `after_id` |
| `list_profiles()` | List all profiles | - |

**Total: 7 tools (was 16)**

---

## Notes

- **Relative paths** in `profile()` resolve from project root
- **Profile IDs** persist in server memory during a session
- **GPU support** requires NVIDIA CUDA and PyTorch/TensorFlow
- **metric_type** is case-sensitive
- All tools return consistent, predictable structures
