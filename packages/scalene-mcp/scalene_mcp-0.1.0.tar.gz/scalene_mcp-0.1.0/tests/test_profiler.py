"""Tests for ScaleneProfiler wrapper."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from scalene_mcp.models import ProfileResult
from scalene_mcp.profiler import ScaleneProfiler


@pytest.fixture
def profiler():
    """ScaleneProfiler instance"""
    return ScaleneProfiler()


@pytest.fixture
def fibonacci_path(scripts_dir: Path) -> Path:
    """Path to fibonacci test script"""
    return scripts_dir / "fibonacci.py"


@pytest.fixture
def memory_heavy_path(scripts_dir: Path) -> Path:
    """Path to memory-heavy test script"""
    return scripts_dir / "memory_heavy.py"


@pytest.fixture
def leaky_path(scripts_dir: Path) -> Path:
    """Path to leaky test script"""
    return scripts_dir / "leaky.py"


@pytest.mark.asyncio
async def test_profile_script_success(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test successful profiling of a script"""
    # Disable GPU to avoid PermissionError in test environments
    result = await profiler.profile_script(fibonacci_path, gpu=False)
    
    assert isinstance(result, ProfileResult)
    assert result.profile_id
    assert result.timestamp > 0
    # Elapsed time may be 0 for very fast scripts
    assert result.summary.elapsed_time_sec >= 0
    assert len(result.files) > 0
    # Should have CPU data
    assert result.summary.total_cpu_samples > 0


@pytest.mark.asyncio
async def test_profile_script_file_not_found(profiler: ScaleneProfiler):
    """Test profiling with non-existent file"""
    with pytest.raises(FileNotFoundError):
        await profiler.profile_script(Path("nonexistent.py"))


@pytest.mark.asyncio
async def test_profile_code_snippet(profiler: ScaleneProfiler):
    """Test profiling a code snippet"""
    code = """
def hello():
    return "world"

result = hello()
"""
    
    result = await profiler.profile_code(code)
    
    assert isinstance(result, ProfileResult)
    assert result.profile_id
    assert result.summary.elapsed_time_sec >= 0


