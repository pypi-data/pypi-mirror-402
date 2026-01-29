"""Tests for FastMCP server tools."""

import pytest
from unittest.mock import AsyncMock, patch

from scalene_mcp.models import ProfileResult
from scalene_mcp.parser import ProfileParser
from scalene_mcp.server import (
    analyze,
    analyze_profile,
    compare_profiles,
    get_bottlenecks,
    get_cpu_hotspots,
    get_file_details,
    get_function_summary,
    get_gpu_hotspots,
    get_memory_hotspots,
    get_memory_leaks,
    get_recommendations,
    list_profiles,
    profile,
    profile_code,
    profile_script,
    recent_profiles,
)


@pytest.fixture(autouse=True)
def clear_profiles():
    """Clear profiles before each test."""
    recent_profiles.clear()
    yield
    recent_profiles.clear()


@pytest.fixture
async def simple_profile_id(simple_cpu_profile_json):
    """Create a simple profile and return its ID."""
    # Load the JSON profile and mock the profiler
    parser = ProfileParser()
    profile = parser.parse_file(simple_cpu_profile_json)
    
    with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
        mock_profile.return_value = profile
        result = await profile_script(str(simple_cpu_profile_json))
        return result["profile_id"]


@pytest.fixture
async def memory_leak_profile_id(memory_leak_profile_json):
    """Create a memory leak profile and return its ID."""
    # Load the JSON profile and mock the profiler
    parser = ProfileParser()
    profile = parser.parse_file(memory_leak_profile_json)
    
    with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
        mock_profile.return_value = profile
        result = await profile_script(str(memory_leak_profile_json))
        return result["profile_id"]


class TestProfileScript:
    """Tests for profile_script tool."""

    async def test_profile_nonexistent_script(self):
        """Test profiling a nonexistent script."""
        with pytest.raises(FileNotFoundError):
            await profile_script("/nonexistent/script.py")

    async def test_profile_existing_script(self, simple_cpu_profile_json):
        """Test profiling an existing script."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            result = await profile_script(str(simple_cpu_profile_json))

        assert "profile_id" in result
        assert "summary" in result
        assert "text_summary" in result
        assert result["profile_id"] in recent_profiles

    async def test_profile_with_args(self, simple_cpu_profile_json):
        """Test profiling with script arguments."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            result = await profile_script(
                str(simple_cpu_profile_json), script_args=["--arg1", "value1"]
            )

        assert "profile_id" in result
        assert result["profile_id"] in recent_profiles

    async def test_cpu_only_mode(self, simple_cpu_profile_json):
        """Test CPU-only profiling mode."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            result = await profile_script(str(simple_cpu_profile_json), cpu_only=True)

        assert "profile_id" in result
        assert result["profile_id"] in recent_profiles

    async def test_gpu_mode(self, simple_cpu_profile_json):
        """Test GPU profiling mode."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            result = await profile_script(
                str(simple_cpu_profile_json), include_gpu=True
            )

        assert "profile_id" in result
        assert result["profile_id"] in recent_profiles


class TestProfileCode:
    """Tests for profile_code tool."""

    async def test_profile_simple_code(self, simple_cpu_profile_json):
        """Test profiling simple code snippet."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(10)
"""
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_code", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            result = await profile_code(code)

        assert "profile_id" in result
        assert "summary" in result
        assert "text_summary" in result
        assert result["profile_id"] in recent_profiles

    async def test_cpu_only_code(self, simple_cpu_profile_json):
        """Test CPU-only code profiling."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        code = "x = sum(range(1000))"
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_code", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            result = await profile_code(code, cpu_only=True)

        assert "profile_id" in result
        assert result["profile_id"] in recent_profiles


class TestAnalyzeProfile:
    """Tests for analyze_profile tool."""

    async def test_analyze_missing_profile(self):
        """Test analyzing a nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await analyze_profile("nonexistent_id")

    async def test_analyze_existing_profile(self, simple_profile_id):
        """Test analyzing an existing profile."""
        result = await analyze_profile(simple_profile_id)

        assert "focus" in result
        assert "hotspots" in result
        assert "recommendations" in result

    async def test_analyze_with_focus(self, simple_profile_id):
        """Test analyzing with specific focus."""
        result = await analyze_profile(simple_profile_id, focus="cpu")

        assert result["focus"] == "cpu"
        assert "hotspots" in result

    async def test_analyze_with_thresholds(self, simple_profile_id):
        """Test analyzing with custom thresholds."""
        result = await analyze_profile(
            simple_profile_id, cpu_threshold=10.0, memory_threshold_mb=50.0
        )

        assert "hotspots" in result
        assert "recommendations" in result


