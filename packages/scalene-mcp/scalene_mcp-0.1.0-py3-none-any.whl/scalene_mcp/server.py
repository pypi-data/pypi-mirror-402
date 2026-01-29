"""Scalene MCP Server.

Main FastMCP server with tools, resources, and prompts for Scalene profiling.
"""

import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from scalene_mcp.logging import get_logger

from .analyzer import ProfileAnalyzer
from .comparator import ProfileComparator
from .models import ProfileResult
from .parser import ProfileParser
from .profiler import ScaleneProfiler

# Create the MCP server
server = FastMCP("Scalene Profiler")

# Initialize components
profiler = ScaleneProfiler()
parser = ProfileParser()
analyzer = ProfileAnalyzer()
comparator = ProfileComparator()

# Store recent profiles (in-memory for now)
recent_profiles: dict[str, ProfileResult] = {}

# Project context (auto-detected or explicitly set)
_project_root: Path | None = None

logger = get_logger(__name__)


def _detect_project_root(start_path: Path | None = None) -> Path:
    """Auto-detect project root by looking for common markers.
    
    Checks for: .git, pyproject.toml, setup.py, package.json, Makefile
    Falls back to current working directory if no markers found.
    """
    search_path = start_path or Path.cwd()
    if search_path.is_file():
        search_path = search_path.parent
    
    markers = {".git", "pyproject.toml", "setup.py", "package.json", "Makefile", "GNUmakefile"}
    
    # Search up directory tree
    for current in [search_path, *search_path.parents]:
        if any((current / marker).exists() for marker in markers):
            return current
    
    # Fallback to cwd
    return Path.cwd()


def _get_project_root() -> Path:
    """Get the current project root (auto-detected or explicitly set)."""
    global _project_root
    if _project_root is None:
        _project_root = _detect_project_root()
    return _project_root


def _resolve_path(relative_or_absolute: str) -> Path:
    """Resolve a path, making it absolute relative to project root if needed."""
    path = Path(relative_or_absolute)
    if path.is_absolute():
        return path
    return _get_project_root() / path


# ============================================================================
# Discovery Tools - Help LLM understand the project context
# ============================================================================


async def get_project_root() -> dict[str, str]:
    """Get the detected project root and structure type.
    
    Returns: {root, type, markers_found}
    """
    root = _get_project_root()
    
    # Detect project type
    project_type = "unknown"
    markers_found = []
    
    if (root / "pyproject.toml").exists():
        project_type = "python"
        markers_found.append("pyproject.toml")
    if (root / "setup.py").exists():
        project_type = "python"
        markers_found.append("setup.py")
    if (root / "package.json").exists():
        project_type = "node" if project_type == "unknown" else "mixed"
        markers_found.append("package.json")
    if (root / ".git").exists():
        markers_found.append(".git")
    if (root / "Makefile").exists():
        markers_found.append("Makefile")
    if (root / "GNUmakefile").exists():
        markers_found.append("GNUmakefile")
    
    return {
        "root": str(root.absolute()),
        "type": project_type,
        "markers_found": ", ".join(markers_found) if markers_found else "none",
    }


server.tool(get_project_root)


async def list_project_files(
    pattern: str = "*.py",
    max_depth: int = 3,
    exclude_patterns: str = ".git,__pycache__,node_modules,.venv,venv",
) -> list[str]:
    """List project files matching pattern, relative to project root.
    
    Args:
        pattern: Glob pattern (*.py, src/**, etc.)
        max_depth: Maximum directory depth to search
        exclude_patterns: Comma-separated patterns to exclude
        
    Returns: [relative_path, ...] sorted alphabetically
    """
    root = _get_project_root()
    exclude = {s.strip() for s in exclude_patterns.split(",") if s.strip()}
    
    def should_exclude(p: Path) -> bool:
        """Check if path should be excluded."""
        return any(part in exclude for part in p.parts)
    
    results = []
    
    # Handle different pattern types
    if "**" in pattern:
        # Recursive glob
        glob_pattern = pattern
    else:
        # Non-recursive, search at all depths
        glob_pattern = f"**/{pattern}"
    
    for file_path in sorted(root.glob(glob_pattern)):
        if file_path.is_file() and not should_exclude(file_path):
            try:
                rel_path = file_path.relative_to(root)
                depth = len(rel_path.parts)
                if depth <= max_depth:
                    results.append(str(rel_path))
            except ValueError:
                pass
    
    return sorted(results)


server.tool(list_project_files)


async def set_project_context(project_root: str) -> dict[str, str]:
    """Explicitly set the project root (overrides auto-detection).
    
    Use this if auto-detection fails or gives wrong path.
    
    Args:
        project_root: Absolute path to project root
        
    Returns: {project_root, status}
    """
    global _project_root
    path = Path(project_root)
    if not path.exists():
        raise ValueError(f"Path does not exist: {project_root}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {project_root}")
    
    _project_root = path
    return {
        "project_root": str(path.absolute()),
        "status": "set",
    }


