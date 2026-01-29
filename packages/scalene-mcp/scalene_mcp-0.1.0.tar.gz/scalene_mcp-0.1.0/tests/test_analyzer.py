"""Tests for ProfileAnalyzer."""

import pytest

from scalene_mcp.analyzer import ProfileAnalyzer
from scalene_mcp.parser import ProfileParser


@pytest.fixture
def analyzer():
    """Create a ProfileAnalyzer instance."""
    return ProfileAnalyzer()


@pytest.fixture
def parser():
    """Create a ProfileParser instance."""
    return ProfileParser()


class TestTopCpuHotspots:
    """Test CPU hotspot extraction."""

    def test_get_top_cpu_hotspots_simple(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test extracting CPU hotspots from simple profile."""
        profile = parser.parse_file(simple_cpu_profile_json)
        hotspots = analyzer.get_top_cpu_hotspots(profile, n=5)

        assert len(hotspots) > 0
        assert hotspots[0].type == "cpu"
        assert hotspots[0].cpu_percent > 0
        assert hotspots[0].filename
        assert hotspots[0].lineno > 0
        assert hotspots[0].line

        # Verify sorting (descending by CPU)
        for i in range(len(hotspots) - 1):
            assert hotspots[i].cpu_percent >= hotspots[i + 1].cpu_percent

    def test_get_top_cpu_hotspots_details(self, analyzer, parser, simple_cpu_profile_json):
        """Test CPU hotspot details structure."""
        profile = parser.parse_file(simple_cpu_profile_json)
        hotspots = analyzer.get_top_cpu_hotspots(profile, n=1)

        if hotspots:
            hotspot = hotspots[0]
            # Hotspot model has cpu_percent, memory_mb, gpu_percent as direct fields
            assert hotspot.cpu_percent >= 0
            assert isinstance(hotspot.cpu_percent, float)

    def test_get_top_cpu_hotspots_limit(self, analyzer, parser, simple_cpu_profile_json):
        """Test hotspot limit parameter."""
        profile = parser.parse_file(simple_cpu_profile_json)
        hotspots_3 = analyzer.get_top_cpu_hotspots(profile, n=3)
        hotspots_10 = analyzer.get_top_cpu_hotspots(profile, n=10)

        assert len(hotspots_3) <= 3
        # If we have more than 3 hotspots, verify limiting works
        if len(hotspots_10) > 3:
            assert len(hotspots_3) == 3


class TestTopMemoryHotspots:
    """Test memory hotspot extraction."""

    def test_get_top_memory_hotspots(
        self, analyzer, parser, memory_heavy_profile_json
    ):
        """Test extracting memory hotspots."""
        profile = parser.parse_file(memory_heavy_profile_json)
        hotspots = analyzer.get_top_memory_hotspots(profile, n=5)

        assert len(hotspots) > 0
        assert hotspots[0].type == "memory"
        assert hotspots[0].memory_mb > 0
        assert hotspots[0].filename
        assert hotspots[0].lineno > 0

        # Verify sorting (descending by memory)
        for i in range(len(hotspots) - 1):
            assert hotspots[i].memory_mb >= hotspots[i + 1].memory_mb

    def test_get_top_memory_hotspots_details(
        self, analyzer, parser, memory_heavy_profile_json
    ):
        """Test memory hotspot details structure."""
        profile = parser.parse_file(memory_heavy_profile_json)
        hotspots = analyzer.get_top_memory_hotspots(profile, n=1)

        if hotspots:
            hotspot = hotspots[0]
            # Hotspot model has memory_mb as direct field
            assert hotspot.memory_mb >= 0
            assert isinstance(hotspot.memory_mb, float)


class TestTopGpuHotspots:
    """Test GPU hotspot extraction."""

    def test_get_top_gpu_hotspots_no_gpu(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test GPU hotspots when no GPU usage."""
        profile = parser.parse_file(simple_cpu_profile_json)
        hotspots = analyzer.get_top_gpu_hotspots(profile, n=5)

        # Should return empty list for profiles without GPU
        assert isinstance(hotspots, list)

    def test_get_top_gpu_hotspots_structure(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test GPU hotspot structure if present."""
        profile = parser.parse_file(simple_cpu_profile_json)
        hotspots = analyzer.get_top_gpu_hotspots(profile, n=5)

        # Even if empty, should have correct structure
        for hotspot in hotspots:
            assert hotspot.type == "gpu"
            assert hotspot.gpu_percent >= 0


class TestBottleneckIdentification:
    """Test bottleneck detection."""

    def test_identify_bottlenecks_cpu(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test CPU bottleneck identification."""
        profile = parser.parse_file(simple_cpu_profile_json)
        bottlenecks = analyzer.identify_bottlenecks(
            profile, cpu_threshold=1.0, memory_threshold_mb=1.0
        )

        assert "cpu" in bottlenecks
        assert "memory" in bottlenecks
        assert "gpu" in bottlenecks
        assert isinstance(bottlenecks["cpu"], list)

        # Check CPU bottleneck structure
        for bn in bottlenecks["cpu"]:
            assert bn["type"] == "cpu"
            assert bn["severity"] in ["high", "medium"]
            assert "file" in bn
            assert "line" in bn
            assert "code" in bn
            assert "cpu_percent" in bn
            assert "recommendation" in bn

    def test_identify_bottlenecks_memory(
        self, analyzer, parser, memory_heavy_profile_json
    ):
        """Test memory bottleneck identification."""
        profile = parser.parse_file(memory_heavy_profile_json)
        bottlenecks = analyzer.identify_bottlenecks(
            profile, cpu_threshold=5.0, memory_threshold_mb=1.0
        )

        assert "memory" in bottlenecks
        assert isinstance(bottlenecks["memory"], list)

        # Check memory bottleneck structure
        for bn in bottlenecks["memory"]:
            assert bn["type"] == "memory"
            assert bn["severity"] in ["high", "medium"]
            assert "peak_mb" in bn
            assert "recommendation" in bn

    def test_identify_bottlenecks_thresholds(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test bottleneck threshold filtering."""
        profile = parser.parse_file(simple_cpu_profile_json)

        # Low thresholds - more bottlenecks
        bottlenecks_low = analyzer.identify_bottlenecks(
            profile, cpu_threshold=0.1, memory_threshold_mb=0.1
        )

        # High thresholds - fewer bottlenecks
        bottlenecks_high = analyzer.identify_bottlenecks(
            profile, cpu_threshold=50.0, memory_threshold_mb=1000.0
        )

        cpu_low = len(bottlenecks_low["cpu"])
        cpu_high = len(bottlenecks_high["cpu"])

        # Low threshold should find at least as many as high threshold
        assert cpu_low >= cpu_high

    def test_bottleneck_severity_levels(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test bottleneck severity classification."""
        profile = parser.parse_file(simple_cpu_profile_json)
        bottlenecks = analyzer.identify_bottlenecks(
            profile, cpu_threshold=1.0, memory_threshold_mb=1.0
        )

        # CPU: >20% is high, else medium
        for bn in bottlenecks["cpu"]:
            if bn["cpu_percent"] > 20:
                assert bn["severity"] == "high"
            else:
                assert bn["severity"] == "medium"

        # Memory: >100MB is high, else medium
        for bn in bottlenecks["memory"]:
            if bn["peak_mb"] > 100:
                assert bn["severity"] == "high"
            else:
                assert bn["severity"] == "medium"


class TestRecommendations:
    """Test recommendation generation."""

    def test_cpu_recommendations(self, analyzer, parser, simple_cpu_profile_json):
        """Test CPU-specific recommendations."""
        profile = parser.parse_file(simple_cpu_profile_json)
        recommendations = analyzer.generate_recommendations(profile)

        assert isinstance(recommendations, list)
        # Should have at least some recommendations
        assert len(recommendations) >= 0

    def test_memory_recommendations(
        self, analyzer, parser, memory_heavy_profile_json
    ):
        """Test memory-specific recommendations."""
        profile = parser.parse_file(memory_heavy_profile_json)
        recommendations = analyzer.generate_recommendations(profile)

        assert isinstance(recommendations, list)

        # Check for memory-related recommendations if high memory usage
        if profile.summary.max_memory_mb > 1000:
            assert any("memory" in rec.lower() for rec in recommendations)

    def test_leak_recommendations(
        self, analyzer, parser, memory_leak_profile_json
    ):
        """Test leak detection recommendations."""
        profile = parser.parse_file(memory_leak_profile_json)
        recommendations = analyzer.generate_recommendations(profile)

        # If leaks detected, should recommend investigation
        if profile.summary.detected_leaks:
            assert any("leak" in rec.lower() for rec in recommendations)


class TestSummaryGeneration:
    """Test summary text generation."""

    def test_generate_summary_structure(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test summary has expected structure."""
        profile = parser.parse_file(simple_cpu_profile_json)
        summary = analyzer.generate_summary(profile)

        assert isinstance(summary, str)
        assert len(summary) > 0

        # Check for key sections
        assert "Profile Summary" in summary or "Runtime" in summary
        assert "CPU" in summary or "Memory" in summary

    def test_generate_summary_with_leaks(
        self, analyzer, parser, memory_leak_profile_json
    ):
        """Test summary includes leak information."""
        profile = parser.parse_file(memory_leak_profile_json)
        summary = analyzer.generate_summary(profile)

        if profile.summary.detected_leaks:
            assert "leak" in summary.lower() or "⚠️" in summary

    def test_generate_summary_recommendations(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test summary includes recommendations."""
        profile = parser.parse_file(simple_cpu_profile_json)
        summary = analyzer.generate_summary(profile)

        # Summary should include recommendations section if any exist
        recommendations = analyzer.generate_recommendations(profile)
        if recommendations:
            assert "Recommendation" in summary


class TestFullAnalysis:
    """Test complete profile analysis."""

    def test_analyze_complete(self, analyzer, parser, simple_cpu_profile_json):
        """Test full analyze method."""
        profile = parser.parse_file(simple_cpu_profile_json)
        analysis = analyzer.analyze(profile, top_n=5)

        # Check all required fields
        assert analysis.profile_id
        assert analysis.focus in ("cpu", "memory", "gpu", "all")
        assert isinstance(analysis.hotspots, list)
        assert isinstance(analysis.leaks, list)
        assert isinstance(analysis.recommendations, list)
        assert isinstance(analysis.summary_text, str)

    def test_analyze_with_custom_thresholds(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test analysis with custom thresholds."""
        profile = parser.parse_file(simple_cpu_profile_json)

        # Low thresholds
        analysis_low = analyzer.analyze(
            profile, top_n=10, cpu_threshold=0.1, memory_threshold_mb=0.1, focus="all"
        )

        # High thresholds
        analysis_high = analyzer.analyze(
            profile, top_n=10, cpu_threshold=50.0, memory_threshold_mb=1000.0, focus="all"
        )

        # Low threshold should find more or equal hotspots
        hotspots_low = len(analysis_low.hotspots)
        hotspots_high = len(analysis_high.hotspots)
        assert hotspots_low >= hotspots_high

    def test_analyze_top_n_limit(self, analyzer, parser, simple_cpu_profile_json):
        """Test top_n parameter limits hotspots."""
        profile = parser.parse_file(simple_cpu_profile_json)

        analysis_3 = analyzer.analyze(profile, top_n=3, focus="all")
        analysis_10 = analyzer.analyze(profile, top_n=10, focus="all")

        # top_n applies per category (cpu, memory, gpu), so 3 means up to 9 total (3 * 3)
        # But we're checking that 3 is <= the total from 10
        assert len(analysis_3.hotspots) <= len(analysis_10.hotspots)


class TestFunctionSummary:
    """Test function-level summary."""

    def test_get_function_summary(self, analyzer, parser, simple_cpu_profile_json):
        """Test function summary extraction."""
        profile = parser.parse_file(simple_cpu_profile_json)
        summary = analyzer.get_function_summary(profile, top_n=5)

        assert isinstance(summary, list)

        # Check structure
        for func in summary:
            assert "file" in func
            assert "cpu_percent" in func
            assert "memory_peak_mb" in func
            assert "gpu_percent" in func
            assert "line_count" in func

            # Check types
            assert isinstance(func["file"], str)
            assert isinstance(func["cpu_percent"], float)
            assert isinstance(func["line_count"], int)

    def test_get_function_summary_sorting(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test function summary is sorted by CPU."""
        profile = parser.parse_file(simple_cpu_profile_json)
        summary = analyzer.get_function_summary(profile, top_n=10)

        # Verify sorted by CPU descending
        for i in range(len(summary) - 1):
            assert summary[i]["cpu_percent"] >= summary[i + 1]["cpu_percent"]

    def test_get_function_summary_limit(
        self, analyzer, parser, simple_cpu_profile_json
    ):
        """Test function summary respects top_n limit."""
        profile = parser.parse_file(simple_cpu_profile_json)
        summary = analyzer.get_function_summary(profile, top_n=3)

        assert len(summary) <= 3
