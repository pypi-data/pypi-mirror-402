"""Comprehensive tests for profile storage module."""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

from scalene_mcp.models import FileMetrics, ProfileResult, ProfileSummary
from scalene_mcp.storage import ProfileStorage


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create a ProfileStorage instance with temp directory."""
    return ProfileStorage(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_profile():
    """Create a sample profile for testing."""
    return ProfileResult(
        profile_id="test-profile-1",
        timestamp=1000.0,
        summary=ProfileSummary(
            profile_id="test-profile-1",
            timestamp=1000.0,
            elapsed_time_sec=1.0,
            max_memory_mb=100.0,
            total_allocations_mb=50.0,
            allocation_count=1000,
            total_cpu_samples=5000,
            python_time_percent=70.0,
            native_time_percent=20.0,
            system_time_percent=10.0,
            files_profiled=["test.py"],
            lines_profiled=50,
        ),
        files={
            "test.py": FileMetrics(
                filename="test.py",
                total_cpu_percent=50.0,
            )
        },
        scalene_version="1.0.0",
    )


@pytest.fixture
def another_profile():
    """Create a different profile for testing."""
    return ProfileResult(
        profile_id="test-profile-2",
        timestamp=2000.0,
        summary=ProfileSummary(
            profile_id="test-profile-2",
            timestamp=2000.0,
            elapsed_time_sec=2.0,
            max_memory_mb=200.0,
            total_allocations_mb=100.0,
            allocation_count=2000,
            total_cpu_samples=10000,
            python_time_percent=60.0,
            native_time_percent=30.0,
            system_time_percent=10.0,
            files_profiled=["other.py"],
            lines_profiled=100,
        ),
        files={
            "other.py": FileMetrics(
                filename="other.py",
                total_cpu_percent=60.0,
            )
        },
        scalene_version="1.0.0",
    )


class TestProfileStorageInit:
    """Test ProfileStorage initialization."""

    def test_storage_creation_default(self):
        """Test creating ProfileStorage with default directory."""
        storage = ProfileStorage()
        assert storage.storage_dir is not None
        assert isinstance(storage.storage_dir, Path)

    def test_storage_creation_custom_dir(self, temp_storage_dir):
        """Test creating ProfileStorage with custom directory."""
        storage = ProfileStorage(storage_dir=temp_storage_dir)
        assert storage.storage_dir == temp_storage_dir

    def test_storage_creation_string_path(self, temp_storage_dir):
        """Test creating ProfileStorage with string path."""
        storage = ProfileStorage(storage_dir=str(temp_storage_dir))
        assert storage.storage_dir == temp_storage_dir

    def test_storage_creates_directory(self):
        """Test that ProfileStorage creates directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "storage" / "path"
            assert not new_dir.exists()
            storage = ProfileStorage(storage_dir=new_dir)
            assert new_dir.exists()

    def test_storage_sets_permissions(self, temp_storage_dir):
        """Test that storage directory has restrictive permissions."""
        storage = ProfileStorage(storage_dir=temp_storage_dir)
        # Permissions should be 0o700 (user only)
        assert oct(temp_storage_dir.stat().st_mode)[-3:] == "700"


class TestProfileStorageSaveLoad:
    """Test save and load operations."""

    def test_save_profile(self, storage, sample_profile):
        """Test saving a profile."""
        path = storage.save(sample_profile)
        assert path.exists()
        assert path.name == "test-profile-1.json"

    def test_save_profile_returns_path(self, storage, sample_profile):
        """Test save returns correct path."""
        path = storage.save(sample_profile)
        assert isinstance(path, Path)
        assert path.parent == storage.storage_dir

    def test_save_creates_json_file(self, storage, sample_profile):
        """Test saved file is valid JSON."""
        storage.save(sample_profile)
        profile_path = storage.storage_dir / "test-profile-1.json"
        with open(profile_path) as f:
            data = json.load(f)
        assert data["profile_id"] == "test-profile-1"

    def test_save_profile_permissions(self, storage, sample_profile):
        """Test saved profile has restrictive permissions."""
        path = storage.save(sample_profile)
        # Permissions should be 0o600 (user only)
        assert oct(path.stat().st_mode)[-3:] == "600"

    def test_load_profile(self, storage, sample_profile):
        """Test loading a saved profile."""
        storage.save(sample_profile)
        loaded = storage.load("test-profile-1")
        assert loaded.profile_id == "test-profile-1"
        assert loaded.timestamp == 1000.0

    def test_load_preserves_data(self, storage, sample_profile):
        """Test that loaded profile matches original."""
        storage.save(sample_profile)
        loaded = storage.load("test-profile-1")
        assert loaded.summary.elapsed_time_sec == 1.0
        assert loaded.summary.max_memory_mb == 100.0

    def test_load_nonexistent_raises(self, storage):
        """Test loading nonexistent profile raises."""
        with pytest.raises(FileNotFoundError):
            storage.load("nonexistent")

    def test_load_nonexistent_message(self, storage):
        """Test error message for nonexistent profile."""
        with pytest.raises(FileNotFoundError, match="Profile not found"):
            storage.load("missing-id")

    def test_save_overwrites_existing(self, storage, sample_profile, another_profile):
        """Test saving overwrites existing profile."""
        storage.save(sample_profile)
        # Save different data with same ID
        another_profile.profile_id = "test-profile-1"
        storage.save(another_profile)
        
        loaded = storage.load("test-profile-1")
        assert loaded.summary.elapsed_time_sec == 2.0