server.tool(set_project_context)


# ============================================================================
# Profiling Tool
# ============================================================================


async def profile(
    type: str,
    script_path: str | None = None,
    code: str | None = None,
    cpu_only: bool = False,
    include_memory: bool = True,
    include_gpu: bool = False,
    reduced_profile: bool = False,
    profile_only: str = "",
    profile_exclude: str = "",
    use_virtual_time: bool = False,
    cpu_percent_threshold: float = 1.0,
    malloc_threshold: int = 100,
    script_args: list[str] | None = None,
) -> dict[str, Any]:
    """Profile Python code using Scalene.
    
    Args:
        type: "script" (profile a file) or "code" (profile code snippet)
        script_path: Required if type="script". Path to Python script
        code: Required if type="code". Python code to execute
        cpu_only: Skip memory/GPU profiling
        include_memory: Profile memory allocations
        include_gpu: Profile GPU usage (requires NVIDIA GPU)
        reduced_profile: Show only lines >1% CPU or >100 allocations
        profile_only: Comma-separated paths to include (e.g., "myapp")
        profile_exclude: Comma-separated paths to exclude (e.g., "test,vendor")
        use_virtual_time: Measure CPU time excluding I/O wait
        cpu_percent_threshold: Minimum CPU % to report
        malloc_threshold: Minimum allocation bytes to report
        script_args: Command-line arguments for the script
        
    Returns: {profile_id, summary, text_summary}
    """
    if type == "script":
        if not script_path:
            raise ValueError("script_path required when type='script'")
        path = _resolve_path(script_path)
        if not path.exists():
            raise FileNotFoundError(f"Script not found: {path}")
        
        profile = await profiler.profile_script(
            path,
            cpu_only=cpu_only,
            memory=include_memory and not cpu_only,
            gpu=include_gpu,
            reduced_profile=reduced_profile,
            profile_only=profile_only,
            profile_exclude=profile_exclude,
            use_virtual_time=use_virtual_time,
            cpu_percent_threshold=cpu_percent_threshold,
            malloc_threshold=malloc_threshold,
            script_args=script_args or [],
        )
    elif type == "code":
        if not code:
            raise ValueError("code required when type='code'")
        profile = await profiler.profile_code(
            code,
            cpu_only=cpu_only,
            memory=include_memory and not cpu_only,
            reduced_profile=reduced_profile,
        )
    else:
        raise ValueError(f"type must be 'script' or 'code', got: {type}")

    # Store profile
    profile_id = profile.profile_id or f"profile_{len(recent_profiles)}"
    recent_profiles[profile_id] = profile

    return {
        "profile_id": profile_id,
        "summary": profile.summary.model_dump(),
        "text_summary": analyzer.generate_summary(profile),
    }


server.tool(profile)



# ============================================================================
# Analysis Tool (Mega Tool)
# ============================================================================


