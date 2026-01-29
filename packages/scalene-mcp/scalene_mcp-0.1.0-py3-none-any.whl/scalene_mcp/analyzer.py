"""Profile analysis and insight extraction for Scalene profiling results."""

from typing import Any

from .models import (
    Hotspot,
    LineMetrics,
    ProfileAnalysis,
    ProfileResult,
)


class ProfileAnalyzer:
    """Analyze profiling results and extract actionable insights."""

    def analyze(
        self,
        profile: ProfileResult,
        top_n: int = 10,
        cpu_threshold: float = 5.0,
        memory_threshold_mb: float = 10.0,
        focus: str = "all",
    ) -> ProfileAnalysis:
        """
        Analyze a profile and generate comprehensive insights.

        Args:
            profile: The profile result to analyze
            top_n: Number of top hotspots to include
            cpu_threshold: Minimum CPU percentage for bottleneck detection
            memory_threshold_mb: Minimum memory MB for bottleneck detection
            focus: Analysis focus - "cpu", "memory", "gpu", or "all"

        Returns:
            Complete profile analysis with hotspots and recommendations
        """
        # Collect hotspots based on focus
        hotspots = []
        if focus in ("all", "cpu"):
            hotspots.extend(self.get_top_cpu_hotspots(profile, top_n))
        if focus in ("all", "memory"):
            hotspots.extend(self.get_top_memory_hotspots(profile, top_n))
        if focus in ("all", "gpu"):
            hotspots.extend(self.get_top_gpu_hotspots(profile, top_n))
        
        # Get leaks
        leaks = []
        for file_metrics in profile.files.values():
            leaks.extend(file_metrics.leaks)
        
        return ProfileAnalysis(
            profile_id=profile.profile_id or "unknown",
            focus=focus,  # type: ignore
            hotspots=hotspots,
            leaks=leaks,
            recommendations=self.generate_recommendations(profile),
            summary_text=self.generate_summary(profile),
        )

    def get_top_cpu_hotspots(
        self, profile: ProfileResult, n: int = 10
    ) -> list[Hotspot]:
        """
        Get top N lines by CPU usage.

        Args:
            profile: The profile result to analyze
            n: Number of top hotspots to return

        Returns:
            List of CPU hotspots sorted by total CPU percentage
        """
        all_lines: list[tuple[float, str, LineMetrics]] = []

        for filename, file_metrics in profile.files.items():
            for line in file_metrics.lines:
                total_cpu = line.total_cpu_percent
                if total_cpu > 0:
                    all_lines.append((total_cpu, filename, line))

        # Sort by CPU percentage descending
        all_lines.sort(key=lambda x: x[0], reverse=True)

        hotspots: list[Hotspot] = []
        for total_cpu, filename, line in all_lines[:n]:
            severity = "high" if total_cpu > 20 else "medium" if total_cpu > 5 else "low"
            hotspots.append(
                Hotspot(
                    type="cpu",
                    severity=severity,
                    filename=filename,
                    lineno=line.lineno,
                    line=line.line,
                    cpu_percent=total_cpu,
                    recommendation=self._get_cpu_recommendation(line),
                )
            )

        return hotspots

    def get_top_memory_hotspots(
        self, profile: ProfileResult, n: int = 10
    ) -> list[Hotspot]:
        """
        Get top N lines by memory allocation.

        Args:
            profile: The profile result to analyze
            n: Number of top hotspots to return

        Returns:
            List of memory hotspots sorted by peak memory usage
        """
        all_lines: list[tuple[float, str, LineMetrics]] = []

        for filename, file_metrics in profile.files.items():
            for line in file_metrics.lines:
                if line.memory_peak_mb > 0:
                    all_lines.append((line.memory_peak_mb, filename, line))

        # Sort by peak memory descending
        all_lines.sort(key=lambda x: x[0], reverse=True)

        hotspots: list[Hotspot] = []
        for peak_mb, filename, line in all_lines[:n]:
            severity = "high" if peak_mb > 100 else "medium" if peak_mb > 10 else "low"
            hotspots.append(
                Hotspot(
                    type="memory",
                    severity=severity,
                    filename=filename,
                    lineno=line.lineno,
                    line=line.line,
                    memory_mb=peak_mb,
                    recommendation=self._get_memory_recommendation(line),
                )
            )

        return hotspots

    def get_top_gpu_hotspots(
        self, profile: ProfileResult, n: int = 10
    ) -> list[Hotspot]:
        """
        Get top N lines by GPU usage.

        Args:
            profile: The profile result to analyze
            n: Number of top hotspots to return

        Returns:
            List of GPU hotspots sorted by GPU percentage
        """
        all_lines: list[tuple[float, str, LineMetrics]] = []

        for filename, file_metrics in profile.files.items():
            for line in file_metrics.lines:
                if line.gpu_percent > 0:
                    all_lines.append((line.gpu_percent, filename, line))

        # Sort by GPU percentage descending
        all_lines.sort(key=lambda x: x[0], reverse=True)

        hotspots: list[Hotspot] = []
        for gpu_percent, filename, line in all_lines[:n]:
            severity = "high" if gpu_percent > 50 else "medium" if gpu_percent > 10 else "low"
            hotspots.append(
                Hotspot(
                    type="gpu",
                    severity=severity,
                    filename=filename,
                    lineno=line.lineno,
                    line=line.line,
                    gpu_percent=gpu_percent,
                    recommendation=self._get_gpu_recommendation(line),
                )
            )

        return hotspots

    def identify_bottlenecks(
        self,
        profile: ProfileResult,
        cpu_threshold: float = 5.0,
        memory_threshold_mb: float = 10.0,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Identify performance bottlenecks.

        Args:
            profile: The profile result to analyze
            cpu_threshold: Minimum CPU percentage to consider as bottleneck
            memory_threshold_mb: Minimum memory MB to consider as bottleneck

        Returns:
            Dictionary with 'cpu', 'memory', and 'gpu' bottleneck lists
        """
        bottlenecks: dict[str, list[dict[str, Any]]] = {
            "cpu": [],
            "memory": [],
            "gpu": [],
        }

        for filename, file_metrics in profile.files.items():
            for line in file_metrics.lines:
                # CPU bottlenecks
                total_cpu = line.total_cpu_percent
                if total_cpu >= cpu_threshold:
                    severity = "high" if total_cpu > 20 else "medium"
                    bottlenecks["cpu"].append(
                        {
                            "type": "cpu",
                            "severity": severity,
                            "file": filename,
                            "line": line.lineno,
                            "code": line.line,
                            "cpu_percent": total_cpu,
                            "python_percent": line.cpu_percent_python,
                            "native_percent": line.cpu_percent_c,
                            "recommendation": self._get_cpu_recommendation(line),
                        }
                    )

                # Memory bottlenecks
                if line.memory_peak_mb >= memory_threshold_mb:
                    severity = "high" if line.memory_peak_mb > 100 else "medium"
                    bottlenecks["memory"].append(
                        {
                            "type": "memory",
                            "severity": severity,
                            "file": filename,
                            "line": line.lineno,
                            "code": line.line,
                            "peak_mb": line.memory_peak_mb,
                            "average_mb": line.memory_average_mb,
                            "alloc_mb": line.memory_alloc_mb,
                            "recommendation": self._get_memory_recommendation(line),
                        }
                    )

                # GPU bottlenecks
                if line.gpu_percent > 0:
                    severity = "high" if line.gpu_percent > 50 else "medium"
                    bottlenecks["gpu"].append(
                        {
                            "type": "gpu",
                            "severity": severity,
                            "file": filename,
                            "line": line.lineno,
                            "code": line.line,
                            "gpu_percent": line.gpu_percent,
                            "gpu_memory_mb": line.gpu_memory_mb,
                            "recommendation": self._get_gpu_recommendation(line),
                        }
                    )

        return bottlenecks

    def _get_cpu_recommendation(self, line: LineMetrics) -> str:
        """Generate CPU optimization recommendation for a line."""
        recommendations = []

        if line.cpu_percent_c > line.cpu_percent_python:
            recommendations.append(
                "Native code dominates - check C extension performance"
            )
        elif line.cpu_percent_python > 10:
            recommendations.append("Consider vectorization or caching")

        if line.cpu_percent_system > 5:
            recommendations.append("High system time - check I/O operations")

        return " | ".join(recommendations) if recommendations else "Optimize algorithm"

    def _get_memory_recommendation(self, line: LineMetrics) -> str:
        """Generate memory optimization recommendation for a line."""
        recommendations = []

        if line.memory_alloc_count > 1000:
            recommendations.append("High allocation count - consider object pooling")
        elif line.memory_peak_mb > 100:
            recommendations.append("Large allocation - consider chunking or streaming")

        if line.memory_average_mb < line.memory_peak_mb * 0.3:
            recommendations.append("Memory spikes - check for temporary objects")

        return (
            " | ".join(recommendations)
            if recommendations
            else "Reduce memory usage"
        )

    def _get_gpu_recommendation(self, line: LineMetrics) -> str:
        """Generate GPU optimization recommendation for a line."""
        recommendations = []

        if line.gpu_percent > 50:
            recommendations.append("GPU intensive - consider batching")

        if line.gpu_memory_mb > 1000:
            recommendations.append("High GPU memory - optimize tensor sizes")

        return (
            " | ".join(recommendations) if recommendations else "Optimize GPU usage"
        )

    def generate_recommendations(self, profile: ProfileResult) -> list[str]:
        """
        Generate high-level recommendations based on profile analysis.

        Args:
            profile: The profile result to analyze

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        # Check overall memory usage
        if profile.summary.max_memory_mb > 1000:
            recommendations.append(
                f"High memory usage ({profile.summary.max_memory_mb:.1f} MB) - "
                "consider memory profiling and optimization"
            )

        # Check for memory leaks
        if profile.summary.detected_leaks:
            leak_count = len(profile.summary.detected_leaks)
            recommendations.append(
                f"⚠️ {leak_count} potential memory leak(s) detected - "
                "investigate growing allocations"
            )

        # Check CPU distribution
        cpu_hotspots = self.get_top_cpu_hotspots(profile, 3)
        if cpu_hotspots and cpu_hotspots[0].cpu_percent > 30:
            recommendations.append(
                f"Single hotspot dominates CPU ({cpu_hotspots[0].cpu_percent:.1f}%) - "
                f"focus optimization on {cpu_hotspots[0].filename}:{cpu_hotspots[0].lineno}"
            )

        # Check GPU usage
        has_gpu = any(
            any(line.gpu_percent > 0 for line in fm.lines)
            for fm in profile.files.values()
        )
        if has_gpu:
            recommendations.append(
                "GPU usage detected - ensure efficient GPU utilization"
            )

        # Check file count
        if len(profile.files) > 50:
            recommendations.append(
                f"Large codebase ({len(profile.files)} files) - "
                "consider focused profiling with --profile-only"
            )

        return recommendations

    def generate_summary(self, profile: ProfileResult) -> str:
        """
        Generate human-readable summary for LLM consumption.

        Args:
            profile: The profile result to summarize

        Returns:
            Formatted markdown summary
        """
        summary_parts = ["# Profile Summary\n"]

        # Overview
        summary_parts.append(
            f"**Runtime**: {profile.summary.elapsed_time_sec:.2f} seconds\n"
        )
        summary_parts.append(
            f"**Peak Memory**: {profile.summary.max_memory_mb:.2f} MB\n"
        )
        summary_parts.append(f"**Files Profiled**: {len(profile.files)}\n")

        # CPU Hotspots
        cpu_hotspots = self.get_top_cpu_hotspots(profile, 5)
        if cpu_hotspots:
            summary_parts.append("\n## Top CPU Hotspots\n")
            for i, hotspot in enumerate(cpu_hotspots, 1):
                summary_parts.append(
                    f"{i}. {hotspot.filename}:{hotspot.lineno} - "
                    f"{hotspot.cpu_percent:.1f}% CPU\n"
                )
                summary_parts.append(f"   `{hotspot.line.strip()}`\n")

        # Memory Hotspots
        memory_hotspots = self.get_top_memory_hotspots(profile, 5)
        if memory_hotspots:
            summary_parts.append("\n## Top Memory Allocations\n")
            for i, hotspot in enumerate(memory_hotspots, 1):
                summary_parts.append(
                    f"{i}. {hotspot.filename}:{hotspot.lineno} - "
                    f"{hotspot.memory_mb:.1f} MB\n"
                )
                summary_parts.append(f"   `{hotspot.line.strip()}`\n")

        # GPU Hotspots
        gpu_hotspots = self.get_top_gpu_hotspots(profile, 5)
        if gpu_hotspots:
            summary_parts.append("\n## Top GPU Usage\n")
            for i, hotspot in enumerate(gpu_hotspots, 1):
                summary_parts.append(
                    f"{i}. {hotspot.filename}:{hotspot.lineno} - "
                    f"{hotspot.gpu_percent:.1f}% GPU\n"
                )
                summary_parts.append(f"   `{hotspot.line.strip()}`\n")

        # Memory Leaks
        if profile.summary.detected_leaks:
            summary_parts.append("\n## ⚠️ Memory Leaks Detected\n")
            for leak in profile.summary.detected_leaks:
                summary_parts.append(
                    f"- {leak.filename}:{leak.lineno} "
                    f"(likelihood: {leak.likelihood:.0%}, "
                    f"rate: {leak.velocity_mb_s:.2f} MB/s)\n"
                )

        # Recommendations
        recommendations = self.generate_recommendations(profile)
        if recommendations:
            summary_parts.append("\n## Recommendations\n")
            for rec in recommendations:
                summary_parts.append(f"- {rec}\n")

        return "".join(summary_parts)

    def get_function_summary(
        self, profile: ProfileResult, top_n: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get summary of top functions by resource usage.

        Args:
            profile: The profile result to analyze
            top_n: Number of top functions to return

        Returns:
            List of function summaries sorted by total CPU percentage
        """
        all_functions: list[tuple[float, str, FileMetrics]] = []

        for filename, file_metrics in profile.files.items():
            if file_metrics.total_cpu_percent > 0:
                all_functions.append(
                    (file_metrics.total_cpu_percent, filename, file_metrics)
                )

        # Sort by CPU percentage descending
        all_functions.sort(key=lambda x: x[0], reverse=True)

        function_summaries: list[dict[str, Any]] = []
        for total_cpu, filename, file_metrics in all_functions[:top_n]:
            # Calculate total memory from lines
            total_memory = sum(
                line.memory_peak_mb for line in file_metrics.lines
            )
            # Calculate total GPU from lines
            max_gpu = max(
                (line.gpu_percent for line in file_metrics.lines),
                default=0.0,
            )
            function_summaries.append(
                {
                    "file": filename,
                    "cpu_percent": total_cpu,
                    "memory_peak_mb": total_memory,
                    "gpu_percent": max_gpu,
                    "line_count": len(file_metrics.lines),
                }
            )

        return function_summaries
