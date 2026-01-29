# Documentation Index

Complete guide to Scalene-MCP documentation and resources.

## Getting Started

### Quick Start
- [README.md](../README.md) - Project overview, installation, quick examples
- **First time?** Start here to get up and running in minutes

---

## Core Documentation

### [API Reference](./api.md)
Complete API documentation for all tools and functions.

**Includes**:
- FastMCP tool signatures and parameters
- All available profiling options
- Return types and data models
- Code examples for each tool
- Python programmatic API
- Logging and error handling
- Best practices

**When to use**: Looking for specific tool documentation or function signatures

---

### [Architecture](./architecture.md)
Design and implementation details of Scalene-MCP.

**Includes**:
- System architecture diagrams
- Component responsibilities
- Data flow diagrams
- Design decision rationales
- Extension points for customization
- Performance characteristics
- Security considerations
- Deployment architecture

**When to use**: Understanding how the system works or planning extensions

---

### [Examples](./examples.md)
Practical code examples for common scenarios.

**Includes**:
- Simple profiling
- CPU/memory/GPU profiling
- Analysis workflows
- Profile comparison
- Function-level metrics
- Selective profiling
- Integration patterns
- Error handling

**When to use**: Learning by example or copying patterns for your use case

---

### [Troubleshooting](./troubleshooting.md)
Solutions to common problems and debugging guide.

**Includes**:
- Installation issues and fixes
- Runtime errors and solutions
- Memory and performance issues
- Platform-specific problems
- Debugging techniques
- FAQs
- Performance optimization tips

**When to use**: Encountering errors or unexpected behavior

---

## Reference Material

### Models and Data Structures

**ProfileResult**: Top-level profiling output
- `summary`: Overall statistics
- `cpu_profile`: CPU time breakdown
- `memory_profile`: Memory usage details
- `gpu_profile`: GPU metrics (if enabled)
- `errors`: Any warnings or issues