async def analyze(
    profile_id: str,
    metric_type: str = "all",
    top_n: int = 10,
    cpu_threshold: float = 5.0,
    memory_threshold_mb: float = 10.0,
    filename: str | None = None,
) -> dict[str, Any]:
    """Analyze profiling data with flexible analysis types.
    
    Args:
        profile_id: Profile ID from profile()
        metric_type: "all", "cpu", "memory", "gpu", "bottlenecks", "leaks", "file", "functions", "recommendations"
        top_n: Number of items to return (for rankings)
        cpu_threshold: Minimum CPU % to flag bottleneck
        memory_threshold_mb: Minimum MB to flag bottleneck
        filename: Required if metric_type="file", file to analyze
        
    Returns: {metric_type, data, summary} structure varies by metric_type
    """
    if profile_id not in recent_profiles:
        raise ValueError(f"Profile not found: {profile_id}")

    profile = recent_profiles[profile_id]
    
    if metric_type == "all":
        # Comprehensive analysis
        analysis = analyzer.analyze(
            profile,
            top_n=top_n,
            cpu_threshold=cpu_threshold,
            memory_threshold_mb=memory_threshold_mb,
            focus="all",
        )
        return {
            "metric_type": "all",
            "data": analysis.model_dump(),
        }
    
    elif metric_type == "cpu":
        # CPU hotspots
        hotspots = analyzer.get_top_cpu_hotspots(profile, n=top_n)
        return {
            "metric_type": "cpu",
            "data": [h.model_dump() for h in hotspots],
        }
    
    elif metric_type == "memory":
        # Memory hotspots
        hotspots = analyzer.get_top_memory_hotspots(profile, n=top_n)
        return {
            "metric_type": "memory",
            "data": [h.model_dump() for h in hotspots],
        }
    
    elif metric_type == "gpu":
        # GPU hotspots
        hotspots = analyzer.get_top_gpu_hotspots(profile, n=top_n)
        return {
            "metric_type": "gpu",
            "data": [h.model_dump() for h in hotspots],
        }
    
    elif metric_type == "bottlenecks":
        # Lines exceeding thresholds
        bottlenecks = analyzer.identify_bottlenecks(
            profile,
            cpu_threshold=cpu_threshold,
            memory_threshold_mb=memory_threshold_mb,
        )
        return {
            "metric_type": "bottlenecks",
            "data": bottlenecks,
        }
    
    elif metric_type == "leaks":
        # Memory leaks
        leaks = [leak.model_dump() for leak in profile.summary.detected_leaks]
        return {
            "metric_type": "leaks",
            "data": leaks,
        }
    
    elif metric_type == "file":
        # File-level metrics
        if not filename:
            raise ValueError("filename required when metric_type='file'")
        if filename not in profile.files:
            available = list(profile.files.keys())
            raise ValueError(
                f"File not in profile: {filename}. Available: {', '.join(available)}"
            )
        file_metrics = profile.files[filename]
        return {
            "metric_type": "file",
            "filename": filename,
            "data": file_metrics.model_dump(),
        }
    
    elif metric_type == "functions":
        # Function-level metrics
        functions = analyzer.get_function_summary(profile, top_n=top_n)
        return {
            "metric_type": "functions",
            "data": functions,
        }
    
    elif metric_type == "recommendations":
        # Optimization recommendations
        recommendations = analyzer.generate_recommendations(profile)
        return {
            "metric_type": "recommendations",
            "data": recommendations,
        }
    
    else:
        raise ValueError(
            f"Unknown metric_type: {metric_type}. "
            "Must be: all, cpu, memory, gpu, bottlenecks, leaks, file, functions, recommendations"
        )


server.tool(analyze)


async def compare_profiles(
    before_id: str,
    after_id: str,
) -> dict[str, Any]:
    """Compare two profiles to measure optimization impact.
    
    Args:
        before_id: Profile ID from original code
        after_id: Profile ID from optimized code
        
    Returns: {runtime_change_pct, memory_change_pct, improvements, regressions, summary_text}
    """
    if before_id not in recent_profiles:
        raise ValueError(f"Profile not found: {before_id}")
    if after_id not in recent_profiles:
        raise ValueError(f"Profile not found: {after_id}")

    before = recent_profiles[before_id]
    after = recent_profiles[after_id]

    comparison = comparator.compare(before, after)
    return comparison.model_dump()


server.tool(compare_profiles)


async def list_profiles() -> list[str]:
    """List all captured profiles in this session.
    
    Returns: [profile_id, ...]
    """
    return list(recent_profiles.keys())


server.tool(list_profiles)


# ============================================================================
# BACKWARD COMPATIBILITY WRAPPERS (for existing tests)
# ============================================================================
# These wrappers maintain backward compatibility with tests written for the
# old 16-tool API. They delegate to the new consolidated 7-tool API.
# These are NOT registered as MCP tools - they're only for internal use.

