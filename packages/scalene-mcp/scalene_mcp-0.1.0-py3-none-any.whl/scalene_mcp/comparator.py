"""Profile comparison and regression detection."""

from typing import Any

from .models import ProfileComparison, ProfileResult


class ProfileComparator:
    """Compare two profile results to identify improvements and regressions."""

    def compare(
        self,
        before: ProfileResult,
        after: ProfileResult,
    ) -> ProfileComparison:
        """
        Compare two profiles to identify performance changes.

        Args:
            before: Profile from before optimization
            after: Profile from after optimization

        Returns:
            ProfileComparison with detailed change analysis
        """
        # Runtime comparison
        runtime_before = before.summary.elapsed_time_sec
        runtime_after = after.summary.elapsed_time_sec
        runtime_change_percent = (
            ((runtime_after - runtime_before) / runtime_before * 100)
            if runtime_before > 0
            else 0.0
        )
        runtime_improved = runtime_change_percent < 0

        # Memory comparison
        memory_before = before.summary.max_memory_mb
        memory_after = after.summary.max_memory_mb
        memory_change_percent = (
            ((memory_after - memory_before) / memory_before * 100)
            if memory_before > 0
            else 0.0
        )
        memory_improved = memory_change_percent < 0

        # CPU comparison
        cpu_before = before.summary.total_cpu_samples
        cpu_after = after.summary.total_cpu_samples
        cpu_change_percent = (
            ((cpu_after - cpu_before) / cpu_before * 100)
            if cpu_before > 0
            else 0.0
        )
        cpu_improved = cpu_change_percent < 0

        # Collect improvements and regressions
        improvements = self._identify_improvements(before, after)
        regressions = self._identify_regressions(before, after)

        # Generate summary
        summary = self._generate_comparison_summary(
            runtime_improved,
            memory_improved,
            cpu_improved,
            runtime_change_percent,
            memory_change_percent,
            improvements,
            regressions,
        )

        return ProfileComparison(
            before_id=before.profile_id or "unknown",
            after_id=after.profile_id or "unknown",
            runtime_before_sec=runtime_before,
            runtime_after_sec=runtime_after,
            runtime_change_percent=runtime_change_percent,
            runtime_improved=runtime_improved,
            memory_before_mb=memory_before,
            memory_after_mb=memory_after,
            memory_change_percent=memory_change_percent,
            memory_improved=memory_improved,
            cpu_before_samples=cpu_before,
            cpu_after_samples=cpu_after,
            cpu_change_percent=cpu_change_percent,
            cpu_improved=cpu_improved,
            improvements=improvements,
            regressions=regressions,
            overall_improved=(
                runtime_improved or memory_improved or cpu_improved
            )
            and len(regressions) == 0,
            summary_text=summary,
        )

    def _identify_improvements(
        self, before: ProfileResult, after: ProfileResult
    ) -> list[str]:
        """
        Identify specific improvements between profiles.

        Args:
            before: Profile from before optimization
            after: Profile from after optimization

        Returns:
            List of improvement descriptions
        """
        improvements = []

        # Runtime improvements
        runtime_change = (
            (after.summary.elapsed_time_sec - before.summary.elapsed_time_sec)
            / before.summary.elapsed_time_sec
            * 100
            if before.summary.elapsed_time_sec > 0
            else 0
        )
        if runtime_change < -5:  # At least 5% improvement
            improvements.append(
                f"Runtime improved by {abs(runtime_change):.1f}% "
                f"({before.summary.elapsed_time_sec:.2f}s → "
                f"{after.summary.elapsed_time_sec:.2f}s)"
            )

        # Memory improvements
        memory_change = (
            (after.summary.max_memory_mb - before.summary.max_memory_mb)
            / before.summary.max_memory_mb
            * 100
            if before.summary.max_memory_mb > 0
            else 0
        )
        if memory_change < -5:  # At least 5% improvement
            improvements.append(
                f"Peak memory reduced by {abs(memory_change):.1f}% "
                f"({before.summary.max_memory_mb:.1f}MB → "
                f"{after.summary.max_memory_mb:.1f}MB)"
            )

        # Leak improvements
        leaks_before = len(before.summary.detected_leaks)
        leaks_after = len(after.summary.detected_leaks)
        if leaks_after < leaks_before:
            improvements.append(
                f"Memory leaks reduced from {leaks_before} to {leaks_after}"
            )

        # Allocation improvements
        alloc_change = (
            (
                after.summary.total_allocations_mb
                - before.summary.total_allocations_mb
            )
            / before.summary.total_allocations_mb
            * 100
            if before.summary.total_allocations_mb > 0
            else 0
        )
        if alloc_change < -10:  # At least 10% improvement
            improvements.append(
                f"Total allocations reduced by {abs(alloc_change):.1f}%"
            )

        return improvements

    def _identify_regressions(
        self, before: ProfileResult, after: ProfileResult
    ) -> list[str]:
        """
        Identify performance regressions between profiles.

        Args:
            before: Profile from before optimization
            after: Profile from after optimization

        Returns:
            List of regression descriptions
        """
        regressions = []

        # Runtime regressions
        runtime_change = (
            (after.summary.elapsed_time_sec - before.summary.elapsed_time_sec)
            / before.summary.elapsed_time_sec
            * 100
            if before.summary.elapsed_time_sec > 0
            else 0
        )
        if runtime_change > 5:  # At least 5% regression
            regressions.append(
                f"⚠️ Runtime increased by {runtime_change:.1f}% "
                f"({before.summary.elapsed_time_sec:.2f}s → "
                f"{after.summary.elapsed_time_sec:.2f}s)"
            )

        # Memory regressions
        memory_change = (
            (after.summary.max_memory_mb - before.summary.max_memory_mb)
            / before.summary.max_memory_mb
            * 100
            if before.summary.max_memory_mb > 0
            else 0
        )
        if memory_change > 5:  # At least 5% regression
            regressions.append(
                f"⚠️ Peak memory increased by {memory_change:.1f}% "
                f"({before.summary.max_memory_mb:.1f}MB → "
                f"{after.summary.max_memory_mb:.1f}MB)"
            )

        # Leak regressions
        leaks_before = len(before.summary.detected_leaks)
        leaks_after = len(after.summary.detected_leaks)
        if leaks_after > leaks_before:
            regressions.append(
                f"⚠️ Memory leaks increased from {leaks_before} to {leaks_after}"
            )

        return regressions

    def _generate_comparison_summary(
        self,
        runtime_improved: bool,
        memory_improved: bool,
        cpu_improved: bool,
        runtime_change: float,
        memory_change: float,
        improvements: list[str],
        regressions: list[str],
    ) -> str:
        """
        Generate human-readable comparison summary.

        Args:
            runtime_improved: Whether runtime improved
            memory_improved: Whether memory improved
            cpu_improved: Whether CPU usage improved
            runtime_change: Runtime change percentage
            memory_change: Memory change percentage
            improvements: List of improvements
            regressions: List of regressions

        Returns:
            Formatted markdown summary
        """
        summary_parts = ["# Profile Comparison\n"]

        # Overall assessment
        if improvements and not regressions:
            summary_parts.append("✅ **Overall: Improved**\n\n")
        elif regressions and not improvements:
            summary_parts.append("⚠️ **Overall: Regressed**\n\n")
        elif improvements and regressions:
            summary_parts.append("⚡ **Overall: Mixed Results**\n\n")
        else:
            summary_parts.append("➡️ **Overall: No Significant Change**\n\n")

        # Key metrics
        summary_parts.append("## Key Metrics\n\n")

        runtime_emoji = "✅" if runtime_improved else "⚠️" if runtime_change > 5 else "➡️"
        summary_parts.append(
            f"{runtime_emoji} **Runtime**: {runtime_change:+.1f}%\n"
        )

        memory_emoji = "✅" if memory_improved else "⚠️" if memory_change > 5 else "➡️"
        summary_parts.append(
            f"{memory_emoji} **Memory**: {memory_change:+.1f}%\n\n"
        )

        # Improvements
        if improvements:
            summary_parts.append("## Improvements\n\n")
            for improvement in improvements:
                summary_parts.append(f"- {improvement}\n")
            summary_parts.append("\n")

        # Regressions
        if regressions:
            summary_parts.append("## Regressions\n\n")
            for regression in regressions:
                summary_parts.append(f"- {regression}\n")
            summary_parts.append("\n")

        # Recommendations
        if regressions:
            summary_parts.append("## Recommendations\n\n")
            summary_parts.append(
                "- Review changes that may have introduced regressions\n"
            )
            if any("Runtime" in r for r in regressions):
                summary_parts.append(
                    "- Profile CPU hotspots to identify performance bottlenecks\n"
                )
            if any("memory" in r.lower() for r in regressions):
                summary_parts.append(
                    "- Check for increased allocations or memory leaks\n"
                )

        return "".join(summary_parts)

    def get_file_changes(
        self, before: ProfileResult, after: ProfileResult, min_change_percent: float = 5.0
    ) -> dict[str, dict[str, Any]]:
        """
        Get per-file performance changes.

        Args:
            before: Profile from before optimization
            after: Profile from after optimization
            min_change_percent: Minimum change percentage to report

        Returns:
            Dictionary mapping filenames to their change metrics
        """
        changes: dict[str, dict[str, Any]] = {}

        # Get all files from both profiles
        all_files = set(before.files.keys()) | set(after.files.keys())

        for filename in all_files:
            before_metrics = before.files.get(filename)
            after_metrics = after.files.get(filename)

            if before_metrics and after_metrics:
                # File exists in both profiles
                cpu_change = (
                    (
                        after_metrics.total_cpu_percent
                        - before_metrics.total_cpu_percent
                    )
                    / before_metrics.total_cpu_percent
                    * 100
                    if before_metrics.total_cpu_percent > 0
                    else 0.0
                )

                if abs(cpu_change) >= min_change_percent:
                    changes[filename] = {
                        "cpu_before": before_metrics.total_cpu_percent,
                        "cpu_after": after_metrics.total_cpu_percent,
                        "cpu_change_percent": cpu_change,
                        "improved": cpu_change < 0,
                    }
            elif before_metrics and not after_metrics:
                # File removed (likely optimization)
                changes[filename] = {
                    "status": "removed",
                    "cpu_before": before_metrics.total_cpu_percent,
                }
            elif after_metrics and not before_metrics:
                # File added (potential regression)
                changes[filename] = {
                    "status": "added",
                    "cpu_after": after_metrics.total_cpu_percent,
                }

        return changes
