# Architecture

Design and architecture of Scalene-MCP.

## Overview

Scalene-MCP is a FastMCP v2 server that provides LLMs with structured access to Scalene's profiling capabilities. The architecture is designed around clean separation of concerns with minimal coupling.

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastMCP MCP Server                            │
│  (Handles protocol, tool registration, streaming responses)      │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    ┌───▼────┐         ┌────▼──┐          ┌────▼──┐
    │Profile │         │Analyze│          │Compare│
    │  Tool  │         │ Tool  │          │ Tool  │
    └───┬────┘         └────┬──┘          └────┬──┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────────────┐
        │                   │                           │
    ┌───▼──────────┐  ┌─────▼──────┐  ┌──────────────┐ │
    │ Profiler     │  │  Analyzer  │  │  Comparator  │ │
    │ (Subprocess) │  │ (Analysis) │  │ (Comparison) │ │
    └───┬──────────┘  └─────┬──────┘  └──────────────┘ │
        │                   │                           │
        └───────────────────┼───────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    ┌───▼────┐         ┌────▼──┐          ┌────▼──┐
    │ Parser │         │ Models│          │Logging│
    │ (JSON) │         │(Validation)      │(Rich) │
    └───┬────┘         └────┬──┘          └───────┘
        │                   │
        └───────────────────┼───────────────┐
                            │               │
                    ┌───────▼──────┐   ┌────▼────┐
                    │ Scalene CLI  │   │   Temp  │
                    │ (subprocess) │   │  Files  │
                    └──────────────┘   └─────────┘
```

## Component Architecture

### 1. FastMCP Server (`server.py`)

**Responsibility**: Expose profiling capabilities through MCP tools

**Key Classes**:
- `FastMCP` instance configured with Scalene Profiler description
- Tool registration for all profiling operations

**Inputs**: 
- MCP protocol messages from LLM clients
- Tool requests with parameters

**Outputs**:
- Structured tool responses
- Streaming messages via MCP protocol

**Dependencies**:
- FastMCP framework
- All profiler/analyzer/comparator modules
- Logging infrastructure

---

### 2. ScaleneProfiler (`profiler.py`)

**Responsibility**: Execute Scalene via subprocess, handle execution, return structured results

**Key Methods**:
- `profile_script()`: Profile a Python script
- `profile_code()`: Profile code snippet via temp file

**Execution Flow**:
1. Validate inputs (file exists, timeout reasonable)
2. Build Scalene command with all options
3. Create temp file for JSON output
4. Execute via `asyncio.create_subprocess_exec()`
5. Parse JSON output via ProfileParser
6. Clean up temp file in finally block
7. Return ProfileResult

**Key Details**:
- Uses `tempfile.NamedTemporaryFile(delete=False)` for JSON output
- Subprocess command: `["python", "-m", "scalene", "run", "--json", "--outfile", path, "--no-browser"]`
- Comprehensive error handling with logging at all levels
- Cleanup happens even on errors

**Dependencies**:
- asyncio for subprocess
- tempfile for JSON output
- ProfileParser for JSON conversion
- Logging infrastructure

---

### 3. ProfileParser (`parser.py`)

**Responsibility**: Convert Scalene JSON to structured Pydantic models

**Key Methods**:
- `parse_file()`: Parse from file path
- `parse_json()`: Parse from JSON string

**Implementation Details**:
- `parse_json()` extracts JSON from mixed output (uses `find('{')` and `rfind('}')`)
- Handles Scalene quirks:
  - `scalene_args` comes as list → convert to dict
  - Nested file paths → preserve structure
- Comprehensive error messages on parse failures

**Output Model Hierarchy**:
```
ProfileResult
├── SummaryMetrics (overall stats)
├── CPUMetrics (if cpu=True)
├── MemoryMetrics (if memory=True)
├── GPUMetrics (if gpu=True)
└── errors: list[str]
```

**Dependencies**:
- Pydantic for validation
- JSON module for parsing
- Logging infrastructure

---

### 4. ProfileAnalyzer (`analyzer.py`)

**Responsibility**: Extract insights and identify problems from profiles

**Key Methods**:
- `get_hotspots()`: Find CPU/memory hot spots
- `get_bottlenecks()`: Identify performance issues
- `get_memory_leaks()`: Detect potential leaks
- `get_function_metrics()`: Aggregate by function

**Analysis Strategies**:
- **Hotspots**: Sort by time/memory, apply threshold
- **Bottlenecks**: Combine multiple metrics (CPU + memory + velocity)
- **Leaks**: Use allocation velocity (MB/s) + confidence scoring
- **Functions**: Aggregate line metrics to function level

**Output Models**:
- `Hotspot`: Ranked performance locations
- `Bottleneck`: Severity-ranked issues with recommendations
- `MemoryLeak`: Detected leaks with confidence
- `FunctionMetrics`: Aggregated function-level data

**Dependencies**:
- Profile models
- Statistical calculations

---

### 5. ProfileComparator (`comparator.py`)

**Responsibility**: Compare profiles to detect regressions and improvements

**Key Methods**:
- `compare()`: Compare two profiles with tolerance

**Comparison Logic**:
1. Match lines between profiles by file:line
2. Calculate percentage changes in metrics
3. Flag regressions (CPU/memory increase > tolerance)
4. Flag improvements (CPU/memory decrease > tolerance)
5. Mark unchanged lines

**Output**:
- `ComparisonResult` with summary and line-by-line changes
- Severity assessment for regressions
- Recommendations for improvements

**Dependencies**:
- Profile models
- Statistical calculations

---

### 6. Data Models (`models.py`)

**Responsibility**: Define and validate all data structures

**Model Hierarchy**:
```
ProfileResult (Top-level profile data)
├── SummaryMetrics
│   ├── elapsed_time_sec
│   ├── max_footprint_mb
│   └── ...
├── CPUMetrics
│   ├── total_python_time_sec
│   ├── total_c_time_sec
│   └── lines: dict[str, LineMetrics]
├── MemoryMetrics
│   ├── peak_mb
│   ├── average_mb
│   └── lines: dict[str, LineMemory]
└── GPUMetrics
    ├── total_gpu_time_sec
    └── lines: dict[str, LineGPU]

