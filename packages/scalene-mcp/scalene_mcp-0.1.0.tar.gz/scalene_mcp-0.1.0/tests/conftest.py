"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import FastMCP

# Import the actual MCP server instance
from scalene_mcp import server as mcp_server

# ============================================================================
# Directory Fixtures
# ============================================================================


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def profiles_dir(fixtures_dir: Path) -> Path:
    """Path to sample profile outputs."""
    return fixtures_dir / "profiles"


@pytest.fixture
def scripts_dir(fixtures_dir: Path) -> Path:
    """Path to sample scripts."""
    return fixtures_dir / "scripts"


# ============================================================================
# MCP Server Fixture
# ============================================================================


@pytest.fixture
def server() -> FastMCP:
    """FastMCP server instance for testing."""
    return mcp_server


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_profile_simple(profiles_dir: Path) -> dict:
    """Simple CPU profile data."""
    with open(profiles_dir / "simple_cpu.json") as f:
        return json.load(f)


@pytest.fixture
def sample_profile_leak(profiles_dir: Path) -> dict:
    """Profile with memory leaks."""
    with open(profiles_dir / "memory_leak.json") as f:
        return json.load(f)


@pytest.fixture
def sample_profile_memory_heavy(profiles_dir: Path) -> dict:
    """Memory-intensive profile data."""
    with open(profiles_dir / "memory_heavy.json") as f:
        return json.load(f)


@pytest.fixture
def fibonacci_script(scripts_dir: Path) -> Path:
    """Path to fibonacci test script."""
    return scripts_dir / "fibonacci.py"


@pytest.fixture
def memory_heavy_script(scripts_dir: Path) -> Path:
    """Path to memory-intensive test script."""
    return scripts_dir / "memory_heavy.py"


@pytest.fixture
def leaky_script(scripts_dir: Path) -> Path:
    """Path to script with memory leaks."""
    return scripts_dir / "leaky.py"


# ============================================================================
# Profile File Path Fixtures (for analyzer/parser testing)
# ============================================================================


@pytest.fixture
def simple_cpu_profile_json(profiles_dir: Path) -> Path:
    """Path to simple CPU profile JSON file."""
    return profiles_dir / "simple_cpu.json"


@pytest.fixture
def memory_leak_profile_json(profiles_dir: Path) -> Path:
    """Path to memory leak profile JSON file."""
    return profiles_dir / "memory_leak.json"


@pytest.fixture
def memory_heavy_profile_json(profiles_dir: Path) -> Path:
    """Path to memory-heavy profile JSON file."""
    return profiles_dir / "memory_heavy.json"
