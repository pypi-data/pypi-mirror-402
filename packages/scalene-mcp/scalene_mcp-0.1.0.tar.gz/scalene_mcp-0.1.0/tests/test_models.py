"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from scalene_mcp.models import (
    FileMetrics,
    FunctionMetrics,
    Hotspot,
    LineMetrics,
    MemoryLeak,
    ProfileAnalysis,
    ProfileComparison,
    ProfileResult,
    ProfileResultSummary,
    ProfileSummary,
)


class TestLineMetrics:
    """Tests for LineMetrics model."""

    def test_create_basic(self):
        """Test creating a basic LineMetrics."""
        line = LineMetrics(lineno=10, line="x = 1")
        assert line.lineno == 10
        assert line.line == "x = 1"
        assert line.total_cpu_percent == 0.0

    def test_total_cpu_percent(self):
        """Test total_cpu_percent property calculation."""
        line = LineMetrics(
            lineno=10,
            line="x = 1",
            cpu_percent_python=10.5,
            cpu_percent_c=5.2,
            cpu_percent_system=2.3,
        )
        assert line.total_cpu_percent == 18.0

    def test_validation_cpu_range(self):
        """Test that CPU percentages must be 0-100."""
        with pytest.raises(ValidationError):
            LineMetrics(lineno=1, line="x = 1", cpu_percent_python=150.0)

    def test_validation_negative_memory(self):
        """Test that memory values cannot be negative."""
        with pytest.raises(ValidationError):
            LineMetrics(lineno=1, line="x = 1", memory_peak_mb=-10.0)

    def test_frozen(self):
        """Test that LineMetrics is frozen."""
        line = LineMetrics(lineno=1, line="x = 1")
        with pytest.raises(ValidationError):
            line.lineno = 2


class TestMemoryLeak:
    """Tests for MemoryLeak model."""

    def test_create_basic(self):
        """Test creating a MemoryLeak."""
        leak = MemoryLeak(
            filename="test.py",
            lineno=42,
            line="leaked = []",
            likelihood=0.85,
            velocity_mb_s=10.5,
        )
        assert leak.filename == "test.py"
        assert leak.lineno == 42
        assert leak.likelihood == 0.85
        assert leak.velocity_mb_s == 10.5

    def test_validation_likelihood_range(self):
        """Test that likelihood must be 0-1."""
        with pytest.raises(ValidationError):
            MemoryLeak(
                filename="test.py",
                lineno=1,
                line="x = 1",
                likelihood=1.5,
                velocity_mb_s=10.0,
            )

    def test_validation_negative_velocity(self):
        """Test that velocity cannot be negative."""
        with pytest.raises(ValidationError):
            MemoryLeak(
                filename="test.py",
                lineno=1,
                line="x = 1",
                likelihood=0.5,
                velocity_mb_s=-5.0,
            )

    def test_frozen(self):
        """Test that MemoryLeak is frozen."""
        leak = MemoryLeak(
            filename="test.py",
            lineno=1,
            line="x = 1",
            likelihood=0.5,
            velocity_mb_s=5.0,
        )
        with pytest.raises(ValidationError):
            leak.likelihood = 0.8


class TestFunctionMetrics:
    """Tests for FunctionMetrics model."""

    def test_create_basic(self):
        """Test creating a FunctionMetrics."""
        func = FunctionMetrics(
            name="my_function", first_lineno=10, last_lineno=20
        )
        assert func.name == "my_function"
        assert func.first_lineno == 10
        assert func.last_lineno == 20
        assert len(func.lines) == 0

    def test_with_lines(self):
        """Test FunctionMetrics with LineMetrics."""
        lines = [
            LineMetrics(lineno=10, line="def foo():", cpu_percent_python=5.0),
            LineMetrics(lineno=11, line="    return 1", cpu_percent_python=2.0),
        ]
        func = FunctionMetrics(
            name="foo", first_lineno=10, last_lineno=11, lines=lines
        )
        assert len(func.lines) == 2
        assert func.lines[0].lineno == 10


class TestFileMetrics:
    """Tests for FileMetrics model."""

    def test_create_basic(self):
        """Test creating a FileMetrics."""
        file = FileMetrics(filename="test.py")
        assert file.filename == "test.py"
        assert len(file.functions) == 0
        assert len(file.lines) == 0
        assert len(file.leaks) == 0

    def test_with_leaks(self):
        """Test FileMetrics with memory leaks."""
        leaks = [
            MemoryLeak(
                filename="test.py",
                lineno=10,
                line="x = []",
                likelihood=0.9,
                velocity_mb_s=5.0,
            )
        ]
        file = FileMetrics(filename="test.py", leaks=leaks)
        assert len(file.leaks) == 1
        assert file.leaks[0].likelihood == 0.9