class TestGetCpuHotspots:
    """Tests for get_cpu_hotspots tool."""

    async def test_missing_profile(self):
        """Test getting hotspots from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_cpu_hotspots("nonexistent_id")

    async def test_get_cpu_hotspots(self, simple_profile_id):
        """Test getting CPU hotspots."""
        hotspots = await get_cpu_hotspots(simple_profile_id)

        assert isinstance(hotspots, list)
        # Check structure if hotspots exist
        if hotspots:
            assert "type" in hotspots[0]
            assert "filename" in hotspots[0]

    async def test_custom_top_n(self, simple_profile_id):
        """Test getting top N hotspots."""
        hotspots = await get_cpu_hotspots(simple_profile_id, top_n=5)

        assert isinstance(hotspots, list)
        assert len(hotspots) <= 5


class TestGetMemoryHotspots:
    """Tests for get_memory_hotspots tool."""

    async def test_missing_profile(self):
        """Test getting hotspots from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_memory_hotspots("nonexistent_id")

    async def test_get_memory_hotspots(self, simple_profile_id):
        """Test getting memory hotspots."""
        hotspots = await get_memory_hotspots(simple_profile_id)

        assert isinstance(hotspots, list)

    async def test_memory_hotspots_with_leak_profile(self, memory_leak_profile_id):
        """Test memory hotspots with leak profile."""
        hotspots = await get_memory_hotspots(memory_leak_profile_id)

        assert isinstance(hotspots, list)
        # Leak profile should have memory hotspots
        if hotspots:
            assert "type" in hotspots[0]
            assert hotspots[0]["type"] == "memory"


class TestGetGpuHotspots:
    """Tests for get_gpu_hotspots tool."""

    async def test_missing_profile(self):
        """Test getting GPU hotspots from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_gpu_hotspots("nonexistent_id")

    async def test_get_gpu_hotspots(self, simple_profile_id):
        """Test getting GPU hotspots."""
        hotspots = await get_gpu_hotspots(simple_profile_id)

        assert isinstance(hotspots, list)
        # Most profiles won't have GPU data


class TestGetBottlenecks:
    """Tests for get_bottlenecks tool."""

    async def test_missing_profile(self):
        """Test getting bottlenecks from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_bottlenecks("nonexistent_id")

    async def test_get_bottlenecks(self, simple_profile_id):
        """Test getting bottlenecks."""
        result = await get_bottlenecks(simple_profile_id)

        assert isinstance(result, dict)
        assert "cpu" in result
        assert "memory" in result
        assert "gpu" in result

    async def test_bottlenecks_with_thresholds(self, simple_profile_id):
        """Test bottlenecks with custom thresholds."""
        result = await get_bottlenecks(
            simple_profile_id, cpu_threshold=20.0, memory_threshold_mb=100.0
        )

        assert isinstance(result, dict)


class TestGetMemoryLeaks:
    """Tests for get_memory_leaks tool."""

    async def test_missing_profile(self):
        """Test getting leaks from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_memory_leaks("nonexistent_id")

    async def test_get_memory_leaks(self, simple_profile_id):
        """Test getting memory leaks."""
        leaks = await get_memory_leaks(simple_profile_id)

        assert isinstance(leaks, list)

    async def test_memory_leaks_with_leak_profile(self, memory_leak_profile_id):
        """Test memory leaks with leak profile."""
        leaks = await get_memory_leaks(memory_leak_profile_id)

        assert isinstance(leaks, list)


class TestCompareProfiles:
    """Tests for compare_profiles tool."""

    async def test_missing_before_profile(self, simple_profile_id):
        """Test comparison with missing before profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await compare_profiles("nonexistent_id", simple_profile_id)

    async def test_missing_after_profile(self, simple_profile_id):
        """Test comparison with missing after profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await compare_profiles(simple_profile_id, "nonexistent_id")

    async def test_compare_two_profiles(
        self, simple_profile_id, memory_leak_profile_id
    ):
        """Test comparing two profiles."""
        result = await compare_profiles(simple_profile_id, memory_leak_profile_id)

        assert isinstance(result, dict)
        assert "before_id" in result
        assert "after_id" in result
        assert "improvements" in result
        assert "regressions" in result
        assert "runtime_change_percent" in result
        assert "memory_change_percent" in result

    async def test_compare_identical_profiles(self, simple_profile_id):
        """Test comparing profile with itself."""
        result = await compare_profiles(simple_profile_id, simple_profile_id)

        assert isinstance(result, dict)
        # Comparing identical profiles should show no changes
        assert len(result["improvements"]) == 0
        assert len(result["regressions"]) == 0


class TestGetFileDetails:
    """Tests for get_file_details tool."""

    async def test_missing_profile(self):
        """Test getting file details from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_file_details("nonexistent_id", "test.py")

    async def test_missing_file(self, simple_profile_id):
        """Test getting nonexistent file from profile."""
        with pytest.raises(ValueError, match="File not in profile"):
            await get_file_details(simple_profile_id, "nonexistent.py")

    async def test_get_file_details(self, simple_profile_id):
        """Test getting file details."""
        # Get profile to check available files
        profile = recent_profiles[simple_profile_id]
        if not profile.files:
            pytest.skip("No files in profile")

        filename = next(iter(profile.files.keys()))
        result = await get_file_details(simple_profile_id, filename)

        assert isinstance(result, dict)
        assert "lines" in result


