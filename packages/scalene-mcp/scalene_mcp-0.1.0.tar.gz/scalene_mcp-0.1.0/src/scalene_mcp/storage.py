"""Optional persistent storage for profile results.

This module provides opt-in file-based storage for ProfileResults.
By default, profiles are kept in-memory only. Use this for:
- Historical analysis and comparisons
- Saving important benchmark results
- Long-term performance tracking

NOT recommended for temporary profiling sessions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scalene_mcp.models import ProfileResult


class ProfileStorage:
    """Optional file-based storage for profile results."""

    def __init__(self, storage_dir: Path | str | None = None):
        """
        Initialize profile storage.

        Args:
            storage_dir: Directory to store profiles (default: ~/.scalene-mcp/profiles)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".scalene-mcp" / "profiles"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions (user only)
        self.storage_dir.chmod(0o700)

    def save(self, profile: ProfileResult) -> Path:
        """
        Save a profile result.

        Args:
            profile: ProfileResult to save

        Returns:
            Path to saved profile file
        """
        profile_path = self.storage_dir / f"{profile.profile_id}.json"
        
        # Convert to dict for JSON serialization
        profile_dict = profile.model_dump(mode="json")
        
        with open(profile_path, "w") as f:
            json.dump(profile_dict, f, indent=2)
        
        # Set restrictive permissions
        profile_path.chmod(0o600)
        
        return profile_path

    def load(self, profile_id: str) -> ProfileResult:
        """
        Load a profile result.

        Args:
            profile_id: ID of profile to load

        Returns:
            Loaded ProfileResult

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        profile_path = self.storage_dir / f"{profile_id}.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_id}")
        
        with open(profile_path) as f:
            profile_dict = json.load(f)
        
        return ProfileResult(**profile_dict)

    def list_profiles(self) -> list[str]:
        """
        List all stored profile IDs.

        Returns:
            List of profile IDs
        """
        return [
            p.stem for p in self.storage_dir.glob("*.json")
        ]

    def delete(self, profile_id: str) -> bool:
        """
        Delete a profile.

        Args:
            profile_id: ID of profile to delete

        Returns:
            True if deleted, False if not found
        """
        profile_path = self.storage_dir / f"{profile_id}.json"
        
        if profile_path.exists():
            profile_path.unlink()
            return True
        
        return False

    def exists(self, profile_id: str) -> bool:
        """
        Check if a profile exists.

        Args:
            profile_id: ID of profile to check

        Returns:
            True if profile exists
        """
        profile_path = self.storage_dir / f"{profile_id}.json"
        return profile_path.exists()

    def get_metadata(self, profile_id: str) -> dict[str, Any]:
        """
        Get profile metadata without loading full profile.

        Args:
            profile_id: ID of profile

        Returns:
            Dictionary with profile metadata

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        profile_path = self.storage_dir / f"{profile_id}.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_id}")
        
        with open(profile_path) as f:
            data = json.load(f)
        
        # Return just summary fields
        return {
            "profile_id": data.get("profile_id"),
            "timestamp": data.get("timestamp"),
            "elapsed_time_sec": data.get("summary", {}).get("elapsed_time_sec"),
            "max_memory_mb": data.get("summary", {}).get("max_memory_mb"),
            "files_profiled": data.get("summary", {}).get("files_profiled", []),
            "has_memory_leaks": data.get("summary", {}).get("has_memory_leaks", False),
        }
    
    def cleanup_old(self, max_age_days: int) -> int:
        """
        Delete profiles older than specified days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of profiles deleted
        """
        import time
        
        cutoff = time.time() - (max_age_days * 24 * 60 * 60)
        deleted = 0
        
        for profile_path in self.storage_dir.glob("*.json"):
            if profile_path.stat().st_mtime < cutoff:
                profile_path.unlink()
                deleted += 1
        
        return deleted
    
    def clear_all(self) -> int:
        """
        Delete all stored profiles.

        Returns:
            Number of profiles deleted
        """
        deleted = 0
        
        for profile_path in self.storage_dir.glob("*.json"):
            profile_path.unlink()
            deleted += 1
        
        return deleted


