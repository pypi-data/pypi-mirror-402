"""Tests for fixtures and test infrastructure."""

# Minimum expected memory for memory_heavy profile
MEMORY_HEAVY_MIN_MB = 100.0


def test_fixtures_dir_exists(fixtures_dir):
    """Test that fixtures directory exists."""
    assert fixtures_dir.exists()
    assert fixtures_dir.is_dir()


def test_profiles_dir_exists(profiles_dir):
    """Test that profiles directory exists."""
    assert profiles_dir.exists()
    assert profiles_dir.is_dir()


def test_scripts_dir_exists(scripts_dir):
    """Test that scripts directory exists."""
    assert scripts_dir.exists()
    assert scripts_dir.is_dir()


def test_sample_profile_simple_loads(sample_profile_simple):
    """Test that simple profile fixture loads correctly."""
    assert "elapsed_time_seconds" in sample_profile_simple
    assert "files" in sample_profile_simple
    assert "fibonacci.py" in sample_profile_simple["files"]
    assert sample_profile_simple["elapsed_time_seconds"] > 0


def test_sample_profile_leak_loads(sample_profile_leak):
    """Test that leak profile fixture loads correctly."""
    assert "elapsed_time_seconds" in sample_profile_leak
    assert "files" in sample_profile_leak
    assert "leaky.py" in sample_profile_leak["files"]
    
    # Check leak detection data
    file_data = sample_profile_leak["files"]["leaky.py"]
    assert "leaks" in file_data
    assert len(file_data["leaks"]) > 0


def test_sample_profile_memory_heavy_loads(sample_profile_memory_heavy):
    """Test that memory heavy profile fixture loads correctly."""
    assert "elapsed_time_seconds" in sample_profile_memory_heavy
    assert "files" in sample_profile_memory_heavy
    assert "memory_heavy.py" in sample_profile_memory_heavy["files"]
    assert sample_profile_memory_heavy["max_footprint_mb"] > MEMORY_HEAVY_MIN_MB


def test_fibonacci_script_exists(fibonacci_script):
    """Test that fibonacci test script exists."""
    assert fibonacci_script.exists()
    assert fibonacci_script.suffix == ".py"


def test_memory_heavy_script_exists(memory_heavy_script):
    """Test that memory heavy test script exists."""
    assert memory_heavy_script.exists()
    assert memory_heavy_script.suffix == ".py"


def test_leaky_script_exists(leaky_script):
    """Test that leaky test script exists."""
    assert leaky_script.exists()
    assert leaky_script.suffix == ".py"