**See**: [API Reference - Data Models](./api.md#data-models)

---

### Available Tools

| Tool | Purpose |
|------|---------|
| `profile_script` | Profile a Python script |
| `profile_code` | Profile a code snippet |
| `analyze_profile` | Get insights from a profile |
| `get_cpu_hotspots` | Find CPU-intensive lines |
| `get_memory_hotspots` | Find memory-heavy code |
| `get_gpu_hotspots` | Find GPU-intensive operations |
| `get_bottlenecks` | Identify performance issues |
| `get_memory_leaks` | Detect potential leaks |
| `get_function_summary` | Aggregate by function |
| `compare_profiles` | Compare two profiles |
| `list_profiles` | View stored profiles |
| `get_file_details` | Get line-by-line metrics |

---

### Configuration Options

**Profiling Control**:
- `cpu`: Enable CPU profiling
- `memory`: Enable memory profiling
- `gpu`: Enable GPU profiling
- `stacks`: Collect stack traces

**Performance Tuning**:
- `cpu_sampling_rate`: CPU sample interval
- `cpu_percent_threshold`: Minimum CPU % to report
- `malloc_threshold`: Minimum allocation size
- `reduced_profile`: Minimal output mode

**Scope Control**:
- `profile_only`: Profile only these paths
- `profile_exclude`: Exclude these paths
- `use_virtual_time`: Use virtual time instead of wall time

**Analysis**:
- `memory_leak_detector`: Enable leak detection

See [API Reference - Profiling Options](./api.md#configuration)

---

## Learning Paths

### I want to...

#### Profile a Python script
1. Read: [README - Quick Start](../README.md#quick-start)
2. Example: [Examples - Simple Profile](./examples.md#basic-usage)
3. Reference: [API - profile_script](./api.md#profile_script)

#### Find performance bottlenecks
1. Read: [Examples - Find Bottlenecks](./examples.md#identifying-bottlenecks)
2. Reference: [API - get_bottlenecks](./api.md#get_bottlenecks)
3. Deep dive: [Architecture - Analysis Workflow](./architecture.md#analysis-workflow)

#### Detect memory leaks
1. Read: [Examples - Memory Profiling](./examples.md#memory-profiling-with-leak-detection)
2. Reference: [API - get_memory_leaks](./api.md#get_memory_leaks)
3. Troubleshoot: [Troubleshooting - Memory Issues](./troubleshooting.md#memory-issues)

#### Compare profiles for regressions
1. Read: [Examples - Compare Profiles](./examples.md#compare-two-profile-runs)
2. Reference: [API - compare_profiles](./api.md#compare_profiles)
3. Understand: [Architecture - Comparison Workflow](./architecture.md#comparison-workflow)

#### Integrate with my application
1. Read: [Examples - Web Service Integration](./examples.md#integration-with-your-application)
2. API: [Python API Reference](./api.md#python-api)
3. Design: [Architecture - Extension Points](./architecture.md#extension-points)

#### Troubleshoot an issue
1. Find: [Troubleshooting - Common Errors](./troubleshooting.md#common-errors-and-fixes)
2. Debug: [Troubleshooting - Debugging](./troubleshooting.md#debugging)
3. Optimize: [Troubleshooting - Performance](./troubleshooting.md#performance-optimization-tips)

#### Understand the system
1. Overview: [Architecture - Overview](./architecture.md#overview)
2. Components: [Architecture - Component Architecture](./architecture.md#component-architecture)
3. Design: [Architecture - Key Design Decisions](./architecture.md#key-design-decisions)

---

## Common Tasks

### Profile a script with default settings

```python
from scalene_mcp.profiler import ScaleneProfiler
import asyncio

async def main():
    profiler = ScaleneProfiler()
    result = await profiler.profile_script("my_script.py")
    print(f"Peak memory: {result.summary.max_footprint_mb}MB")

asyncio.run(main())
```

**See**: [API - profile_script](./api.md#profile_script)

---

### Find the slowest function

```python
from scalene_mcp.analyzer import ProfileAnalyzer

analyzer = ProfileAnalyzer()
hotspots = analyzer.get_hotspots(profile, metric="cpu", limit=1)
slowest = hotspots[0]
print(f"{slowest.file}:{slowest.line} - {slowest.time_sec:.2f}s")
```

**See**: [API - get_hotspots](./api.md#get_hotspots)

---

### Detect memory issues

```python
from scalene_mcp.analyzer import ProfileAnalyzer

analyzer = ProfileAnalyzer()
leaks = analyzer.get_memory_leaks(profile)
if leaks:
    print(f"Found {len(leaks)} potential leaks")
    for leak in leaks:
        print(f"  {leak.file}:{leak.line}")
```

**See**: [API - get_memory_leaks](./api.md#get_memory_leaks)

---

### Check for regressions

```python
from scalene_mcp.comparator import ProfileComparator

comparator = ProfileComparator()
comparison = comparator.compare(old_profile, new_profile)
if comparison.regressions:
    print("Performance regressed!")
```

**See**: [API - compare_profiles](./api.md#compare_profiles)

---

## Advanced Topics

### Custom Analysis

**See**: [Architecture - Extension Points](./architecture.md#extension-points)

### Persistent Storage

**See**: [Architecture - Extension Points - Adding Persistent Storage](./architecture.md#adding-persistent-storage)

### Performance Optimization

**See**: [Troubleshooting - Performance Optimization](./troubleshooting.md#performance-optimization-tips)

### Security Considerations

**See**: [Architecture - Security Considerations](./architecture.md#security-considerations)

---

## Contributing

### Adding Documentation

1. Create file in `docs/` directory
2. Follow markdown conventions
3. Include examples
4. Update this index

### Improving Examples

1. Add to `docs/examples.md`
2. Include docstring
3. Show expected output
4. Link from index

### Reporting Issues

Use GitHub Issues with:
1. Python version
2. OS and version
3. Steps to reproduce
4. Full error traceback

---

## Glossary

| Term | Definition |
|------|-----------|
| **Profile** | Complete profiling output with CPU/memory/GPU metrics |
| **Hotspot** | Code location with high resource usage |
| **Bottleneck** | Performance problem with severity and recommendation |
| **Regression** | Performance degradation compared to baseline |
| **Leak** | Potential memory issue indicated by allocation velocity |
| **Sampling** | Periodic measurement to estimate overall metrics |
| **Reduced Profile** | Output filtered to significant lines only |

See full [Architecture - Glossary](./architecture.md#glossary)

---

## Quick Links

### Core Files
- [README.md](../README.md)
- [API Reference](./api.md)
- [Architecture](./architecture.md)
- [Examples](./examples.md)
- [Troubleshooting](./troubleshooting.md)

### External Resources
- [Scalene GitHub](https://github.com/plasma-umass/scalene)
- [FastMCP Documentation](https://fastmcp.dev)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### Source Code
- [src/scalene_mcp/](../src/scalene_mcp/)
- [tests/](../tests/)

---

## Documentation Statistics

| Document | Sections | Length |
|----------|----------|--------|
| README.md | 8 | ~300 lines |
| api.md | 12 | ~600 lines |
| architecture.md | 15 | ~800 lines |
| examples.md | 11 | ~700 lines |
| troubleshooting.md | 12 | ~600 lines |
| **Total** | **58** | **~3000 lines** |

---

## Version History

Current version: **1.0.0**

See [CHANGELOG.md](../CHANGELOG.md) for detailed version history.

---

## Last Updated

Documentation last updated: 2026-01-15

For updates, check GitHub repository for latest version.