class TestProfileStorageList:
    """Test list_profiles operation."""

    def test_list_empty_storage(self, storage):
        """Test listing profiles from empty storage."""
        profiles = storage.list_profiles()
        assert profiles == []
        assert isinstance(profiles, list)

    def test_list_single_profile(self, storage, sample_profile):
        """Test listing one profile."""
        storage.save(sample_profile)
        profiles = storage.list_profiles()
        assert len(profiles) == 1
        assert "test-profile-1" in profiles

    def test_list_multiple_profiles(self, storage, sample_profile, another_profile):
        """Test listing multiple profiles."""
        storage.save(sample_profile)
        storage.save(another_profile)
        profiles = storage.list_profiles()
        assert len(profiles) == 2
        assert "test-profile-1" in profiles
        assert "test-profile-2" in profiles

    def test_list_returns_strings(self, storage, sample_profile):
        """Test list_profiles returns list of strings."""
        storage.save(sample_profile)
        profiles = storage.list_profiles()
        assert all(isinstance(p, str) for p in profiles)


class TestProfileStorageDelete:
    """Test delete operation."""

    def test_delete_existing_profile(self, storage, sample_profile):
        """Test deleting an existing profile."""
        storage.save(sample_profile)
        assert storage.exists("test-profile-1")
        result = storage.delete("test-profile-1")
        assert result is True
        assert not storage.exists("test-profile-1")

    def test_delete_nonexistent_returns_false(self, storage):
        """Test deleting nonexistent profile returns False."""
        result = storage.delete("nonexistent")
        assert result is False

    def test_delete_removes_file(self, storage, sample_profile):
        """Test delete actually removes the file."""
        path = storage.save(sample_profile)
        assert path.exists()
        storage.delete("test-profile-1")
        assert not path.exists()

    def test_delete_multiple_profiles(self, storage, sample_profile, another_profile):
        """Test deleting specific profile doesn't affect others."""
        storage.save(sample_profile)
        storage.save(another_profile)
        storage.delete("test-profile-1")
        assert not storage.exists("test-profile-1")
        assert storage.exists("test-profile-2")

    def test_delete_and_relist(self, storage, sample_profile, another_profile):
        """Test list after deletion."""
        storage.save(sample_profile)
        storage.save(another_profile)
        storage.delete("test-profile-1")
        profiles = storage.list_profiles()
        assert len(profiles) == 1
        assert "test-profile-2" in profiles


class TestProfileStorageExists:
    """Test exists operation."""

    def test_exists_for_saved_profile(self, storage, sample_profile):
        """Test exists returns True for saved profile."""
        storage.save(sample_profile)
        assert storage.exists("test-profile-1") is True

    def test_exists_for_unsaved_profile(self, storage):
        """Test exists returns False for unsaved profile."""
        assert storage.exists("nonexistent") is False

    def test_exists_after_delete(self, storage, sample_profile):
        """Test exists returns False after deletion."""
        storage.save(sample_profile)
        storage.delete("test-profile-1")
        assert storage.exists("test-profile-1") is False