class TestHotspot:
    """Tests for Hotspot model."""

    def test_create_cpu_hotspot(self):
        """Test creating a CPU hotspot."""
        hotspot = Hotspot(
            type="cpu",
            severity="high",
            filename="test.py",
            lineno=42,
            line="x = heavy_computation()",
            cpu_percent=45.5,
        )
        assert hotspot.type == "cpu"
        assert hotspot.severity == "high"
        assert hotspot.cpu_percent == 45.5

    def test_create_memory_hotspot(self):
        """Test creating a memory hotspot."""
        hotspot = Hotspot(
            type="memory",
            severity="critical",
            filename="test.py",
            lineno=100,
            line="data = [0] * 10_000_000",
            memory_mb=500.0,
        )
        assert hotspot.type == "memory"
        assert hotspot.memory_mb == 500.0

    def test_with_context(self):
        """Test hotspot with context information."""
        hotspot = Hotspot(
            type="cpu",
            severity="medium",
            filename="test.py",
            lineno=50,
            line="for i in range(n):",
            cpu_percent=25.0,
            function_name="process_data",
            is_in_loop=True,
            recommendation="Consider vectorizing this loop",
        )
        assert hotspot.function_name == "process_data"
        assert hotspot.is_in_loop is True
        assert "vectorizing" in hotspot.recommendation


class TestProfileSummary:
    """Tests for ProfileSummary model."""

    def test_create_basic(self):
        """Test creating a basic ProfileSummary."""
        summary = ProfileSummary(
            profile_id="prof_001",
            timestamp=1234567890.0,
            elapsed_time_sec=2.5,
            max_memory_mb=100.0,
            total_allocations_mb=50.0,
            allocation_count=1000,
            total_cpu_samples=500,
            python_time_percent=80.0,
            native_time_percent=15.0,
            system_time_percent=5.0,
            files_profiled=["test.py"],
            lines_profiled=50,
        )
        assert summary.profile_id == "prof_001"
        assert summary.elapsed_time_sec == 2.5
        assert not summary.gpu_enabled
        assert not summary.has_performance_issues

    def test_with_hotspots(self):
        """Test ProfileSummary with hotspots."""
        hotspot = Hotspot(
            type="cpu",
            severity="high",
            filename="test.py",
            lineno=10,
            line="x = 1",
            cpu_percent=50.0,
        )
        summary = ProfileSummary(
            profile_id="prof_001",
            timestamp=1234567890.0,
            elapsed_time_sec=2.5,
            max_memory_mb=100.0,
            total_allocations_mb=50.0,
            allocation_count=1000,
            total_cpu_samples=500,
            python_time_percent=80.0,
            native_time_percent=15.0,
            system_time_percent=5.0,
            files_profiled=["test.py"],
            lines_profiled=50,
            top_cpu_hotspots=[hotspot],
        )
        assert len(summary.top_cpu_hotspots) == 1

    def test_with_gpu(self):
        """Test ProfileSummary with GPU enabled."""
        summary = ProfileSummary(
            profile_id="prof_001",
            timestamp=1234567890.0,
            elapsed_time_sec=2.5,
            max_memory_mb=100.0,
            total_allocations_mb=50.0,
            allocation_count=1000,
            total_cpu_samples=500,
            python_time_percent=60.0,
            native_time_percent=10.0,
            system_time_percent=5.0,
            files_profiled=["test.py"],
            lines_profiled=50,
            gpu_enabled=True,
            gpu_utilization_percent=75.5,
        )
        assert summary.gpu_enabled
        assert summary.gpu_utilization_percent == 75.5


