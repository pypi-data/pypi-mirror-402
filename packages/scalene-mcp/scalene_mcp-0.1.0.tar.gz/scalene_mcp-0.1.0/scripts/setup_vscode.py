#!/usr/bin/env python3
"""Auto-setup script for Scalene MCP Server in VSCode.

This script helps you quickly configure the Scalene MCP Server for:
- GitHub Copilot
- Claude Code
- Cursor

Usage:
    python setup_vscode.py
"""

import json
import sys
from pathlib import Path


def find_vscode_settings() -> Path | None:
    """Find VSCode settings.json file."""
    home = Path.home()
    
    # Try common locations
    candidates = [
        home / ".config/Code/User/settings.json",  # Linux
        home / "AppData/Roaming/Code/User/settings.json",  # Windows
        home / "Library/Application Support/Code/User/settings.json",  # macOS
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    return None


def read_settings(path: Path) -> dict:
    """Read VSCode settings.json."""
    try:
        with open(path) as f:
            content = f.read().strip()
            # Handle empty file
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {path}: {e}")
        return {}


def write_settings(path: Path, settings: dict) -> bool:
    """Write VSCode settings.json."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error writing {path}: {e}")
        return False


def setup_github_copilot(settings: dict) -> dict:
    """Add Scalene to GitHub Copilot configuration."""
    if "github.copilot.chat.mcp.servers" not in settings:
        settings["github.copilot.chat.mcp.servers"] = {}
    
    settings["github.copilot.chat.mcp.servers"]["scalene"] = {
        "command": "uv",
        "args": ["run", "-m", "scalene_mcp.server"]
    }
    
    return settings


def setup_claude_code(settings: dict) -> dict:
    """Add Scalene to Claude Code configuration."""
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    
    settings["mcpServers"]["scalene"] = {
        "command": "uv",
        "args": ["run", "-m", "scalene_mcp.server"]
    }
    
    return settings


def setup_cursor(settings: dict) -> dict:
    """Add Scalene to Cursor configuration."""
    if "mcp" not in settings:
        settings["mcp"] = {}
    if "servers" not in settings["mcp"]:
        settings["mcp"]["servers"] = {}
    
    settings["mcp"]["servers"]["scalene"] = {
        "command": "uv",
        "args": ["run", "-m", "scalene_mcp.server"]
    }
    
    return settings


def main():
    """Main setup function."""
    print("🚀 Scalene MCP Server - VSCode Setup")
    print("=" * 50)
    print()
    
    # Find settings file
    settings_path = find_vscode_settings()
    if not settings_path:
        print("❌ Could not find VSCode settings.json")
        print()
        print("Please manually add configuration:")
        print("1. Open VSCode Settings (Ctrl+,)")
        print("2. Search for 'MCP' or open settings.json")
        print("3. Add one of the configurations from SETUP_VSCODE.md")
        return 1
    
    print(f"✓ Found VSCode settings: {settings_path}")
    print()
    
    # Read existing settings
    settings = read_settings(settings_path)
    
    # Show options
    print("Which editor are you using?")
    print("1. GitHub Copilot")
    print("2. Claude Code")
    print("3. Cursor")
    print("4. All of the above")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n⚙️  Configuring GitHub Copilot...")
        settings = setup_github_copilot(settings)
    elif choice == "2":
        print("\n⚙️  Configuring Claude Code...")
        settings = setup_claude_code(settings)
    elif choice == "3":
        print("\n⚙️  Configuring Cursor...")
        settings = setup_cursor(settings)
    elif choice == "4":
        print("\n⚙️  Configuring all editors...")
        settings = setup_github_copilot(settings)
        settings = setup_claude_code(settings)
        settings = setup_cursor(settings)
    else:
        print("❌ Invalid choice")
        return 1
    
    # Write back settings
    if write_settings(settings_path, settings):
        print("✓ Settings updated!")
        print()
        print("📝 Next steps:")
        print("1. Restart VSCode completely")
        print("2. Open your Python project")
        print("3. Ask your LLM to profile your code")
        print()
        print("For detailed instructions, see SETUP_VSCODE.md")
        return 0
    else:
        print("❌ Failed to write settings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