class TestProfileStorageMetadata:
    """Test get_metadata operation."""

    def test_metadata_returns_dict(self, storage, sample_profile):
        """Test metadata returns dictionary."""
        storage.save(sample_profile)
        metadata = storage.get_metadata("test-profile-1")
        assert isinstance(metadata, dict)

    def test_metadata_contains_profile_id(self, storage, sample_profile):
        """Test metadata contains profile_id."""
        storage.save(sample_profile)
        metadata = storage.get_metadata("test-profile-1")
        assert metadata["profile_id"] == "test-profile-1"

    def test_metadata_contains_timestamp(self, storage, sample_profile):
        """Test metadata contains timestamp."""
        storage.save(sample_profile)
        metadata = storage.get_metadata("test-profile-1")
        assert metadata["timestamp"] == 1000.0

    def test_metadata_contains_elapsed_time(self, storage, sample_profile):
        """Test metadata contains elapsed_time_sec."""
        storage.save(sample_profile)
        metadata = storage.get_metadata("test-profile-1")
        assert metadata["elapsed_time_sec"] == 1.0

    def test_metadata_contains_memory(self, storage, sample_profile):
        """Test metadata contains max_memory_mb."""
        storage.save(sample_profile)
        metadata = storage.get_metadata("test-profile-1")
        assert metadata["max_memory_mb"] == 100.0

    def test_metadata_contains_files_profiled(self, storage, sample_profile):
        """Test metadata contains files_profiled list."""
        storage.save(sample_profile)
        metadata = storage.get_metadata("test-profile-1")
        assert "files_profiled" in metadata
        assert isinstance(metadata["files_profiled"], list)

    def test_metadata_nonexistent_raises(self, storage):
        """Test metadata for nonexistent profile raises."""
        with pytest.raises(FileNotFoundError):
            storage.get_metadata("nonexistent")


class TestProfileStorageClearAll:
    """Test clear_all operation."""

    def test_clear_all_empty_storage(self, storage):
        """Test clear_all on empty storage."""
        deleted = storage.clear_all()
        assert deleted == 0

    def test_clear_all_single_profile(self, storage, sample_profile):
        """Test clear_all with one profile."""
        storage.save(sample_profile)
        deleted = storage.clear_all()
        assert deleted == 1
        assert len(storage.list_profiles()) == 0

    def test_clear_all_multiple_profiles(self, storage, sample_profile, another_profile):
        """Test clear_all with multiple profiles."""
        storage.save(sample_profile)
        storage.save(another_profile)
        deleted = storage.clear_all()
        assert deleted == 2
        assert len(storage.list_profiles()) == 0

    def test_clear_all_returns_count(self, storage, sample_profile, another_profile):
        """Test clear_all returns correct count."""
        storage.save(sample_profile)
        storage.save(another_profile)
        deleted = storage.clear_all()
        assert deleted == 2


class TestProfileStorageCleanup:
    """Test cleanup_old operation."""

    def test_cleanup_old_empty_storage(self, storage):
        """Test cleanup on empty storage."""
        deleted = storage.cleanup_old(max_age_days=1)
        assert deleted == 0

    def test_cleanup_old_young_profile(self, storage, sample_profile):
        """Test cleanup doesn't delete young profiles."""
        storage.save(sample_profile)
        deleted = storage.cleanup_old(max_age_days=100)
        assert deleted == 0
        assert storage.exists("test-profile-1")

    def test_cleanup_old_returns_count(self, storage, sample_profile):
        """Test cleanup_old returns integer count."""
        storage.save(sample_profile)
        deleted = storage.cleanup_old(max_age_days=100)
        assert isinstance(deleted, int)

    def test_cleanup_old_deletes_old_files(self, storage, sample_profile):
        """Test cleanup_old actually deletes old files."""
        # Save a profile
        storage.save(sample_profile)
        profile_path = storage.storage_dir / "test-profile-1.json"
        assert profile_path.exists()
        
        # Mock the file to be old by setting its modification time to past
        old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
        with mock.patch("time.time", return_value=time.time()):
            # Actually set the file's mtime to the past
            os.utime(profile_path, (old_time, old_time))
        
        # Now cleanup with 5 day max age should delete it
        deleted = storage.cleanup_old(max_age_days=5)
        assert deleted == 1
        assert not profile_path.exists()