class TestListProfiles:
    """Tests for list_profiles tool."""

    async def test_list_empty_profiles(self):
        """Test listing when no profiles exist."""
        result = await list_profiles()

        assert isinstance(result, list)
        assert len(result) == 0

    async def test_list_with_profiles(self, simple_profile_id, memory_leak_profile_id):
        """Test listing with existing profiles."""
        result = await list_profiles()

        assert isinstance(result, list)
        assert len(result) == 2
        assert simple_profile_id in result
        assert memory_leak_profile_id in result


class TestGetRecommendations:
    """Tests for get_recommendations tool."""

    async def test_missing_profile(self):
        """Test getting recommendations from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_recommendations("nonexistent_id")

    async def test_get_recommendations(self, simple_profile_id):
        """Test getting recommendations."""
        result = await get_recommendations(simple_profile_id)

        assert isinstance(result, list)

    async def test_recommendations_with_leak_profile(self, memory_leak_profile_id):
        """Test recommendations with leak profile."""
        result = await get_recommendations(memory_leak_profile_id)

        assert isinstance(result, list)


class TestGetFunctionSummary:
    """Tests for get_function_summary tool."""

    async def test_missing_profile(self):
        """Test getting function summary from nonexistent profile."""
        with pytest.raises(ValueError, match="Profile not found"):
            await get_function_summary("nonexistent_id")

    async def test_get_function_summary(self, simple_profile_id):
        """Test getting function summary."""
        result = await get_function_summary(simple_profile_id)

        assert isinstance(result, list)

    async def test_function_summary_top_n(self, simple_profile_id):
        """Test function summary with top_n."""
        result = await get_function_summary(simple_profile_id, top_n=5)

        assert isinstance(result, list)
        assert len(result) <= 5


class TestProfileStorage:
    """Tests for profile storage."""

    async def test_profile_storage_increments(
        self, simple_cpu_profile_json, memory_leak_profile_json
    ):
        """Test that profile IDs increment correctly."""
        parser = ProfileParser()
        profile1 = parser.parse_file(simple_cpu_profile_json)
        profile2 = parser.parse_file(memory_leak_profile_json)
        
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile1
            result1 = await profile_script(str(simple_cpu_profile_json))
            mock_profile.return_value = profile2
            result2 = await profile_script(str(memory_leak_profile_json))

        assert result1["profile_id"] != result2["profile_id"]
        assert len(recent_profiles) == 2

    async def test_profile_persistence(self, simple_profile_id):
        """Test that profiles persist across tool calls."""
        # Profile should be accessible
        hotspots = await get_cpu_hotspots(simple_profile_id)
        assert isinstance(hotspots, list)

        # Should still be accessible
        leaks = await get_memory_leaks(simple_profile_id)
        assert isinstance(leaks, list)


class TestToolIntegration:
    """Integration tests for tool interactions."""

    async def test_profile_analyze_workflow(self, simple_cpu_profile_json):
        """Test complete profile → analyze workflow."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        # Profile
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            profile_result = await profile_script(str(simple_cpu_profile_json))
            profile_id = profile_result["profile_id"]

        # Analyze
        analysis = await analyze_profile(profile_id)
        assert "hotspots" in analysis

        # Get recommendations
        recommendations = await get_recommendations(profile_id)
        assert isinstance(recommendations, list)

    async def test_compare_workflow(
        self, simple_cpu_profile_json, memory_leak_profile_json
    ):
        """Test complete profile → compare workflow."""
        parser = ProfileParser()
        profile1 = parser.parse_file(simple_cpu_profile_json)
        profile2 = parser.parse_file(memory_leak_profile_json)
        
        # Profile both
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile1
            before = await profile_script(str(simple_cpu_profile_json))
            mock_profile.return_value = profile2
            after = await profile_script(str(memory_leak_profile_json))

        # Compare
        comparison = await compare_profiles(before["profile_id"], after["profile_id"])
        assert "improvements" in comparison
        assert "regressions" in comparison

    async def test_profile_query_all_tools(self, simple_cpu_profile_json):
        """Test querying profile with all tools."""
        parser = ProfileParser()
        profile = parser.parse_file(simple_cpu_profile_json)
        
        # Profile
        with patch("scalene_mcp.profiler.ScaleneProfiler.profile_script", new_callable=AsyncMock) as mock_profile:
            mock_profile.return_value = profile
            profile_result = await profile_script(str(simple_cpu_profile_json))
            profile_id = profile_result["profile_id"]

        # Query with all tools
        await get_cpu_hotspots(profile_id)
        await get_memory_hotspots(profile_id)
        await get_gpu_hotspots(profile_id)
        await get_bottlenecks(profile_id)
        await get_memory_leaks(profile_id)
        await get_recommendations(profile_id)
        await get_function_summary(profile_id)

        # All should succeed without errors