AnalysisResult
├── hotspots: list[Hotspot]
├── bottlenecks: list[Bottleneck]
├── recommendations: list[str]
└── summary: str

ComparisonResult
├── summary: ComparisonSummary
├── regressions: list[Regression]
├── improvements: list[Improvement]
└── unchanged: list[UnchangedLine]
```

**Key Features**:
- All models inherit from `BaseModel` (Pydantic)
- Full type validation
- Serializable to JSON
- Docstrings on all fields

**Dependencies**:
- Pydantic for validation
- Python typing

---

### 7. Logging Infrastructure (`logging.py`)

**Responsibility**: Centralized, structured logging with rich formatting

**Key Functions**:
- `get_logger(name)`: Get logger with "scalene_mcp." namespace
- `configure_logging()`: Set up logging with rich formatting

**Features**:
- Rich formatting for readable console output
- Rich tracebacks for better error visibility
- Integration with FastMCP settings
- Respects `SCALENE_LOG_LEVEL` environment variable

**Usage**:
```python
from scalene_mcp.logging import get_logger

logger = get_logger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

**Dependencies**:
- Python logging module
- rich library for formatting
- FastMCP settings

---

## Data Flow

### Profiling Workflow

```
User Request (script path, options)
    ↓
[FastMCP Server]
    ↓
[ScaleneProfiler]
    ├─ Validate inputs
    ├─ Create temp file
    ├─ Execute Scalene subprocess
    │   └─ Collect stdout/stderr
    ├─ Read temp file
    └─ Clean up (finally block)
    ↓
[ProfileParser]
    ├─ Read/parse JSON
    ├─ Handle Scalene quirks
    └─ Validate with Pydantic
    ↓
[ProfileResult] - Structured data
    ↓
Returns to LLM via MCP protocol
```

### Analysis Workflow

```
[ProfileResult]
    ↓
[ProfileAnalyzer]
    ├─ Extract metrics
    ├─ Calculate percentages
    ├─ Apply thresholds
    └─ Generate recommendations
    ↓
[AnalysisResult] with hotspots, bottlenecks, leaks
    ↓
Format for LLM consumption
    ↓
Returns to LLM via MCP protocol
```

### Comparison Workflow

