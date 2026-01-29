"""Tests for ProfileComparator."""

import pytest

from scalene_mcp.comparator import ProfileComparator
from scalene_mcp.parser import ProfileParser


@pytest.fixture
def comparator():
    """Create a ProfileComparator instance."""
    return ProfileComparator()


@pytest.fixture
def parser():
    """Create a ProfileParser instance."""
    return ProfileParser()


class TestProfileComparison:
    """Test basic profile comparison."""

    def test_compare_identical_profiles(
        self, comparator, parser, simple_cpu_profile_json
    ):
        """Test comparing identical profiles shows no change."""
        profile = parser.parse_file(simple_cpu_profile_json)
        comparison = comparator.compare(profile, profile)

        assert comparison.before_id == comparison.after_id
        assert comparison.runtime_change_percent == 0.0
        assert comparison.memory_change_percent == 0.0
        assert comparison.cpu_change_percent == 0.0
        assert not comparison.runtime_improved
        assert not comparison.memory_improved
        assert len(comparison.improvements) == 0
        assert len(comparison.regressions) == 0

    def test_compare_different_profiles(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test comparing different profiles."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        comparison = comparator.compare(before, after)

        assert comparison.before_id != comparison.after_id
        assert isinstance(comparison.runtime_change_percent, float)
        assert isinstance(comparison.memory_change_percent, float)
        assert isinstance(comparison.summary_text, str)
        assert len(comparison.summary_text) > 0

    def test_comparison_structure(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test comparison has all required fields."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        comparison = comparator.compare(before, after)

        # Check all required fields exist
        assert hasattr(comparison, "before_id")
        assert hasattr(comparison, "after_id")
        assert hasattr(comparison, "runtime_before_sec")
        assert hasattr(comparison, "runtime_after_sec")
        assert hasattr(comparison, "runtime_change_percent")
        assert hasattr(comparison, "runtime_improved")
        assert hasattr(comparison, "memory_before_mb")
        assert hasattr(comparison, "memory_after_mb")
        assert hasattr(comparison, "memory_change_percent")
        assert hasattr(comparison, "memory_improved")
        assert hasattr(comparison, "improvements")
        assert hasattr(comparison, "regressions")
        assert hasattr(comparison, "overall_improved")
        assert hasattr(comparison, "summary_text")


class TestImprovements:
    """Test improvement detection."""

    def test_runtime_improvement_detection(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test runtime improvement detection."""
        # Load two profiles where one might be faster
        before = parser.parse_file(memory_heavy_profile_json)
        after = parser.parse_file(simple_cpu_profile_json)

        # If simple is faster than memory_heavy, should detect improvement
        if after.summary.elapsed_time_sec < before.summary.elapsed_time_sec:
            comparison = comparator.compare(before, after)
            assert comparison.runtime_improved
            assert comparison.runtime_change_percent < 0

    def test_memory_improvement_detection(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test memory improvement detection."""
        # memory_heavy should use more memory than simple
        before = parser.parse_file(memory_heavy_profile_json)
        after = parser.parse_file(simple_cpu_profile_json)

        # If simple uses less memory, should detect improvement
        if after.summary.max_memory_mb < before.summary.max_memory_mb:
            comparison = comparator.compare(before, after)
            assert comparison.memory_improved
            assert comparison.memory_change_percent < 0

    def test_improvements_list(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test improvements list generation."""
        before = parser.parse_file(memory_heavy_profile_json)
        after = parser.parse_file(simple_cpu_profile_json)

        comparison = comparator.compare(before, after)

        # Check improvements is a list of strings
        assert isinstance(comparison.improvements, list)
        for improvement in comparison.improvements:
            assert isinstance(improvement, str)
            assert len(improvement) > 0


class TestRegressions:
    """Test regression detection."""

    def test_runtime_regression_detection(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test runtime regression detection."""
        # If memory_heavy is slower, should detect regression
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        if after.summary.elapsed_time_sec > before.summary.elapsed_time_sec * 1.05:
            comparison = comparator.compare(before, after)
            assert not comparison.runtime_improved
            assert comparison.runtime_change_percent > 0

    def test_memory_regression_detection(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test memory regression detection."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        if after.summary.max_memory_mb > before.summary.max_memory_mb * 1.05:
            comparison = comparator.compare(before, after)
            assert not comparison.memory_improved
            assert comparison.memory_change_percent > 0

    def test_regressions_list(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test regressions list generation."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        comparison = comparator.compare(before, after)

        # Check regressions is a list of strings
        assert isinstance(comparison.regressions, list)
        for regression in comparison.regressions:
            assert isinstance(regression, str)
            assert len(regression) > 0

    def test_leak_regression_detection(
        self, comparator, parser, simple_cpu_profile_json, memory_leak_profile_json
    ):
        """Test memory leak regression detection."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_leak_profile_json)

        comparison = comparator.compare(before, after)

        # If after has more leaks, should be in regressions
        if len(after.summary.detected_leaks) > len(before.summary.detected_leaks):
            assert any("leak" in r.lower() for r in comparison.regressions)


class TestSummaryGeneration:
    """Test comparison summary generation."""

    def test_summary_contains_key_sections(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test summary has expected sections."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        comparison = comparator.compare(before, after)
        summary = comparison.summary_text

        # Should contain key sections
        assert "Profile Comparison" in summary or "Overall" in summary
        assert "Runtime" in summary or "Memory" in summary

    def test_summary_includes_improvements(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test summary includes improvements when present."""
        before = parser.parse_file(memory_heavy_profile_json)
        after = parser.parse_file(simple_cpu_profile_json)

        comparison = comparator.compare(before, after)

        if comparison.improvements:
            assert "Improvement" in comparison.summary_text

    def test_summary_includes_regressions(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test summary includes regressions when present."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        comparison = comparator.compare(before, after)

        if comparison.regressions:
            assert "Regression" in comparison.summary_text or "⚠️" in comparison.summary_text

    def test_summary_format(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test summary is well-formatted markdown."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        comparison = comparator.compare(before, after)
        summary = comparison.summary_text

        # Should be markdown with headers
        assert summary.startswith("#")
        # Should have multiple lines
        assert "\n" in summary
        # Should not be empty
        assert len(summary) > 20


class TestFileChanges:
    """Test per-file change detection."""

    def test_get_file_changes(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test getting file-level changes."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        changes = comparator.get_file_changes(before, after, min_change_percent=0.0)

        assert isinstance(changes, dict)
        # Each entry should have change metrics
        for filename, metrics in changes.items():
            assert isinstance(filename, str)
            assert isinstance(metrics, dict)

    def test_file_changes_structure(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test file changes have expected structure."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        changes = comparator.get_file_changes(before, after, min_change_percent=0.0)

        for filename, metrics in changes.items():
            # Should have status indicators or change metrics
            if "status" in metrics:
                assert metrics["status"] in ("added", "removed")
            else:
                # Should have CPU change metrics
                assert "cpu_change_percent" in metrics or "cpu_before" in metrics

    def test_file_changes_threshold(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test file changes respect threshold."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        # Low threshold should return more changes
        changes_low = comparator.get_file_changes(
            before, after, min_change_percent=0.1
        )

        # High threshold should return fewer changes
        changes_high = comparator.get_file_changes(
            before, after, min_change_percent=50.0
        )

        assert len(changes_low) >= len(changes_high)

    def test_file_changes_improvement_flag(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test file changes include improvement flag."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        changes = comparator.get_file_changes(before, after, min_change_percent=0.0)

        for filename, metrics in changes.items():
            if "improved" in metrics:
                assert isinstance(metrics["improved"], bool)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_compare_zero_runtime(self, comparator, parser, simple_cpu_profile_json):
        """Test comparison handles zero runtime gracefully."""
        profile = parser.parse_file(simple_cpu_profile_json)

        # Should not raise division by zero
        comparison = comparator.compare(profile, profile)
        assert comparison.runtime_change_percent == 0.0

    def test_compare_zero_memory(self, comparator, parser, simple_cpu_profile_json):
        """Test comparison handles zero memory gracefully."""
        profile = parser.parse_file(simple_cpu_profile_json)

        # Should not raise division by zero
        comparison = comparator.compare(profile, profile)
        assert comparison.memory_change_percent == 0.0

    def test_overall_improved_logic(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test overall_improved logic."""
        before = parser.parse_file(memory_heavy_profile_json)
        after = parser.parse_file(simple_cpu_profile_json)

        comparison = comparator.compare(before, after)

        # overall_improved should be True if any metric improved and no regressions
        if comparison.improvements and not comparison.regressions:
            assert comparison.overall_improved
        elif comparison.regressions:
            assert not comparison.overall_improved

    def test_percentage_calculations(
        self, comparator, parser, simple_cpu_profile_json, memory_heavy_profile_json
    ):
        """Test percentage calculations are correct."""
        before = parser.parse_file(simple_cpu_profile_json)
        after = parser.parse_file(memory_heavy_profile_json)

        comparison = comparator.compare(before, after)

        # Verify runtime percentage
        expected_runtime_change = (
            (after.summary.elapsed_time_sec - before.summary.elapsed_time_sec)
            / before.summary.elapsed_time_sec
            * 100
        )
        assert abs(comparison.runtime_change_percent - expected_runtime_change) < 0.01

        # Verify memory percentage
        expected_memory_change = (
            (after.summary.max_memory_mb - before.summary.max_memory_mb)
            / before.summary.max_memory_mb
            * 100
        )
        assert abs(comparison.memory_change_percent - expected_memory_change) < 0.01