async def profile_script(
    script_path: str,
    cpu_only: bool = False,
    include_memory: bool = True,
    include_gpu: bool = False,
    reduced_profile: bool = False,
    profile_only: str = "",
    profile_exclude: str = "",
    use_virtual_time: bool = False,
    cpu_percent_threshold: float = 1.0,
    malloc_threshold: int = 100,
    script_args: list[str] | None = None,
    **kwargs: dict[str, Any],
) -> dict[str, Any]:
    """DEPRECATED: Use profile(type='script', ...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    return await profile(
        type="script",
        script_path=script_path,
        cpu_only=cpu_only,
        include_memory=include_memory,
        include_gpu=include_gpu,
        reduced_profile=reduced_profile,
        profile_only=profile_only,
        profile_exclude=profile_exclude,
        use_virtual_time=use_virtual_time,
        cpu_percent_threshold=cpu_percent_threshold,
        malloc_threshold=malloc_threshold,
        script_args=script_args,
    )


async def profile_code(
    code: str,
    cpu_only: bool = False,
    include_memory: bool = True,
    include_gpu: bool = False,
    reduced_profile: bool = False,
    **kwargs: dict[str, Any],
) -> dict[str, Any]:
    """DEPRECATED: Use profile(type='code', ...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    return await profile(
        type="code",
        code=code,
        cpu_only=cpu_only,
        include_memory=include_memory,
        include_gpu=include_gpu,
        reduced_profile=reduced_profile,
    )


async def analyze_profile(
    profile_id: str,
    focus: str = "all",
    cpu_threshold: float = 5.0,
    memory_threshold_mb: float = 10.0,
    **kwargs: dict[str, Any],
) -> dict[str, Any]:
    """DEPRECATED: Use analyze(profile_id, metric_type='all', ...) instead.
    
    This is a backward-compatibility wrapper for tests.
    Maps old 'focus' parameter to new 'metric_type' parameter.
    Flattens response structure to match old API.
    """
    # Map old focus names to new metric_type values
    focus_map = {
        "all": "all",
        "cpu": "cpu",
        "memory": "memory",
        "gpu": "gpu",
        "bottlenecks": "bottlenecks",
        "leaks": "leaks",
        "recommendations": "recommendations",
    }
    metric_type = focus_map.get(focus, "all")
    
    result = await analyze(
        profile_id=profile_id,
        metric_type=metric_type,
        cpu_threshold=cpu_threshold,
        memory_threshold_mb=memory_threshold_mb,
    )
    
    # Old API returned flat structure with focus, hotspots, recommendations, etc.
    # New API returns {metric_type: ..., data: {...}}
    # Flatten the structure for backward compatibility
    if isinstance(result, dict) and "data" in result:
        data = result["data"]
        
        # Handle different data types returned by different metric_types
        if isinstance(data, list):
            # For "cpu", "memory", "gpu" - hotspots come as a list
            flat_result = {
                "focus": focus,
                "hotspots": data,
                "metric_type": metric_type,
            }
        elif isinstance(data, dict):
            # For "all", "bottlenecks", etc. - data is already a dict
            flat_result = data.copy()
            flat_result["focus"] = focus  # Restore old focus parameter
        else:
            flat_result = {"focus": focus, "data": data}
        
        return flat_result
    return result


async def get_cpu_hotspots(
    profile_id: str, top_n: int = 10, **kwargs: dict[str, Any]
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='cpu', top_n=...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(profile_id=profile_id, metric_type="cpu", top_n=top_n)
    # Extract 'hotspots' from nested data structure
    data = result.get("data", {})
    return data.get("hotspots", []) if isinstance(data, dict) else []


async def get_memory_hotspots(
    profile_id: str, top_n: int = 10, **kwargs: dict[str, Any]
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='memory', top_n=...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(profile_id=profile_id, metric_type="memory", top_n=top_n)
    # Extract 'hotspots' from nested data structure
    data = result.get("data", {})
    return data.get("hotspots", []) if isinstance(data, dict) else []


async def get_gpu_hotspots(
    profile_id: str, top_n: int = 10, **kwargs: dict[str, Any]
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='gpu', top_n=...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(profile_id=profile_id, metric_type="gpu", top_n=top_n)
    # Extract 'hotspots' from nested data structure
    data = result.get("data", {})
    return data.get("hotspots", []) if isinstance(data, dict) else []


async def get_bottlenecks(
    profile_id: str,
    cpu_threshold: float = 5.0,
    memory_threshold_mb: float = 10.0,
    **kwargs: dict[str, Any],
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='bottlenecks', ...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(
        profile_id=profile_id,
        metric_type="bottlenecks",
        cpu_threshold=cpu_threshold,
        memory_threshold_mb=memory_threshold_mb,
    )
    # Returns {metric_type, data: {cpu: [...], memory: [...], gpu: [...]}}
    # Return the entire data dict for backward compatibility
    return result.get("data", {})


async def get_memory_leaks(
    profile_id: str, **kwargs: dict[str, Any]
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='leaks') instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(profile_id=profile_id, metric_type="leaks")
    # Extract 'leaks' from nested data structure
    data = result.get("data", {})
    return data.get("leaks", []) if isinstance(data, dict) else []


async def get_file_details(
    profile_id: str, filename: str, **kwargs: dict[str, Any]
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='file', filename=...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(
        profile_id=profile_id, metric_type="file", filename=filename
    )
    # Returns {metric_type, filename, data: {lines: [...], ...}}
    # Return the entire data dict for backward compatibility
    return result.get("data", {})


async def get_function_summary(
    profile_id: str, top_n: int = 10, **kwargs: dict[str, Any]
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='functions', top_n=...) instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(
        profile_id=profile_id, metric_type="functions", top_n=top_n
    )
    # Returns {metric_type, data: [...list of functions...]}
    # Return the entire data list for backward compatibility
    return result.get("data", [])


async def get_recommendations(
    profile_id: str, **kwargs: dict[str, Any]
) -> dict[str, Any] | list[dict[str, Any]]:
    """DEPRECATED: Use analyze(profile_id, metric_type='recommendations') instead.
    
    This is a backward-compatibility wrapper for tests.
    """
    result = await analyze(profile_id=profile_id, metric_type="recommendations")
    # Extract 'recommendations' from nested data structure
    data = result.get("data", {})
    return data.get("recommendations", []) if isinstance(data, dict) else []


def main() -> None:
    """Entry point for running the server."""
    server.run()


if __name__ == "__main__":
    main()
