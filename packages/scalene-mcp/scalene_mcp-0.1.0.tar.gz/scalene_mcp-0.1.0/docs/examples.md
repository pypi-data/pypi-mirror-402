# Scalene-MCP Examples

Practical examples demonstrating how to use Scalene-MCP in different scenarios.

## Basic Usage

### Profile a Simple Script

**File: `examples/simple_profile.py`**

```python
"""Basic script profiling example."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler


async def main():
    profiler = ScaleneProfiler()
    
    # Profile a script
    result = await profiler.profile_script("fibonacci.py")
    
    # Print summary
    print(f"Elapsed time: {result.summary.elapsed_time_sec:.2f}s")
    print(f"Peak memory: {result.summary.max_footprint_mb:.1f}MB")
    
    # Check for issues
    if result.errors:
        print("Errors encountered:")
        for error in result.errors:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Target script: `fibonacci.py`**

```python
def fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


if __name__ == "__main__":
    result = fibonacci(30)
    print(f"Result: {result}")
```

---

### Profile Code Directly

**File: `examples/profile_snippet.py`**

```python
"""Profile a code snippet without saving to file."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler


async def main():
    profiler = ScaleneProfiler()
    
    code = """
import time

def slow_function():
    '''Simulate slow operation.'''
    total = 0
    for i in range(1000000):
        total += i
    return total

result = slow_function()
"""
    
    result = await profiler.profile_code(code, cpu=True, memory=True)
    print(f"Execution time: {result.summary.elapsed_time_sec:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Advanced Profiling

### CPU-Only Profiling with Sampling

**File: `examples/cpu_profile_advanced.py`**

```python
"""Advanced CPU profiling with custom sampling."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler


