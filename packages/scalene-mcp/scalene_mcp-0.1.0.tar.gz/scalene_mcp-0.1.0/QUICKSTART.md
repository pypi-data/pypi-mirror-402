# Quick Start Guide - Scalene MCP for VSCode

## In 3 Steps

### Step 1: Install
```bash
pip install scalene-mcp
```

### Step 2: Configure
Run the setup script:
```bash
python scripts/setup_vscode.py
```

Or manually add to `.vscode/settings.json`:

**GitHub Copilot:**
```json
{
  "github.copilot.chat.mcp.servers": {
    "scalene": {
      "command": "uv",
      "args": ["run", "-m", "scalene_mcp.server"]
    }
  }
}
```

**Claude Code:**
```json
{
  "mcpServers": {
    "scalene": {
      "command": "uv",
      "args": ["run", "-m", "scalene_mcp.server"]
    }
  }
}
```

**Cursor:**
```json
{
  "mcp": {
    "servers": {
      "scalene": {
        "command": "uv",
        "args": ["run", "-m", "scalene_mcp.server"]
      }
    }
  }
}
```

### Step 3: Restart VSCode
Close and reopen VSCode.

---

## Your First Profile

1. Open any Python project folder in VSCode
2. Open Copilot/Claude Code/Cursor chat
3. Ask:

```
"Profile my main.py and show me the bottlenecks"
```

**What happens next:**
- LLM auto-detects your project root
- Finds `main.py` in your project
- Profiles it with Scalene
- Shows you CPU, memory, and performance issues
- Suggests optimizations

---

## Available Tools

### Discovery (LLM uses automatically)
- `get_project_root()` - Finds your project
- `list_project_files()` - Lists Python files
- `set_project_context()` - Override if needed

### Profiling (Unified Tool)
- `profile(type="script", script_path="...", ...)` - Profile any Python script or code
  - Use `type="script"` for script files
  - Use `type="code"` for code snippets

### Analysis (Single Mega Tool with 9 Modes)
- `analyze(profile_id, metric_type="all")` - Comprehensive view
- `analyze(profile_id, metric_type="cpu")` - Find slow code
- `analyze(profile_id, metric_type="memory")` - Find memory hogs
- `analyze(profile_id, metric_type="gpu")` - Find GPU bottlenecks
- `analyze(profile_id, metric_type="bottlenecks")` - Lines exceeding thresholds
- `analyze(profile_id, metric_type="leaks")` - Detect memory leaks
- `analyze(profile_id, metric_type="file", filename="...")` - Line-by-line metrics
- `analyze(profile_id, metric_type="functions")` - Function-level view
- `analyze(profile_id, metric_type="recommendations")` - Optimization suggestions

### Comparison & Storage
- `compare_profiles(before_id, after_id)` - Compare before/after
- `list_profiles()` - List all profiles in session
- `list_profiles()` - See all profiles

---

## Example Conversations

### Find Performance Issues
```
You: "Why is my code slow?"

LLM: 
1. Profiles your main script
2. Finds hotspots using 50% CPU
3. Shows you the 5 slowest lines
4. Gives optimization suggestions
```

### Detect Memory Leaks
```
You: "Check my app for memory leaks"

LLM:
1. Profiles with memory tracking
2. Finds lines allocating unbounded memory
3. Shows likelihood scores
4. Suggests fixes (close files, clear caches, etc.)
```

### Validate Optimization
```
You: "I optimized my code. Prove it works."

LLM:
1. Profiles original version
2. Profiles optimized version
3. Compares: "25% faster, 15% less memory"
4. Shows which optimizations helped most
```

### Understand Your Project
```
You: "What's in this project?"

LLM:
1. Detects project root and type
2. Lists Python files
3. Shows project structure
4. Ready to profile anything you ask
```

---

## Paths "Just Work"

Forget about absolute paths. Just say:

```
"Profile main.py"
"Profile src/train.py"
"Profile tests/test_main.py"
"Profile ./data/process.py"
```

All resolved automatically relative to your project root!

---

## Troubleshooting

**MCP server not showing?**
- Restart VSCode completely
- Check `uv --version` is installed
- Verify JSON syntax in settings

**Can't find my file?**
- Ask: `"List Python files in my project"`
- Use the exact path returned

**Path resolution fails?**
- Ask: `"Set project context to /absolute/path/here"`
- Or check `.git` or `pyproject.toml` exist in project root

---

## Full Documentation

- **[SETUP_VSCODE.md](SETUP_VSCODE.md)** - Detailed setup guide
- **[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)** - Complete tool API
- **[README.md](README.md)** - Project overview

---

## Need Help?

1. Check **[SETUP_VSCODE.md](SETUP_VSCODE.md)** for troubleshooting
2. See **[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)** for tool details
3. Open an issue on GitHub

---

Happy profiling! 🚀