```
[ProfileResult 1] + [ProfileResult 2]
    ↓
[ProfileComparator]
    ├─ Match lines by location
    ├─ Calculate deltas
    ├─ Compare with tolerance
    └─ Classify changes
    ↓
[ComparisonResult] with regressions/improvements
    ↓
Format for LLM consumption
    ↓
Returns to LLM via MCP protocol
```

---

## Key Design Decisions

### 0. Subprocess-Based Profiling (Scope Decision)

**Decision**: Use subprocess-based profiling (`python -m scalene run`) instead of direct Scalene API

**Rationale**:
- **Isolation**: Script execution isolated from profiler state
- **Reliability**: No Scalene state conflicts or memory leaks
- **Simplicity**: Don't manage Scalene's internal state machine
- **Safety**: Script crashes/hangs don't crash profiler
- **Resource Cleanup**: Automatic process termination
- **LLM Workflows**: Subprocess approach fits "script profiling" use case

**What This Supports**:
- ✅ Profile standalone scripts
- ✅ Profile packages (via entry point)
- ✅ Pass command-line arguments
- ✅ Full profiling feature set

**What This Doesn't Support**:
- ❌ In-process profiling (`Scalene.start()`/`stop()`)
- ❌ Function-level profiling without subprocess
- ❌ Process attachment/PID-based profiling

**Trade-offs**:
- Subprocess overhead (~1-5% extra time per profile)
- Temporary file I/O (mitigated by async)
- But gains isolation, reliability, and simplicity

**Future**: Could add in-process profiling in v1.1+ if needed:
```python
# Hypothetical future method
async def profile_function(func, *args, **kwargs) -> ProfileResult:
    """Profile a function using direct Scalene API."""
    # Would use Scalene.start()/stop() directly
    # Lower latency but more complex error handling
```

**See Also**: [SCALENE_MODES_ANALYSIS.md](../SCALENE_MODES_ANALYSIS.md) for detailed coverage analysis

---

### 1. Async/Await for Subprocess

**Decision**: Use `asyncio.create_subprocess_exec()` instead of subprocess.run()

**Rationale**:
- Non-blocking execution allows multiple profiles in parallel
- Better integration with async MCP server
- Allows timeouts without blocking thread

**Trade-offs**:
- More complex code than sync subprocess
- But worth it for production use

---

### 2. Temporary Files for Scalene Output

**Decision**: Use temp files instead of stdout/stderr redirection

**Rationale**:
- Scalene's JSON output can be mixed with script output
- `/dev/stdout` and `/dev/stderr` don't work reliably
- Temp files provide clean separation
- Easy cleanup with error handling

**Trade-offs**:
- Slight I/O overhead (mitigated by cleanup in finally block)
- But reliability is worth it

**Implementation**:
```python
output_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
output_path = Path(output_file.name)
output_file.close()

try:
    # Run Scalene, write to output_path
    result = parse_json_from_file(output_path)
finally:
    output_path.unlink(missing_ok=True)  # Cleanup
```

---

### 3. Pydantic for Validation

**Decision**: Use Pydantic BaseModel for all data structures

**Rationale**:
- Automatic JSON serialization
- Type validation
- Clear API contracts
- IDE autocomplete support

**Trade-offs**:
- Slight overhead for validation
- But catches errors early

---

### 4. In-Memory Profile Storage

**Decision**: Store profiles in memory (current session only)

**Rationale**:
- Simple implementation for now
- Suitable for interactive LLM sessions
- Easy to extend with persistent storage later

**Future**: Could add:
- SQLite for persistence
- Cloud storage (S3, etc.)
- Redis for distributed caching

---

### 5. Structured Logging

**Decision**: Use Python logging + rich formatting

**Rationale**:
- Standard Python approach
- Rich formatting for better visibility
- Easy to redirect/filter logs
- Integrates with FastMCP settings

**Benefits**:
- Debug issues without changing code
- Professional error messages for users
- Structured data for log aggregation

---

## Extension Points

### Adding a New Analysis Type

1. Add method to `ProfileAnalyzer`
2. Create corresponding Result model in `models.py`
3. Register tool in `server.py`
4. Add tests in `tests/test_analyzer.py`

**Example**:
```python
# In analyzer.py
def get_thread_contention(self, profile: ProfileResult) -> ThreadContention:
    """Analyze thread contention issues."""
    # Implementation
    pass

# In models.py
class ThreadContention(BaseModel):
    """Thread contention metrics."""
    # Fields
    pass

# In server.py
@server.tool()
async def analyze_threads(profile: ProfileResult) -> dict:
    """Analyze thread contention."""
    return analyzer.get_thread_contention(profile).dict()
```