async def main():
    profiler = ScaleneProfiler()
    
    result = await profiler.profile_script(
        "matrix_multiply.py",
        # Only profile CPU
        cpu=True,
        memory=False,
        gpu=False,
        # Sampling configuration
        cpu_sampling_rate=0.001,  # 1ms sampling for finer granularity
        cpu_percent_threshold=0.5,  # Report anything > 0.5% CPU
        reduced_profile=False,  # Full profile
        # Target specific code
        profile_only="matrix",  # Only profile files with "matrix" in name
    )
    
    print(f"Total CPU time: {result.cpu_profile.total_python_time_sec:.2f}s")
    print(f"Number of lines profiled: {result.summary.num_lines}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Memory Profiling with Leak Detection

**File: `examples/memory_profile.py`**

```python
"""Memory profiling with leak detection."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler
from scalene_mcp.analyzer import ProfileAnalyzer


async def main():
    profiler = ScaleneProfiler()
    analyzer = ProfileAnalyzer()
    
    # Profile with memory focus
    result = await profiler.profile_script(
        "memory_heavy.py",
        cpu=False,  # Skip CPU for faster profiling
        memory=True,
        gpu=False,
        # Memory-specific options
        malloc_threshold=50,  # Track allocations > 50 bytes
        memory_leak_detector=True,  # Enable leak detection
        reduced_profile=False,  # Full memory details
    )
    
    print(f"Peak memory: {result.summary.max_footprint_mb:.1f}MB")
    print(f"Average memory: {result.summary.average_memory_mb:.1f}MB")
    
    # Detect leaks
    leaks = analyzer.get_memory_leaks(result)
    if leaks:
        print("\nPotential memory leaks detected:")
        for leak in leaks:
            print(f"  {leak.file}:{leak.line}")
            print(f"    Velocity: {leak.velocity_mb_per_sec:.3f}MB/s")
            print(f"    Total: {leak.total_leaked_mb:.1f}MB")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Analysis Workflows

### Finding CPU Hotspots

**File: `examples/find_hotspots.py`**

```python
"""Find and analyze CPU hotspots."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler
from scalene_mcp.analyzer import ProfileAnalyzer


async def main():
    profiler = ScaleneProfiler()
    analyzer = ProfileAnalyzer()
    
    # Profile the script
    result = await profiler.profile_script("app.py", cpu=True, memory=False)
    
    # Get top CPU hotspots
    hotspots = analyzer.get_hotspots(
        result,
        metric="cpu",
        limit=10
    )
    
    print("Top 10 CPU Hotspots:")
    print("-" * 60)
    
    for i, spot in enumerate(hotspots, 1):
        print(f"{i}. {spot.file}:{spot.line}")
        print(f"   Time: {spot.time_sec:.2f}s ({spot.percent_of_total:.1f}%)")
        print(f"   Code: {spot.content.strip()}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Identifying Bottlenecks

**File: `examples/find_bottlenecks.py`**

```python
"""Identify performance bottlenecks."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler
from scalene_mcp.analyzer import ProfileAnalyzer


async def main():
    profiler = ScaleneProfiler()
    analyzer = ProfileAnalyzer()
    
    # Profile the application
    result = await profiler.profile_script("app.py")
    
    # Get bottlenecks ranked by severity
    bottlenecks = analyzer.get_bottlenecks(result, limit=5)
    
    print("Top Performance Bottlenecks:")
    print("-" * 60)
    
    for bn in bottlenecks:
        severity_color = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        
        print(f"{severity_color[bn.severity]} [{bn.severity.upper()}] {bn.location}")
        print(f"   Issue: {bn.issue}")
        print(f"   Impact: {bn.impact}")
        print(f"   Recommended fix: {bn.recommendation}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Comparison & Regression Detection

### Compare Two Profile Runs

**File: `examples/compare_profiles.py`**

```python
"""Compare profiles to detect regressions."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler
from scalene_mcp.comparator import ProfileComparator


async def main():
    profiler = ScaleneProfiler()
    comparator = ProfileComparator()
    
    print("Profiling version 1...")
    profile_v1 = await profiler.profile_script("app.py")
    
    # ... Make changes to app ...
    
    print("Profiling version 2...")
    profile_v2 = await profiler.profile_script("app.py")
    
    # Compare profiles with 10% tolerance
    comparison = comparator.compare(
        profile_v1,
        profile_v2,
        tolerance=0.10
    )
    
    print(f"Total change: {comparison.summary.total_cpu_change_pct:.1f}%")
    print(f"Memory change: {comparison.summary.memory_change_pct:.1f}%")
    
    if comparison.regressions:
        print(f"\n⚠️ {len(comparison.regressions)} Regressions detected:")
        for reg in comparison.regressions:
            print(f"   {reg.location}: {reg.cpu_change_pct:.1f}% slower")
    
    if comparison.improvements:
        print(f"\n✅ {len(comparison.improvements)} Improvements detected:")
        for imp in comparison.improvements:
            print(f"   {imp.location}: {abs(imp.cpu_change_pct):.1f}% faster")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Function-Level Analysis

### Aggregate Metrics by Function

**File: `examples/function_metrics.py`**

```python
"""Analyze performance by function."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler
from scalene_mcp.analyzer import ProfileAnalyzer


async def main():
    profiler = ScaleneProfiler()
    analyzer = ProfileAnalyzer()
    
    result = await profiler.profile_script("app.py")
    
    # Get function-level metrics
    functions = analyzer.get_function_metrics(result, limit=10)
    
    print("Function-Level Performance Metrics:")
    print("-" * 80)
    print(f"{'Function':<30} {'CPU Time':<12} {'Memory':<12} {'Calls':<8}")
    print("-" * 80)
    
    for func in functions:
        memory_str = f"{func.memory_peak_mb:.1f}MB"
        cpu_str = f"{func.cpu_time_sec:.2f}s"
        print(f"{func.function_name:<30} {cpu_str:<12} {memory_str:<12} {func.num_calls:<8}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Selective Profiling

### Profile Specific Code Paths

**File: `examples/selective_profile.py`**

```python
"""Profile only specific code paths."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler


async def main():
    profiler = ScaleneProfiler()
    
    # Profile only the ML module, exclude tests
    result = await profiler.profile_script(
        "main.py",
        profile_only="ml_module",  # Only profile files with "ml_module"
        profile_exclude="test",     # Exclude files with "test"
        reduced_profile=True,       # Only show significant lines
        cpu_percent_threshold=2.0,  # Ignore lines < 2% CPU
    )
    
    print(f"Profiled {result.summary.num_lines} significant lines")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Integration with Your Application

### Using Scalene-MCP in a Web Service

**File: `examples/web_service_profiling.py`**

```python
"""Profile a web service and log metrics."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from scalene_mcp.profiler import ScaleneProfiler
from scalene_mcp.analyzer import ProfileAnalyzer


async def profile_and_log_service():
    """Profile a service and save results."""
    
    profiler = ScaleneProfiler()
    analyzer = ProfileAnalyzer()
    
    # Profile the service startup and operation
    result = await profiler.profile_script(
        "web_service.py",
        cpu=True,
        memory=True,
        gpu=False,
        timeout=300.0  # 5 minute timeout
    )
    
    # Analyze results
    hotspots = analyzer.get_hotspots(result, metric="cpu", limit=5)
    leaks = analyzer.get_memory_leaks(result)
    bottlenecks = analyzer.get_bottlenecks(result, limit=3)
    
    # Create report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "elapsed_time_sec": result.summary.elapsed_time_sec,
            "peak_memory_mb": result.summary.max_footprint_mb,
            "average_memory_mb": result.summary.average_memory_mb,
        },
        "hotspots": [
            {
                "file": h.file,
                "line": h.line,
                "time_sec": h.time_sec,
                "percent": h.percent_of_total,
                "content": h.content.strip(),
            }
            for h in hotspots
        ],
        "memory_leaks": [
            {
                "file": l.file,
                "line": l.line,
                "velocity_mb_per_sec": l.velocity_mb_per_sec,
                "confidence": l.confidence,
            }
            for l in leaks
        ],
        "bottlenecks": [
            {
                "severity": b.severity,
                "location": b.location,
                "recommendation": b.recommendation,
            }
            for b in bottlenecks
        ],
    }
    
    # Save report
    report_path = Path("profile_report.json")
    report_path.write_text(json.dumps(report, indent=2))
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    asyncio.run(profile_and_log_service())
```

---

## Error Handling

### Robust Profiling with Error Handling

**File: `examples/error_handling.py`**

```python
"""Error handling in profiling operations."""

import asyncio
from pathlib import Path

from scalene_mcp.profiler import ScaleneProfiler
from scalene_mcp.exceptions import (
    ScaleneError,
    ProfileError,
    TimeoutError,
)


async def main():
    profiler = ScaleneProfiler()
    
    try:
        result = await profiler.profile_script(
            "app.py",
            timeout=30.0,
        )
        
        print(f"Success! Elapsed: {result.summary.elapsed_time_sec:.2f}s")
        
        if result.errors:
            print("Warnings:")
            for error in result.errors:
                print(f"  - {error}")
                
    except FileNotFoundError:
        print("Error: Script file not found")
        
    except TimeoutError:
        print("Error: Profiling timed out after 30 seconds")
        print("Tip: Increase timeout for longer-running scripts")
        
    except ProfileError as e:
        print(f"Error: Profiling failed: {e}")
        
    except ScaleneError as e:
        print(f"Error: Scalene error: {e}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Tips & Tricks

### Performance Profiling Best Practices

```python
"""Best practices for efficient profiling."""

import asyncio
from scalene_mcp.profiler import ScaleneProfiler


async def main():
    profiler = ScaleneProfiler()
    
    # ✅ Good: Focused profiling
    # - CPU only when analyzing CPU
    # - Set appropriate thresholds
    # - Use reduced_profile for large codebases
    result = await profiler.profile_script(
        "app.py",
        cpu=True,
        memory=False,  # Skip if not needed
        gpu=False,
        cpu_percent_threshold=1.0,  # Ignore tiny contributors
        reduced_profile=True,  # Reduce output
    )
    
    # ❌ Bad: Unfocused profiling
    # - Profiling everything adds overhead
    # - Too low thresholds = noise
    # - Full profile on large codebases = too much data
    
    print("Profiling complete!")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Running the Examples

```bash
# Profile a script
python examples/simple_profile.py

# Profile code snippet
python examples/profile_snippet.py

# Advanced CPU profiling
python examples/cpu_profile_advanced.py

# Memory profiling with leak detection
python examples/memory_profile.py

# Find hotspots
python examples/find_hotspots.py

# Identify bottlenecks
python examples/find_bottlenecks.py

# Compare profiles
python examples/compare_profiles.py

# Analyze by function
python examples/function_metrics.py

# Selective profiling
python examples/selective_profile.py

# Web service profiling
python examples/web_service_profiling.py

# Error handling
python examples/error_handling.py
```

---

## See Also

- [API Reference](../docs/api.md)
- [Architecture](../docs/architecture.md)
- [Troubleshooting](../docs/troubleshooting.md)