class TestProfileStorageEdgeCases:
    """Test edge cases and error conditions."""

    def test_storage_with_special_chars_in_id(self, storage):
        """Test profile with special characters in ID."""
        profile = ProfileResult(
            profile_id="test-id_v2.0",
            timestamp=1000.0,
            summary=ProfileSummary(
                profile_id="test-id_v2.0",
                timestamp=1000.0,
                elapsed_time_sec=1.0,
                max_memory_mb=100.0,
                total_allocations_mb=50.0,
                allocation_count=1000,
                total_cpu_samples=5000,
                python_time_percent=70.0,
                native_time_percent=20.0,
                system_time_percent=10.0,
                files_profiled=[],
                lines_profiled=0,
            ),
            files={},
            scalene_version="1.0.0",
        )
        path = storage.save(profile)
        assert path.exists()
        loaded = storage.load("test-id_v2.0")
        assert loaded.profile_id == "test-id_v2.0"

    def test_multiple_storage_instances_independent(self, temp_storage_dir, sample_profile):
        """Test multiple storage instances use same directory."""
        storage1 = ProfileStorage(storage_dir=temp_storage_dir)
        storage2 = ProfileStorage(storage_dir=temp_storage_dir)
        
        storage1.save(sample_profile)
        # Second instance should see the profile
        profiles = storage2.list_profiles()
        assert "test-profile-1" in profiles

    def test_load_after_save_preserves_type(self, storage, sample_profile):
        """Test loaded profile is correct type."""
        storage.save(sample_profile)
        loaded = storage.load("test-profile-1")
        assert isinstance(loaded, ProfileResult)

    def test_large_profile_storage(self, storage):
        """Test storing large profile."""
        profile = ProfileResult(
            profile_id="large-profile",
            timestamp=1000.0,
            summary=ProfileSummary(
                profile_id="large-profile",
                timestamp=1000.0,
                elapsed_time_sec=1.0,
                max_memory_mb=100.0,
                total_allocations_mb=50.0,
                allocation_count=1000,
                total_cpu_samples=5000,
                python_time_percent=70.0,
                native_time_percent=20.0,
                system_time_percent=10.0,
                files_profiled=[f"file_{i}.py" for i in range(100)],
                lines_profiled=10000,
            ),
            files={
                f"file_{i}.py": FileMetrics(
                    filename=f"file_{i}.py",
                    total_cpu_percent=50.0,
                )
                for i in range(100)
            },
            scalene_version="1.0.0",
        )
        path = storage.save(profile)
        loaded = storage.load("large-profile")
        assert len(loaded.summary.files_profiled) == 100
        assert len(loaded.files) == 100


class TestProfileStorageIntegration:
    """Integration tests for complete workflows."""

    def test_complete_workflow(self, storage, sample_profile, another_profile):
        """Test complete save->list->load->delete workflow."""
        # Save profiles
        storage.save(sample_profile)
        storage.save(another_profile)
        
        # List should show both
        profiles = storage.list_profiles()
        assert len(profiles) == 2
        
        # Load and verify
        loaded1 = storage.load("test-profile-1")
        assert loaded1.profile_id == "test-profile-1"
        
        # Get metadata
        meta = storage.get_metadata("test-profile-1")
        assert meta["elapsed_time_sec"] == 1.0
        
        # Delete one
        storage.delete("test-profile-1")
        profiles = storage.list_profiles()
        assert len(profiles) == 1
        
        # Verify deleted
        assert not storage.exists("test-profile-1")
        assert storage.exists("test-profile-2")

    def test_multiple_saves_same_profile(self, storage, sample_profile):
        """Test saving same profile multiple times."""
        path1 = storage.save(sample_profile)
        path2 = storage.save(sample_profile)
        
        # Should overwrite, single file exists
        assert path1 == path2
        assert len(storage.list_profiles()) == 1

    def test_concurrent_directory_operations(self, temp_storage_dir):
        """Test multiple storage instances work together."""
        storage1 = ProfileStorage(storage_dir=temp_storage_dir)
        storage2 = ProfileStorage(storage_dir=temp_storage_dir)
        
        profile = ProfileResult(
            profile_id="shared-profile",
            timestamp=1000.0,
            summary=ProfileSummary(
                profile_id="shared-profile",
                timestamp=1000.0,
                elapsed_time_sec=1.0,
                max_memory_mb=100.0,
                total_allocations_mb=50.0,
                allocation_count=1000,
                total_cpu_samples=5000,
                python_time_percent=70.0,
                native_time_percent=20.0,
                system_time_percent=10.0,
                files_profiled=[],
                lines_profiled=0,
            ),
            files={},
            scalene_version="1.0.0",
        )
        
        storage1.save(profile)
        loaded = storage2.load("shared-profile")
        assert loaded.profile_id == "shared-profile"