---

### Adding a New Profiling Option

1. Add parameter to `ScaleneProfiler.profile_script()`
2. Add to Scalene command construction
3. Update parser if new JSON fields appear
4. Add parameter documentation
5. Update server tool descriptions
6. Add tests

---

### Adding Persistent Storage

1. Create `Storage` interface/ABC
2. Implement concrete storage (SQLite, S3, etc.)
3. Inject into components
4. Add configuration options

---

## Testing Strategy

### Unit Tests

- `test_models.py`: Validate all data models
- `test_parser.py`: Test JSON parsing and edge cases
- `test_profiler.py`: Test subprocess execution
- `test_analyzer.py`: Test analysis algorithms
- `test_comparator.py`: Test comparison logic

### Integration Tests

- `test_server.py`: Test MCP tools end-to-end
- Mock profiler to avoid slow actual profiling
- Test error handling
- Test tool parameter validation

### Code Coverage

Target: 85%+ coverage
Currently: 85.62% overall

---

## Performance Characteristics

### Profiling Overhead

- CPU profiling: 2-5x slowdown
- Memory profiling: 5-10x slowdown
- GPU profiling: 2-3x slowdown
- Reduced profile: 1-2x slowdown

### Memory Usage

- Per profile: ~1-10MB depending on code size
- Server memory: ~100MB base + profile storage

### Latency

- Parse JSON: <100ms
- Analyze: <50ms
- Compare: <100ms

---

## Security Considerations

### Code Execution

⚠️ **WARNING**: Scalene-MCP runs arbitrary Python code via subprocess

**Security Implications**:
- Only use with trusted code
- Run in isolated environment (container, VM)
- Don't expose publicly without authentication
- Consider sandboxing

### File Access

- Temp files are readable by process owner
- No additional permissions needed
- Cleanup happens automatically

### Resource Limits

- Timeout prevents infinite loops
- Memory/CPU limits external (OS-level)

---

## Deployment Architecture

### Development Mode

```
┌─────────────────┐
│  Claude Desktop │
│    (Client)     │
└────────┬────────┘
         │ MCP
         │ Protocol
         │
┌────────▼────────┐
│  Scalene-MCP    │
│  (Server)       │
└────────┬────────┘
         │ subprocess
         │
┌────────▼────────┐
│  Scalene CLI    │
│  (Profiler)     │
└─────────────────┘
```

### Production Deployment (Future)

```
┌─────────────────────┐
│  LLM Application    │
│ (claude-sdk)        │
└────────┬────────────┘
         │
         │ MCP
         │ Protocol
         │
    ┌────▼──────┐
    │   MCP     │
    │  Router   │
    └─┬──────┬──┘
      │      │
 ┌────▼─┐ ┌─▼─────┐
 │Scalene│ │Other  │
 │ MCP   │ │ MCPs  │
 │Server │ │ ...   │
 └───────┘ └───────┘
```

---

## Future Enhancements

### Short Term
- Persistent profile storage (SQLite)
- Profile export formats (CSV, HTML)
- Advanced filtering for hotspots
- Performance history tracking

### Medium Term
- Real-time profiling dashboard
- Automated regression detection
- Integration with CI/CD
- Performance benchmarking suite

### Long Term
- Distributed profiling
- ML-based anomaly detection
- Collaborative profiling
- Advanced visualization

---

## Glossary

| Term | Definition |
|------|-----------|
| **Hotspot** | Code location with high CPU/memory usage |
| **Bottleneck** | Performance issue with recommended fix |
| **Memory Leak** | Allocation velocity pattern suggesting leak |
| **Regression** | Performance degradation in later profile |
| **Improvement** | Performance optimization in later profile |
| **Velocity** | Allocation rate (MB/s) for leak detection |
| **Reduced Profile** | Output filtered to significant lines only |
| **Tolerance** | Percentage threshold for regression detection |

---

## References

- [Scalene GitHub](https://github.com/plasma-umass/scalene)
- [FastMCP Documentation](https://fastmcp.dev)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [Rich Documentation](https://rich.readthedocs.io)