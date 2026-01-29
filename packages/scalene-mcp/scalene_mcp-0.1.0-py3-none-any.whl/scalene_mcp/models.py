"""Pydantic models for Scalene profiling data.

These models provide type-safe interfaces to Scalene's JSON output
and our own analysis results.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Raw Scalene Data Models (mirror Scalene's JSON schema)
# ============================================================================


class LineMetrics(BaseModel):
    """Profiling metrics for a single line of code."""

    model_config = ConfigDict(frozen=True)

    lineno: int = Field(..., description="Line number")
    line: str = Field(..., description="Source code")

    # CPU metrics
    cpu_percent_python: float = Field(0.0, ge=0, le=100)
    cpu_percent_c: float = Field(0.0, ge=0, le=100)
    cpu_percent_system: float = Field(0.0, ge=0, le=100)
    cpu_samples: list[float] = Field(default_factory=list)

    # GPU metrics
    gpu_percent: float = Field(0.0, ge=0, le=100)

    # Memory metrics
    memory_peak_mb: float = Field(0.0, ge=0)
    memory_average_mb: float = Field(0.0, ge=0)
    memory_alloc_mb: float = Field(0.0, ge=0)
    memory_alloc_count: int = Field(0, ge=0)
    memory_samples: list[list[float]] = Field(default_factory=list)

    # Utilization
    cpu_utilization: float = Field(0.0, ge=0, le=1)
    core_utilization: float = Field(0.0, ge=0)

    # Loop info
    loop_start: int | None = None
    loop_end: int | None = None

    @property
    def total_cpu_percent(self) -> float:
        """Total CPU percentage across all categories."""
        return self.cpu_percent_python + self.cpu_percent_c + self.cpu_percent_system


class MemoryLeak(BaseModel):
    """Memory leak detection result from Scalene.
    
    Mirrors Scalene's LeakInfo structure exactly.
    """

    model_config = ConfigDict(frozen=True)

    filename: str
    lineno: int
    line: str
    likelihood: float = Field(..., ge=0, le=1, description="Leak probability (0-1)")
    velocity_mb_s: float = Field(..., ge=0, description="Leak rate in MB/s")


class FunctionMetrics(BaseModel):
    """Profiling metrics for a function."""

    model_config = ConfigDict(frozen=True)

    name: str
    first_lineno: int
    last_lineno: int

    total_cpu_percent: float = Field(0.0, ge=0, le=100.1)  # Allow slight float overflow
    total_memory_mb: float = Field(0.0, ge=0)

    lines: list[LineMetrics] = Field(default_factory=list)


class FileMetrics(BaseModel):
    """Profiling metrics for a file."""

    model_config = ConfigDict(frozen=True)

    filename: str
    total_cpu_percent: float = Field(0.0, ge=0, le=100.1)  # Allow slight float overflow

    functions: list[FunctionMetrics] = Field(default_factory=list)
    lines: list[LineMetrics] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    leaks: list[MemoryLeak] = Field(default_factory=list)


# ============================================================================
# Analysis Result Models (our own enriched data)
# ============================================================================


class Hotspot(BaseModel):
    """A performance hotspot (CPU or memory)."""

    model_config = ConfigDict(frozen=True)

    type: Literal["cpu", "memory", "gpu"]
    severity: Literal["low", "medium", "high", "critical"]

    filename: str
    lineno: int
    line: str

    # Metrics
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    gpu_percent: float = 0.0

    # Context
    function_name: str | None = None
    is_in_loop: bool = False

    # Recommendation
    recommendation: str | None = None


class ProfileSummary(BaseModel):
    """High-level summary of profiling results."""

    # Metadata
    profile_id: str
    timestamp: float

    # Runtime
    elapsed_time_sec: float

    # Memory
    max_memory_mb: float
    total_allocations_mb: float
    allocation_count: int

    # CPU
    total_cpu_samples: int
    python_time_percent: float
    native_time_percent: float
    system_time_percent: float

    # GPU (optional)
    gpu_enabled: bool = False
    gpu_utilization_percent: float = 0.0

    # Files
    files_profiled: list[str]
    lines_profiled: int

    # Top issues
    top_cpu_hotspots: list[Hotspot] = Field(default_factory=list)
    top_memory_hotspots: list[Hotspot] = Field(default_factory=list)
    detected_leaks: list[MemoryLeak] = Field(default_factory=list)

    # Analysis
    has_performance_issues: bool = False
    has_memory_leaks: bool = False
    recommendations_count: int = 0


class ProfileAnalysis(BaseModel):
    """Detailed analysis of a profile."""

    profile_id: str
    focus: Literal["cpu", "memory", "gpu", "all"]

    # Filtered results
    hotspots: list[Hotspot]
    leaks: list[MemoryLeak]

    # Aggregations
    by_file: dict[str, float] = Field(default_factory=dict)
    by_function: dict[str, float] = Field(default_factory=dict)

    # Insights
    recommendations: list[str] = Field(default_factory=list)
    summary_text: str


class ProfileComparison(BaseModel):
    """Comparison between two profiles."""

    before_id: str
    after_id: str

    # Runtime changes
    runtime_before_sec: float
    runtime_after_sec: float
    runtime_change_percent: float
    runtime_improved: bool

    # Memory changes
    memory_before_mb: float
    memory_after_mb: float
    memory_change_percent: float
    memory_improved: bool

    # CPU changes
    cpu_before_samples: int
    cpu_after_samples: int
    cpu_change_percent: float
    cpu_improved: bool

    # Detailed changes
    improvements: list[str] = Field(default_factory=list)
    regressions: list[str] = Field(default_factory=list)

    # Overall
    overall_improved: bool
    summary_text: str


class ProfileResult(BaseModel):
    """Complete profiling result with all data."""

    # Identity
    profile_id: str
    timestamp: float

    # Summary
    summary: ProfileSummary

    # Raw data
    files: dict[str, FileMetrics]

    # Metadata
    scalene_version: str
    scalene_args: dict[str, Any] = Field(default_factory=dict)
    raw_json_path: str | None = None


# ============================================================================
# MCP Tool Response Models
# ============================================================================


class ProfileResultSummary(BaseModel):
    """Response from profile tool."""

    profile_id: str
    success: bool = True

    # Quick stats
    elapsed_time_sec: float
    max_memory_mb: float
    files_profiled: int

    # Top issues (preview)
    top_cpu_lines: list[dict[str, Any]] = Field(default_factory=list)
    top_memory_lines: list[dict[str, Any]] = Field(default_factory=list)
    leak_count: int = 0

    # Text summary for LLM
    summary_text: str

    # Next steps
    suggested_actions: list[str] = Field(default_factory=list)
