# Troubleshooting Guide

Common issues and solutions for Scalene-MCP.

## Installation Issues

### Python Version Not Supported

**Error**: `Python 3.10+ required`

**Solution**:
```bash
python --version  # Check your version
python3.10 --version  # Try python3.10
# If not installed, use pyenv or conda
pyenv install 3.11.0
pyenv local 3.11.0
```

---

### Dependencies Not Installing

**Error**: `ModuleNotFoundError` when importing

**Solution**:
```bash
# Reinstall with development dependencies
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"

# Verify installation
python -c "import scalene_mcp; print(scalene_mcp.__version__)"
```

---

### Scalene Not Found

**Error**: `Command 'scalene' not found` or similar

**Solution**:
```bash
# Ensure Scalene is installed
pip install scalene

# Or in development environment
uv add scalene

# Verify it works
python -m scalene --version
```

---

## Runtime Issues

### GPU Permission Error

**Error**: `PermissionError` when profiling with GPU

**Root Cause**: GPU profiling requires special permissions in some environments (CI, containers)

**Solution**:
```python
# Disable GPU profiling
result = await profiler.profile_script(
    "script.py",
    gpu=False  # ← Add this
)
```

**Alternative - Fix Environment**:
```bash
# On Linux, add user to video group
sudo usermod -a -G video $USER
newgrp video

# Verify GPU access
nvidia-smi  # Should work without sudo
```

---

### Timeout Error

**Error**: `asyncio.TimeoutError: Profiling timed out`

**Root Cause**: Script execution exceeded timeout limit

**Solution**:
```python
# Increase timeout for long-running scripts
result = await profiler.profile_script(
    "slow_script.py",
    timeout=300.0  # 5 minutes instead of 2
)
```

**Troubleshooting**:
```python
# Disable timeout entirely
result = await profiler.profile_script(
    "slow_script.py",
    timeout=None  # No timeout
)

# But ALWAYS use timeout in production to prevent hangs
```

---

### Script Not Found

**Error**: `FileNotFoundError: script.py not found`

**Solution**:
```python
from pathlib import Path

# Use absolute path
script_path = Path(__file__).parent / "scripts" / "app.py"
result = await profiler.profile_script(str(script_path))

# Or verify file exists
from pathlib import Path
if not Path("script.py").exists():
    raise FileNotFoundError("script.py not found")
```

---

### Script Crashes During Profiling

**Error**: `RuntimeError: Script execution failed` with no useful traceback

**Solution**:
```python
# Run script manually first to see the error
python script.py

# Then check result.errors for warnings
result = await profiler.profile_script("script.py")
if result.errors:
    for error in result.errors:
        print(f"Warning: {error}")
```

---

### No JSON Output

**Error**: `InvalidProfileError: No valid JSON found in output`

**Root Cause**: Scalene didn't produce JSON output (script crashed silently)

**Solution**:
```bash
# Test the script directly
python -m scalene run --json --outfile test.json script.py

# Check if it produces output
cat test.json | head
```

---

### JSON Parsing Error

**Error**: `json.JSONDecodeError: Expecting value`

**Root Cause**: Incomplete or corrupted JSON

**Solution**:
```python
# Check the JSON file manually
import json
with open("profile.json") as f:
    data = json.load(f)  # This will show the exact error
```

---

## Memory Issues

### High Memory Usage

**Symptom**: Scalene-MCP uses excessive memory

**Solution**:
```python
# Profile with memory disabled if not needed
result = await profiler.profile_script(
    "script.py",
    cpu=True,
    memory=False,  # Skip memory profiling
)

# Use reduced_profile for large codebases
result = await profiler.profile_script(
    "script.py",
    reduced_profile=True,  # Less output = less memory
)
```

---

### Memory Leak in Server

**Symptom**: Server memory grows over time

**Root Cause**: Profiles stored in memory

**Current Workaround**:
```python
# Clear old profiles
from scalene_mcp.server import recent_profiles

# Periodically clear old profiles
if len(recent_profiles) > 100:
    recent_profiles.clear()
```

**Future Solution**: Implement persistent storage with automatic cleanup

---

## Performance Issues

### Profiling Very Slow

**Symptom**: Profiling takes much longer than expected

**Root Causes & Solutions**:

1. **Too many profiling options enabled**:
   ```python
   # Disable unnecessary profiling
   result = await profiler.profile_script(
       "script.py",
       cpu=True,      # Only enable what you need
       memory=False,
       gpu=False,
       stacks=False,  # Stack collection is expensive
   )
   ```

2. **Too low sampling rate**:
   ```python
   # Increase sampling rate (slower → faster)
   result = await profiler.profile_script(
       "script.py",
       cpu_sampling_rate=0.1,  # 100ms intervals
   )
   ```

3. **Large codebase**:
   ```python
   # Profile only relevant code
   result = await profiler.profile_script(
       "script.py",
       profile_only="mymodule",  # Only profile this
       profile_exclude="test",   # Exclude tests
       reduced_profile=True,     # Minimal output
   )
   ```

---

### Analysis Very Slow

**Symptom**: Analyzer takes a long time to process profile

**Root Causes**:

1. **Very large profile** (millions of lines):
   ```python
   # Use reduced_profile during profiling
   result = await profiler.profile_script(
       "huge_codebase.py",
       reduced_profile=True,
   )
   ```

2. **Expensive analysis**:
   ```python
   # Limit analysis scope
   hotspots = analyzer.get_hotspots(result, limit=5)  # Top 5
   ```

---

## Debugging

### Enable Debug Logging

```python
from scalene_mcp.logging import configure_logging
import logging

# Enable DEBUG level logging
configure_logging(logging.DEBUG)

# Now run profiling
result = await profiler.profile_script("script.py")
# Will show detailed debug messages
```