class TestProfileAnalysis:
    """Tests for ProfileAnalysis model."""

    def test_create_basic(self):
        """Test creating a ProfileAnalysis."""
        analysis = ProfileAnalysis(
            profile_id="prof_001",
            focus="cpu",
            hotspots=[],
            leaks=[],
            summary_text="No significant issues found.",
        )
        assert analysis.profile_id == "prof_001"
        assert analysis.focus == "cpu"
        assert len(analysis.hotspots) == 0

    def test_with_aggregations(self):
        """Test ProfileAnalysis with aggregations."""
        analysis = ProfileAnalysis(
            profile_id="prof_001",
            focus="all",
            hotspots=[],
            leaks=[],
            by_file={"test.py": 45.5, "utils.py": 25.3},
            by_function={"main": 30.0, "helper": 15.5},
            summary_text="Performance distributed across multiple files.",
        )
        assert len(analysis.by_file) == 2
        assert analysis.by_file["test.py"] == 45.5


class TestProfileComparison:
    """Tests for ProfileComparison model."""

    def test_create_improvement(self):
        """Test comparison showing improvement."""
        comparison = ProfileComparison(
            before_id="prof_001",
            after_id="prof_002",
            runtime_before_sec=5.0,
            runtime_after_sec=3.0,
            runtime_change_percent=-40.0,
            runtime_improved=True,
            memory_before_mb=200.0,
            memory_after_mb=150.0,
            memory_change_percent=-25.0,
            memory_improved=True,
            cpu_before_samples=1000,
            cpu_after_samples=600,
            cpu_change_percent=-40.0,
            cpu_improved=True,
            improvements=["Reduced runtime by 40%", "Reduced memory by 25%"],
            overall_improved=True,
            summary_text="Significant performance improvements across the board.",
        )
        assert comparison.runtime_improved
        assert comparison.memory_improved
        assert comparison.overall_improved
        assert len(comparison.improvements) == 2

    def test_create_regression(self):
        """Test comparison showing regression."""
        comparison = ProfileComparison(
            before_id="prof_001",
            after_id="prof_002",
            runtime_before_sec=2.0,
            runtime_after_sec=3.0,
            runtime_change_percent=50.0,
            runtime_improved=False,
            memory_before_mb=100.0,
            memory_after_mb=150.0,
            memory_change_percent=50.0,
            memory_improved=False,
            cpu_before_samples=500,
            cpu_after_samples=750,
            cpu_change_percent=50.0,
            cpu_improved=False,
            regressions=["Runtime increased by 50%"],
            overall_improved=False,
            summary_text="Performance regressions detected.",
        )
        assert not comparison.overall_improved
        assert len(comparison.regressions) == 1


class TestProfileResult:
    """Tests for ProfileResult model."""

    def test_create_basic(self):
        """Test creating a ProfileResult."""
        summary = ProfileSummary(
            profile_id="prof_001",
            timestamp=1234567890.0,
            elapsed_time_sec=2.5,
            max_memory_mb=100.0,
            total_allocations_mb=50.0,
            allocation_count=1000,
            total_cpu_samples=500,
            python_time_percent=80.0,
            native_time_percent=15.0,
            system_time_percent=5.0,
            files_profiled=["test.py"],
            lines_profiled=50,
        )

        result = ProfileResult(
            profile_id="prof_001",
            timestamp=1234567890.0,
            summary=summary,
            files={"test.py": FileMetrics(filename="test.py")},
            scalene_version="1.5.45",
        )

        assert result.profile_id == "prof_001"
        assert result.scalene_version == "1.5.45"
        assert "test.py" in result.files


class TestProfileResultSummary:
    """Tests for ProfileResultSummary (MCP tool response)."""

    def test_create_basic(self):
        """Test creating a ProfileResultSummary."""
        summary = ProfileResultSummary(
            profile_id="prof_001",
            elapsed_time_sec=2.5,
            max_memory_mb=100.0,
            files_profiled=2,
            summary_text="Profiling completed successfully.",
        )
        assert summary.profile_id == "prof_001"
        assert summary.success
        assert summary.leak_count == 0

    def test_with_issues(self):
        """Test ProfileResultSummary with detected issues."""
        summary = ProfileResultSummary(
            profile_id="prof_001",
            elapsed_time_sec=5.0,
            max_memory_mb=500.0,
            files_profiled=3,
            top_cpu_lines=[{"line": 42, "percent": 45.5}],
            top_memory_lines=[{"line": 100, "mb": 250.0}],
            leak_count=2,
            summary_text="Found performance issues and memory leaks.",
            suggested_actions=[
                "Investigate line 42 for CPU usage",
                "Check memory allocation at line 100",
            ],
        )
        assert len(summary.top_cpu_lines) == 1
        assert summary.leak_count == 2
        assert len(summary.suggested_actions) == 2