@pytest.mark.asyncio
async def test_profile_with_cpu_only(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test CPU-only profiling mode"""
    result = await profiler.profile_script(fibonacci_path, cpu_only=True, gpu=False)
    
    assert isinstance(result, ProfileResult)
    # CPU-only mode should still produce valid results
    assert result.summary.total_cpu_samples > 0


@pytest.mark.asyncio
async def test_profile_with_memory_disabled(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test with memory profiling disabled"""
    result = await profiler.profile_script(fibonacci_path, memory=False, gpu=False)
    
    assert isinstance(result, ProfileResult)
    # Should still have CPU data
    assert result.summary.total_cpu_samples > 0


@pytest.mark.asyncio
async def test_profile_with_thresholds(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with custom thresholds"""
    result = await profiler.profile_script(
        fibonacci_path,
        cpu_percent_threshold=5.0,
        malloc_threshold=1000,
        gpu=False,
    )
    
    assert isinstance(result, ProfileResult)
    assert len(result.files) > 0


@pytest.mark.asyncio
async def test_profile_with_script_args(profiler: ScaleneProfiler, tmp_path: Path):
    """Test profiling with arguments passed to script"""
    script = tmp_path / "args_test.py"
    script.write_text("""
import sys
print(f"Args: {sys.argv[1:]}")
""")
    
    result = await profiler.profile_script(
        script,
        script_args=["--test", "value"],
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_reduced_profile(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test reduced profile mode"""
    result = await profiler.profile_script(
        fibonacci_path,
        reduced_profile=True,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_with_leak_detector(profiler: ScaleneProfiler, leaky_path: Path):
    """Test profiling with memory leak detection"""
    result = await profiler.profile_script(
        leaky_path,
        memory_leak_detector=True,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)
    # The leaky script should have some profile data
    assert len(result.files) > 0


@pytest.mark.asyncio
async def test_profile_memory_heavy(profiler: ScaleneProfiler, memory_heavy_path: Path):
    """Test profiling memory-intensive code"""
    result = await profiler.profile_script(memory_heavy_path, gpu=False)
    
    assert isinstance(result, ProfileResult)
    # Memory-heavy script should show some data
    assert len(result.files) > 0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_profile_with_timeout(profiler: ScaleneProfiler, tmp_path: Path):
    """Test profiling with timeout"""
    # Create a script that runs for a long time
    script = tmp_path / "slow.py"
    script.write_text("""
import time
time.sleep(10)
""")
    
    with pytest.raises((TimeoutError, asyncio.TimeoutError)):
        await profiler.profile_script(script, timeout=1.0, gpu=False)


@pytest.mark.asyncio
async def test_profile_invalid_python(profiler: ScaleneProfiler, tmp_path: Path):
    """Test profiling invalid Python code"""
    script = tmp_path / "invalid.py"
    script.write_text("this is not valid python syntax !@#$")
    
    with pytest.raises(RuntimeError):
        await profiler.profile_script(script)


@pytest.mark.asyncio
async def test_profile_with_all_options(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with many options combined"""
    result = await profiler.profile_script(
        fibonacci_path,
        cpu=True,
        memory=True,
        cpu_only=False,
        gpu=False,
        cpu_sampling_rate=0.001,
        cpu_percent_threshold=2.0,
        malloc_threshold=50,
        profile_all=False,
        memory_leak_detector=True,
        reduced_profile=False,
    )
    
    assert isinstance(result, ProfileResult)
    assert result.profile_id
    assert result.summary.total_cpu_samples > 0
    assert len(result.files) > 0

@pytest.mark.asyncio
async def test_profile_cpu_only(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test CPU-only profiling mode"""
    result = await profiler.profile_script(
        fibonacci_path,
        cpu_only=True,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)
    assert result.summary.total_cpu_samples > 0


@pytest.mark.asyncio
async def test_profile_no_cpu(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with CPU disabled"""
    result = await profiler.profile_script(
        fibonacci_path,
        cpu=False,
        memory=True,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_no_memory(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with memory disabled"""
    result = await profiler.profile_script(
        fibonacci_path,
        cpu=True,
        memory=False,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_with_stacks(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with stacks enabled"""
    result = await profiler.profile_script(
        fibonacci_path,
        stacks=True,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_virtual_time(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with virtual time"""
    result = await profiler.profile_script(
        fibonacci_path,
        use_virtual_time=True,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_no_leak_detector(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with leak detector disabled"""
    result = await profiler.profile_script(
        fibonacci_path,
        memory_leak_detector=False,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_custom_sampling(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with custom CPU sampling rate"""
    result = await profiler.profile_script(
        fibonacci_path,
        cpu_sampling_rate=0.005,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_profile_all(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with profile_all enabled"""
    result = await profiler.profile_script(
        fibonacci_path,
        profile_all=True,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_with_profile_only(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with profile_only filter"""
    result = await profiler.profile_script(
        fibonacci_path,
        profile_only="test_*",
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_with_profile_exclude(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with profile_exclude filter"""
    result = await profiler.profile_script(
        fibonacci_path,
        profile_exclude="site_packages",
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_code_snippet(profiler: ScaleneProfiler):
    """Test profiling a code snippet directly"""
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
"""
    result = await profiler.profile_code(code, gpu=False)
    
    assert isinstance(result, ProfileResult)
    assert result.profile_id


@pytest.mark.asyncio
async def test_profile_code_with_args(profiler: ScaleneProfiler):
    """Test profiling code snippet with arguments"""
    code = """
x = 0
for i in range(100):
    x += i
"""
    result = await profiler.profile_code(
        code,
        cpu_sampling_rate=0.01,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_custom_allocation_window(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with custom allocation sampling window"""
    result = await profiler.profile_script(
        fibonacci_path,
        allocation_sampling_window=5000000,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)


@pytest.mark.asyncio
async def test_profile_no_cpu_no_memory(profiler: ScaleneProfiler, fibonacci_path: Path):
    """Test profiling with both CPU and memory disabled"""
    # This should still create output (GPU-only or minimal data)
    result = await profiler.profile_script(
        fibonacci_path,
        cpu=False,
        memory=False,
        gpu=False
    )
    
    assert isinstance(result, ProfileResult)

