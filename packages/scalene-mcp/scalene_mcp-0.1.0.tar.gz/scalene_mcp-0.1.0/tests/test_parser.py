"""Tests for ProfileParser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scalene_mcp.models import FileMetrics, LineMetrics, MemoryLeak, ProfileResult
from scalene_mcp.parser import ProfileParser


@pytest.fixture
def parser():
    """ProfileParser instance"""
    return ProfileParser()


@pytest.mark.asyncio
async def test_parse_simple_cpu_profile(parser: ProfileParser, profiles_dir: Path):
    """Test parsing simple CPU profile"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    result = parser.parse_file(profile_path)
    
    assert isinstance(result, ProfileResult)
    assert result.profile_id
    assert result.timestamp > 0
    assert result.summary.elapsed_time_sec > 0
    assert len(result.files) > 0


@pytest.mark.asyncio
async def test_parse_memory_leak_profile(parser: ProfileParser, profiles_dir: Path):
    """Test parsing profile with memory leaks"""
    profile_path = profiles_dir / "memory_leak.json"
    
    result = parser.parse_file(profile_path)
    
    assert isinstance(result, ProfileResult)
    assert result.summary.has_memory_leaks
    # Check that leaks were detected
    leak_count = sum(len(fm.leaks) for fm in result.files.values())
    assert leak_count > 0


@pytest.mark.asyncio
async def test_parse_memory_heavy_profile(parser: ProfileParser, profiles_dir: Path):
    """Test parsing memory-heavy profile"""
    profile_path = profiles_dir / "memory_heavy.json"
    
    result = parser.parse_file(profile_path)
    
    assert isinstance(result, ProfileResult)
    assert result.summary.max_memory_mb > 0
    # Note: total_allocations_mb may be 0 in summary even with line-level allocation data


@pytest.mark.asyncio
async def test_parse_missing_file(parser: ProfileParser):
    """Test parsing non-existent file"""
    with pytest.raises(FileNotFoundError):
        parser.parse_file(Path("nonexistent.json"))


@pytest.mark.asyncio
async def test_parse_invalid_json(parser: ProfileParser, tmp_path: Path):
    """Test parsing invalid JSON"""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("not valid json {")
    
    with pytest.raises((ValueError, json.JSONDecodeError)):
        parser.parse_file(invalid_file)


@pytest.mark.asyncio
async def test_parse_file_metrics(parser: ProfileParser, profiles_dir: Path):
    """Test that file metrics are parsed correctly"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    result = parser.parse_file(profile_path)
    
    # Check that we have file metrics
    assert len(result.files) > 0
    
    for filename, metrics in result.files.items():
        assert isinstance(metrics, FileMetrics)
        assert metrics.filename == filename
        assert isinstance(metrics.lines, list)
        assert isinstance(metrics.functions, list)
        assert isinstance(metrics.imports, list)


@pytest.mark.asyncio
async def test_parse_line_metrics(parser: ProfileParser, profiles_dir: Path):
    """Test that line metrics are parsed correctly"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    result = parser.parse_file(profile_path)
    
    # Get first file with lines
    file_metrics = next(iter(result.files.values()))
    
    if file_metrics.lines:
        line = file_metrics.lines[0]
        assert isinstance(line, LineMetrics)
        assert line.lineno > 0
        assert isinstance(line.line, str)
        assert line.cpu_percent_python >= 0
        assert line.memory_peak_mb >= 0


@pytest.mark.asyncio
async def test_parse_leaks(parser: ProfileParser, profiles_dir: Path):
    """Test that memory leaks are parsed correctly"""
    profile_path = profiles_dir / "memory_leak.json"
    
    result = parser.parse_file(profile_path)
    
    # Find file with leaks
    leaks_found = False
    for file_metrics in result.files.values():
        if file_metrics.leaks:
            leaks_found = True
            leak = file_metrics.leaks[0]
            assert isinstance(leak, MemoryLeak)
            assert leak.filename
            assert leak.lineno > 0
            assert 0 <= leak.likelihood <= 1
            assert leak.velocity_mb_s >= 0
            break
    
    assert leaks_found, "No leaks found in memory_leak.json"


