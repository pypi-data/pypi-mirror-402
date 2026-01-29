# Scalene MCP Server - VSCode Setup Guide

This guide helps you integrate the Scalene MCP Server with your favorite LLM-powered code editor for seamless Python profiling.

## Table of Contents

- [Installation](#installation)
- [Editor-Specific Setup](#editor-specific-setup)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install scalene-mcp
```

Or with `uv`:

```bash
uv add scalene-mcp
```

### Option 2: Install from Source

```bash
git clone https://github.com/emeryberger/scalene-mcp.git
cd scalene-mcp
pip install -e .
```

## Editor-Specific Setup

Choose your editor below for exact configuration steps:

### GitHub Copilot in VSCode

1. **Open Settings**
   - File → Preferences → Settings (or `Ctrl+,` / `Cmd+,`)

2. **Find MCP Configuration**
   - Search for: `@ext:github.copilot mcp`
   - Or go to: Extensions → GitHub Copilot → Settings

3. **Add Scalene Server**
   
   In your VSCode `settings.json`, add:
   
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

   **Alternative** (if using `python` instead of `uv`):
   
   ```json
   {
     "github.copilot.chat.mcp.servers": {
       "scalene": {
         "command": "python",
         "args": ["-m", "scalene_mcp.server"]
       }
     }
   }
   ```

4. **Restart VSCode** to apply changes

5. **Enable in Copilot Chat**
   - Open Copilot Chat
   - Look for the model settings icon
   - Enable "Scalene" in the MCP servers list

---

### Claude Code (VSCode Extension)

1. **Install Claude Code Extension**
   - Command Palette: `Extensions: Install Extensions`
   - Search: `Anthropic Claude Code`
   - Click Install

2. **Configure MCP Server**
   - VSCode Settings → Extensions → Claude Code
   - Find: "MCP Servers" or "Model Context Protocol"
   - Add configuration:

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

3. **Restart VSCode**

---

### Cursor

1. **Update Cursor Settings**
   - File → Preferences → Settings
   - Open `settings.json` (bottom right, JSON icon)

2. **Add MCP Configuration**

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

3. **Restart Cursor**

---

## Usage

### Quick Start Example

Open any Python project in VSCode and ask your LLM:

```
"Can you profile my main.py and tell me where the bottlenecks are?"
```

The LLM will:
1. **Auto-detect** your project root (looks for `.git`, `pyproject.toml`, etc.)
2. **Find** your `main.py` file (resolves relative paths)
3. **Profile** it with Scalene
4. **Analyze** the results
5. **Report** findings and recommendations

### Available Commands

The Scalene server provides these tools:

#### Project Context Discovery

- **`get_project_root()`**
  - Returns the detected project root and type (Python/Node/Mixed)
  - Auto-called by the LLM to understand your project

- **`list_project_files(pattern, max_depth, exclude_patterns)`**
  - Lists files matching a glob pattern (e.g., `*.py`, `src/**.py`)
  - Helps the LLM find scripts to profile
  - Example: `list_project_files("*.py")` → finds all Python files

- **`set_project_context(project_root)`**
  - Explicitly set the project root (if auto-detection fails)
  - Example: `set_project_context("/home/user/myapp")`

#### Profiling (Unified Tool)

- **`profile(type, script_path=None, code=None, ...options)`**
  - Single tool for both scripts and code snippets
  - Use `type="script"` with `script_path` parameter
  - Use `type="code"` with `code` parameter
  - `script_path` can be relative (e.g., `"main.py"`) or absolute

#### Analysis (Mega Tool)

- **`analyze(profile_id, metric_type, ...options)`**
  - Single tool with 9 analysis modes:
  - `metric_type="all"` - Comprehensive analysis
  - `metric_type="cpu"` - CPU hotspots
  - `metric_type="memory"` - Memory hotspots
  - `metric_type="gpu"` - GPU usage
  - `metric_type="bottlenecks"` - Performance thresholds
  - `metric_type="leaks"` - Memory leak detection
  - `metric_type="file"` - File-level metrics
  - `metric_type="functions"` - Function-level metrics
  - `metric_type="recommendations"` - Optimization suggestions
  - Detects potential memory leaks

- **`compare_profiles(before_id, after_id)`**
  - Compares two profiles to measure optimization impact

- **`list_profiles()`**
  - Lists all profiles captured in this session

### Example Conversations

#### Example 1: Quick Profiling

**You:** "Profile my script and show me the hotspots"

**LLM does:**
- Calls `get_project_root()` → learns project is at `/home/user/myapp`
- Calls `list_project_files("*.py")` → finds `src/main.py`
- Calls `profile(type="script", script_path="src/main.py")` → profiles it
- Calls `analyze(profile_id, metric_type="cpu")` → finds CPU-intensive lines
- Shows you the results with context

#### Example 2: Debugging Performance Issues

**You:** "Why is my code slow? Find memory leaks."

**LLM does:**
- Auto-detects your project
- Profiles your main script
- Calls `analyze(profile_id, metric_type="leaks")` → finds issues
- Calls `analyze(profile_id, metric_type="recommendations")` → gets suggestions
- Explains what's wrong and how to fix it

#### Example 3: Optimization Validation

**You:** "I optimized my code. Did it actually get faster?"

**LLM does:**
- Profiles the original version → `profile_id_1`
- Profiles the optimized version → `profile_id_2`
- Calls `compare_profiles(profile_id_1, profile_id_2)`
- Shows metrics comparing CPU, memory, runtime improvements

---

## How Path Resolution Works

The server automatically handles paths intelligently:

### Relative Paths
```
profile(type="script", script_path="main.py")
profile(type="script", script_path="src/utils.py")
profile(type="script", script_path="tests/test_main.py")
```
→ Resolved relative to detected project root

### Absolute Paths
```
profile(type="script", script_path="/home/user/myapp/main.py")
```
→ Used as-is

### Auto-Detection
The server detects project root by looking for:
- `.git` (Git repository)
- `pyproject.toml` (Python project, modern)
- `setup.py` (Python project, classic)
- `package.json` (Node.js project)
- `Makefile` / `GNUmakefile` (Build system)
- Falls back to current working directory

---

## Troubleshooting

### MCP Server Not Showing Up

**Problem:** Copilot/Claude Code doesn't see the Scalene server

**Solutions:**
1. Verify installation: `python -m scalene_mcp.server --help`
2. Check settings.json for syntax errors (use JSON validator)
3. Restart VSCode completely (not just reload window)
4. Check if `uv` is installed: `uv --version`
5. Try using `python` instead of `uv` in the command

### "Project Root Not Found"

**Problem:** Server can't auto-detect project root

**Solution:** Help it by explicitly setting context:
- Ask the LLM: "My project root is `/home/user/myproject`"
- Or use the tool directly: `set_project_context("/home/user/myproject")`

### "Script Not Found"

**Problem:** Profile says file doesn't exist

**Solutions:**
1. Check file exists: Ask LLM to `list_project_files("*.py")`
2. Use correct relative path from project root
3. Use absolute path if relative fails
4. Verify no typos in filename

### "No GPU Detected"

**Problem:** `analyze(profile_id, metric_type="gpu")` returns empty results

**Solution:** This is expected if:
- You don't have NVIDIA GPU
- CUDA is not installed
- Code doesn't use GPU (PyTorch, TensorFlow, etc.)
- Profile wasn't run with `include_gpu=True`

---

## Advanced Configuration

### Custom MCP Server Path

If you installed Scalene in a virtual environment:

```json
{
  "github.copilot.chat.mcp.servers": {
    "scalene": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "scalene_mcp.server"]
    }
  }
}
```

### Environment Variables

Set these before starting VSCode to customize behavior:

```bash
export SCALENE_MCP_PROJECT_ROOT="/custom/project/path"
export SCALENE_REDUCE_PROFILE=1
export SCALENE_CPU_PERCENT_THRESHOLD=2.0
```

---

## Next Steps

1. **Install** the server: `pip install scalene-mcp`
2. **Configure** your editor (see section above)
3. **Restart** VSCode
4. **Open** a Python project
5. **Ask** your LLM to profile your code

Happy profiling! 🚀
