"""Scalene JSON output parser."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from scalene_mcp.models import (
    FileMetrics,
    FunctionMetrics,
    LineMetrics,
    MemoryLeak,
    ProfileResult,
    ProfileSummary,
)


class ProfileParser:
    """Parse Scalene JSON output into our Pydantic models."""

    def parse_json(self, json_str: str, profile_id: str | None = None) -> ProfileResult:
        """
        Parse Scalene JSON output from a string.

        Handles mixed output where the profiled script may have written to stdout.
        Scalene outputs JSON at the end, so we extract the last valid JSON object.

        Args:
            json_str: JSON string from Scalene output (may contain script stdout)
            profile_id: Optional profile ID (generated if not provided)

        Returns:
            Parsed ProfileResult with all metrics

        Raises:
            json.JSONDecodeError: If the JSON is invalid
            KeyError: If required fields are missing
            ValueError: If no valid JSON object found
        """
        json_str = json_str.strip()
        
        # Scalene outputs JSON at the end. Extract it from mixed output.
        # Find the last complete JSON object (starts with '{', ends with '}')
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            raise ValueError("No valid JSON object found in output")
        
        json_content = json_str[start_idx:end_idx + 1]
        
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from output: {e}") from e

        # Generate profile ID if not provided
        if profile_id is None:
            profile_id = f"profile_{int(time.time())}"

        return self._parse_data(profile_id, data)

    def parse_file(self, json_path: Path | str) -> ProfileResult:
        """
        Parse a Scalene JSON profile file.

        Args:
            json_path: Path to Scalene JSON output file

        Returns:
            Parsed ProfileResult with all metrics

        Raises:
            FileNotFoundError: If the JSON file doesn't exist
            json.JSONDecodeError: If the JSON is invalid
            KeyError: If required fields are missing
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"Profile file not found: {json_path}")

        with open(json_path) as f:
            json_content = f.read()

        # Generate profile ID from filename and timestamp
        profile_id = f"{json_path.stem}_{int(time.time())}"

        # Use parse_json for consistent parsing, but pass the ID
        result = self.parse_json(json_content, profile_id=profile_id)
        
        # Update with file path info
        result.raw_json_path = str(json_path)
        
        return result

    def _parse_data(self, profile_id: str, data: dict[str, Any]) -> ProfileResult:
        """Common parsing logic for both JSON string and file."""
        # Parse files
        files: dict[str, FileMetrics] = {}
        for filename, file_data in data.get("files", {}).items():
            files[filename] = self._parse_file_metrics(filename, file_data)

        # Create summary
        summary = self._create_summary(profile_id, data, files)

        # Handle scalene_args - Scalene outputs as list, but we expect dict
        scalene_args = data.get("args", {})
        if isinstance(scalene_args, list):
            # Convert list of args to dict format
            scalene_args = {}

        return ProfileResult(
            profile_id=profile_id,
            timestamp=time.time(),
            summary=summary,
            files=files,
            scalene_version=data.get("scalene_version", "unknown"),
            scalene_args=scalene_args,
            raw_json_path=None,  # Will be set by parse_file if applicable
        )

    def _parse_file_metrics(
        self, filename: str, file_data: dict[str, Any]
    ) -> FileMetrics:
        """Parse metrics for a single file."""
        # Parse lines
        lines: list[LineMetrics] = []
        for line_data in file_data.get("lines", []):
            lines.append(self._parse_line_metrics(line_data))

        # Parse functions
        functions: list[FunctionMetrics] = []
        for func_data in file_data.get("functions", []):
            functions.append(self._parse_function_metrics(func_data))

        # Parse memory leaks
        leaks: list[MemoryLeak] = []
        leaks_data = file_data.get("leaks", {})
        for lineno_str, leak_info in leaks_data.items():
            lineno = int(lineno_str)
            # Find the line text
            line_text = ""
            for line_data in file_data.get("lines", []):
                if line_data.get("lineno") == lineno:
                    line_text = line_data.get("line", "")
                    break

            leaks.append(
                MemoryLeak(
                    filename=filename,
                    lineno=lineno,
                    line=line_text,
                    likelihood=leak_info.get("likelihood", 0.0),
                    velocity_mb_s=leak_info.get("velocity_mb_s", 0.0),
                )
            )

        # Calculate total CPU for file
        total_cpu = sum(
            line.total_cpu_percent for line in lines if line.total_cpu_percent > 0
        )

        return FileMetrics(
            filename=filename,
            total_cpu_percent=min(total_cpu, 100.0),  # Cap at 100%
            functions=functions,
            lines=lines,
            imports=file_data.get("imports", []),
            leaks=leaks,
        )

    def _parse_line_metrics(self, line_data: dict[str, Any]) -> LineMetrics:
        """Parse metrics for a single line."""
        return LineMetrics(
            lineno=line_data.get("lineno", 0),
            line=line_data.get("line", ""),
            cpu_percent_python=line_data.get("n_cpu_percent_python", 0.0),
            cpu_percent_c=line_data.get("n_cpu_percent_c", 0.0),
            cpu_percent_system=line_data.get("n_sys_percent", 0.0),
            cpu_samples=line_data.get("cpu_samples_list", []),
            gpu_percent=line_data.get("n_gpu_percent", 0.0),
            memory_peak_mb=line_data.get("n_peak_mb", 0.0),
            memory_average_mb=line_data.get("n_avg_mb", 0.0),
            memory_alloc_mb=line_data.get("n_malloc_mb", 0.0),
            memory_alloc_count=line_data.get("n_mallocs", 0),
            memory_samples=line_data.get("memory_samples", []),
            cpu_utilization=line_data.get("n_usage_fraction", 0.0),
            core_utilization=line_data.get("n_core_utilization", 0.0),
            loop_start=line_data.get("loop_start"),
            loop_end=line_data.get("loop_end"),
        )

    def _parse_function_metrics(self, func_data: dict[str, Any]) -> FunctionMetrics:
        """Parse metrics for a single function."""
        return FunctionMetrics(
            name=func_data.get("name", "unknown"),
            first_lineno=func_data.get("lineno", 0),
            last_lineno=func_data.get("lineno", 0),  # Scalene doesn't provide end
            total_cpu_percent=(
                func_data.get("n_cpu_percent_python", 0.0)
                + func_data.get("n_cpu_percent_c", 0.0)
                + func_data.get("n_sys_percent", 0.0)
            ),
            total_memory_mb=func_data.get("n_peak_mb", 0.0),
            lines=[],  # Lines are parsed separately at file level
        )

    def _create_summary(
        self, profile_id: str, data: dict[str, Any], files: dict[str, FileMetrics]
    ) -> ProfileSummary:
        """Create a high-level summary from parsed data."""
        # Collect all leaks
        all_leaks: list[MemoryLeak] = []
        for file_metrics in files.values():
            all_leaks.extend(file_metrics.leaks)

        # Calculate totals
        total_cpu_samples = 0
        python_time = 0.0
        native_time = 0.0
        system_time = 0.0
        lines_profiled = 0

        for file_metrics in files.values():
            lines_profiled += len(file_metrics.lines)
            for line in file_metrics.lines:
                if line.total_cpu_percent > 0:
                    total_cpu_samples += len(line.cpu_samples)
                python_time += line.cpu_percent_python
                native_time += line.cpu_percent_c
                system_time += line.cpu_percent_system

        # Normalize percentages
        total_time = python_time + native_time + system_time
        if total_time > 0:
            python_time_percent = (python_time / total_time) * 100
            native_time_percent = (native_time / total_time) * 100
            system_time_percent = (system_time / total_time) * 100
        else:
            python_time_percent = native_time_percent = system_time_percent = 0.0

        return ProfileSummary(
            profile_id=profile_id,
            timestamp=time.time(),
            elapsed_time_sec=data.get("elapsed_time_seconds", 0.0),
            max_memory_mb=data.get("max_footprint_mb", 0.0),
            total_allocations_mb=0.0,  # Not directly in summary
            allocation_count=0,  # Would need to sum from lines
            total_cpu_samples=total_cpu_samples,
            python_time_percent=python_time_percent,
            native_time_percent=native_time_percent,
            system_time_percent=system_time_percent,
            gpu_enabled=any(
                line.gpu_percent > 0
                for file_metrics in files.values()
                for line in file_metrics.lines
            ),
            files_profiled=list(files.keys()),
            lines_profiled=lines_profiled,
            detected_leaks=all_leaks,
            has_memory_leaks=len(all_leaks) > 0,
        )