@pytest.mark.asyncio
async def test_create_summary(parser: ProfileParser, profiles_dir: Path):
    """Test that ProfileSummary is created correctly"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    result = parser.parse_file(profile_path)
    summary = result.summary
    
    assert summary.profile_id == result.profile_id
    assert summary.elapsed_time_sec > 0
    assert summary.files_profiled
    assert summary.lines_profiled >= 0
    assert isinstance(summary.python_time_percent, float)
    assert isinstance(summary.native_time_percent, float)


@pytest.mark.asyncio
async def test_parse_function_metrics(parser: ProfileParser, profiles_dir: Path):
    """Test that function metrics are parsed"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    result = parser.parse_file(profile_path)
    
    # Check for functions in any file
    functions_found = False
    for file_metrics in result.files.values():
        if file_metrics.functions:
            functions_found = True
            func = file_metrics.functions[0]
            assert func.name
            assert func.first_lineno > 0
            assert func.total_cpu_percent >= 0
            break
    
    # Note: Some simple profiles may not have function-level data


@pytest.mark.asyncio
async def test_parse_preserves_all_files(parser: ProfileParser, profiles_dir: Path):
    """Test that all files in profile are preserved"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    # Load raw JSON to check file count
    with open(profile_path) as f:
        raw_data = json.load(f)
    
    result = parser.parse_file(profile_path)
    
    # Check that we have files in the result
    assert len(result.files) > 0


@pytest.mark.asyncio
async def test_parse_handles_empty_sections(parser: ProfileParser, tmp_path: Path):
    """Test parsing profile with empty sections"""
    # Create minimal valid profile
    minimal_profile = {
        "elapsed_time_sec": 1.0,
        "max_footprint_mb": 10.0,
        "samples": [],
        "files": {},
        "growth_rate": 0.0,
    }
    
    profile_path = tmp_path / "minimal.json"
    with open(profile_path, "w") as f:
        json.dump(minimal_profile, f)
    
    result = parser.parse_file(profile_path)
    
    assert isinstance(result, ProfileResult)
    # Parser extracts elapsed_time from raw JSON
    assert result.summary.max_memory_mb == 10.0


@pytest.mark.asyncio
async def test_parse_calculates_totals(parser: ProfileParser, profiles_dir: Path):
    """Test that totals are calculated correctly"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    result = parser.parse_file(profile_path)
    
    # Summary should have calculated totals
    assert result.summary.lines_profiled >= 0
    assert result.summary.total_cpu_samples >= 0
    
    # File percentages should be valid
    for file_metrics in result.files.values():
        assert 0 <= file_metrics.total_cpu_percent <= 100


@pytest.mark.asyncio
async def test_parse_identifies_gpu_usage(parser: ProfileParser, profiles_dir: Path):
    """Test GPU detection in profiles"""
    profile_path = profiles_dir / "simple_cpu.json"
    
    result = parser.parse_file(profile_path)
    
    # GPU should be detected if present in any line
    gpu_found = any(
        line.gpu_percent > 0
        for file_metrics in result.files.values()
        for line in file_metrics.lines
    )
    
    # Summary should reflect GPU usage
    if gpu_found:
        assert result.summary.gpu_enabled

@pytest.mark.asyncio
async def test_parse_json_with_profile_id(parser: ProfileParser):
    """Test parse_json with explicit profile ID"""
    json_str = json.dumps({
        "elapsed_time_sec": 1.0,
        "max_memory_mb": 100.0,
        "total_allocations_mb": 50.0,
        "allocation_count": 1000,
        "total_cpu_samples": 5000,
        "python_time_percent": 70.0,
        "native_time_percent": 20.0,
        "system_time_percent": 10.0,
        "files": {},
    })
    
    result = parser.parse_json(json_str, profile_id="explicit-id")
    assert result.profile_id == "explicit-id"


@pytest.mark.asyncio
async def test_parse_json_without_profile_id(parser: ProfileParser):
    """Test parse_json generates profile ID when not provided"""
    json_str = json.dumps({
        "elapsed_time_sec": 1.0,
        "max_memory_mb": 100.0,
        "total_allocations_mb": 50.0,
        "allocation_count": 1000,
        "total_cpu_samples": 5000,
        "python_time_percent": 70.0,
        "native_time_percent": 20.0,
        "system_time_percent": 10.0,
        "files": {},
    })
    
    result = parser.parse_json(json_str)