---

### Inspect Profile Data

```python
# Print profile structure
import json
from scalene_mcp.models import ProfileResult

result = await profiler.profile_script("script.py")

# Convert to dict
profile_dict = result.dict()
print(json.dumps(profile_dict, indent=2, default=str))

# Inspect specific parts
if result.cpu_profile:
    print(f"Total Python time: {result.cpu_profile.total_python_time_sec}s")

if result.memory_profile:
    print(f"Peak memory: {result.memory_profile.peak_mb}MB")
```

---

### Compare Against Reference

```python
# Take a reference profile
import pickle

reference = await profiler.profile_script("script.py")

# Save for comparison
with open("reference.pkl", "wb") as f:
    pickle.dump(reference, f)

# Later, load and compare
with open("reference.pkl", "rb") as f:
    reference = pickle.load(f)

current = await profiler.profile_script("script.py")
comparison = comparator.compare(reference, current)

if comparison.regressions:
    print("Performance regression detected!")
```

---

## Platform-Specific Issues

### macOS GPU Profiling

**Issue**: Apple GPU profiling may not work

**Solution**:
```python
# Disable Apple GPU profiling
result = await profiler.profile_script(
    "script.py",
    gpu=False
)
```

---

### Windows Compatibility

**Issue**: Some features may not work on Windows

**Workaround**:
```python
import platform

# Check if running on Windows
if platform.system() == "Windows":
    # Windows limitations
    result = await profiler.profile_script(
        "script.py",
        memory=False,  # Memory profiling limited on Windows
    )
```

---

### Docker/Container Issues

**Issue**: GPU/memory profiling may not work in containers

**Solution - Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev

# Install Python packages
RUN pip install scalene-mcp fastmcp

# Run the server
CMD ["python", "-m", "scalene_mcp.server"]
```

**Solution - docker-compose.yml**:
```yaml
version: '3'
services:
  scalene-mcp:
    build: .
    # Allow GPU access
    runtime: nvidia
    # Or for Apple
    # device_support: metal
    environment:
      - SCALENE_CPU_PERCENT_THRESHOLD=1.0
```

---

## Common Errors and Fixes

### Error: "No module named 'scalene_mcp'"

**Solution**:
```bash
# Install from source
git clone https://github.com/...
cd scalene-mcp
pip install -e .

# Or install from PyPI
pip install scalene-mcp
```

---

### Error: "Scalene reported error"

**Debugging**:
```python
# Run Scalene manually
import subprocess
result = subprocess.run(
    ["python", "-m", "scalene", "run", "--json", "--outfile", "test.json", "script.py"],
    capture_output=True,
    text=True
)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
print("return code:", result.returncode)
```

---

### Error: "Profile comparison failed"

**Debugging**:
```python
# Check if profiles are compatible
profile1 = await profiler.profile_script("v1/app.py")
profile2 = await profiler.profile_script("v2/app.py")

# Verify both have the same files
files1 = set(profile1.cpu_profile.lines.keys()) if profile1.cpu_profile else set()
files2 = set(profile2.cpu_profile.lines.keys()) if profile2.cpu_profile else set()

if files1 != files2:
    print("Warning: Different files profiled!")
    print(f"Only in v1: {files1 - files2}")
    print(f"Only in v2: {files2 - files1}")
```

---

## Getting Help

### Check the Logs

```bash
# Run with full debug logging
SCALENE_LOG_LEVEL=DEBUG python your_script.py 2>&1 | tee debug.log

# Review debug.log for clues
less debug.log
```

---

### Minimal Reproduction

Create a simple test case:
```python
# minimal_test.py
import asyncio
from scalene_mcp.profiler import ScaleneProfiler

async def main():
    profiler = ScaleneProfiler()
    result = await profiler.profile_code(
        "x = sum(range(1000))"
    )
    print(result)

asyncio.run(main())
```

Run it:
```bash
python minimal_test.py
```

---

### Submit a Bug Report

Include:
1. Python version (`python --version`)
2. OS and version
3. Installation method
4. Minimal reproduction
5. Full error traceback
6. Debug log output

---

## Frequently Asked Questions

**Q: Can I profile async code?**
A: Yes! Scalene works with async/await code.

**Q: Can I profile long-running services?**
A: Yes, use `timeout=None` but always set a timeout in production.

**Q: Does profiling overhead vary by code?**
A: Yes, overhead depends on code complexity and profiling options.

**Q: Can I profile C extensions?**
A: Yes, Scalene can profile C time in extensions.

**Q: Is GPU profiling accurate?**
A: Depends on GPU and driver. Test in your specific environment.

---

## Performance Optimization Tips

### Quick Profiling

```python
# For fast results, minimize profiling scope
result = await profiler.profile_script(
    "script.py",
    cpu=True,              # Only CPU
    memory=False,
    gpu=False,
    stacks=False,          # No stacks
    reduced_profile=True,  # Minimal output
)
```

### Detailed Analysis

```python
# For thorough analysis, enable everything
result = await profiler.profile_script(
    "script.py",
    cpu=True,
    memory=True,
    gpu=True,
    stacks=True,           # Include stacks
    reduced_profile=False, # Full output
)
```

### Memory-Constrained Environment

```python
# For low-memory environments
result = await profiler.profile_script(
    "script.py",
    cpu=True,
    memory=False,  # Skip memory (expensive)
    profile_exclude="test,vendor",  # Skip large dirs
)
```

---

## Support Resources

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Read [docs/](../) for detailed guides
- **Examples**: Check [docs/examples.md](./examples.md) for usage patterns