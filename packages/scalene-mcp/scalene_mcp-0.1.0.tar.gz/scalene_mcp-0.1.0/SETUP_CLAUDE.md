# Scalene MCP Setup for Claude Code

Complete guide to integrating Scalene MCP with Claude Code VSCode extension.

## What is Claude Code?

[Claude Code](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code) is the official Anthropic VSCode extension that brings Claude (the AI model) directly into your editor. With Scalene MCP integration, Claude can profile and analyze Python code performance directly in your project.

## Prerequisites

- **VSCode** (latest version)
- **Claude Code** extension installed
- **Python 3.10+**
- **Scalene MCP package** (this project)
- Anthropic API key with Claude Code enabled

## Installation

### Step 1: Install Scalene MCP

```bash
pip install scalene-mcp
```

Or from source:

```bash
git clone https://github.com/plasma-umass/scalene-mcp.git
cd scalene-mcp
uv sync
```

### Step 2: Configure Claude Code

Open your VSCode settings. You have two options:

**Option A: Using the Setup Script (Recommended)**

```bash
python scripts/setup_vscode.py
```

The script will auto-detect your setup and configure Claude Code for you.

**Option B: Manual Configuration**

Open `.vscode/settings.json` (create it if it doesn't exist):

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

Or if using pip install (not uv):

```json
{
  "mcpServers": {
    "scalene": {
      "command": "python",
      "args": ["-m", "scalene_mcp.server"]
    }
  }
}
```

### Step 3: Restart VSCode

Close and reopen VSCode completely. Claude Code will initialize the Scalene MCP server on startup.

## Using Scalene MCP with Claude Code

### Opening Claude Code Chat

1. Open any Python project folder in VSCode
2. Press `Ctrl+Shift+L` (Windows/Linux) or `Cmd+Shift+L` (Mac) to open Claude Code chat
3. Or click the Claude Code icon in the sidebar

### Example: Profile and Analyze Code

**You:** "Profile my main.py and show me the bottlenecks"

**Claude does automatically:**
- Detects your project root
- Finds `main.py` in your project
- Profiles it with Scalene
- Shows CPU/memory hotspots
- Suggests optimizations

**Claude's response includes:**
- Profile summary (runtime, peak memory, CPU time)
- Hotspots (lines using most CPU/memory)
- Bottleneck analysis
- Concrete optimization suggestions

### Available Tools (What Claude Can Use)

Claude Code has access to 7 Scalene MCP tools:

#### Discovery Tools
- `get_project_root()` - Auto-detect your project
- `list_project_files(pattern, max_depth)` - Find Python files
- `set_project_context(project_root)` - Override auto-detection

#### Profiling
- `profile(type="script"|"code", script_path|code, ...)` - Profile Python code

#### Analysis
- `analyze(profile_id, metric_type="all"|"cpu"|"memory"|"gpu"|"bottlenecks"|"leaks"|"file"|"functions"|"recommendations", ...)` - Analyze profiles

#### Comparison
- `compare_profiles(before_id, after_id)` - Compare two profiles
- `list_profiles()` - List all profiles in session

## Example Conversations

### Example 1: Quick Performance Check

**You:** "What's the performance profile of src/main.py?"

**Claude:**
```
1. Detects your project at /home/user/myapp
2. Profiles src/main.py
3. Returns:
   - Total runtime: 2.45 seconds
   - Peak memory: 142.3 MB
   - CPU hotspots in compute.py (lines 45, 78)
   - Memory hotspots in data_loader.py (line 23)
```

### Example 2: Find Memory Leaks

**You:** "Find memory leaks in my application"

**Claude:**
```
1. Profiles your main script
2. Analyzes with metric_type="leaks"
3. Reports:
   - Potentially leaking objects (with confidence scores)
   - Lines with growing memory allocations
   - Recommendations to fix each leak
```

### Example 3: Optimize a Specific Function

**You:** "The calculate_stats() function is slow. Profile it and suggest optimizations."

**Claude:**
```
1. Profiles your script
2. Analyzes with metric_type="bottlenecks"
3. Shows:
   - Which lines in calculate_stats() are slow
   - CPU time breakdown
   - Specific optimization suggestions
   - Example optimized code
```

### Example 4: Validate Optimization

**You:** "I optimized this function. Did it actually improve?"

**Claude:**
```
1. Profiles the current version
2. Compares with previous profile
3. Shows:
   - % improvement in runtime
   - % reduction in memory
   - Remaining bottlenecks
   - Next optimization opportunities
```

### Example 5: Deep Dive on Specific File

**You:** "Show me detailed line-by-line metrics for src/processing.py"

**Claude:**
```
1. Profiles your code
2. Analyzes with metric_type="file", filename="src/processing.py"
3. Shows:
   - Every line with CPU/memory metrics
   - Which functions are slowest
   - Memory allocation patterns
```

## How Path Resolution Works

Claude Code and Scalene MCP work together to find your files automatically.

### Auto-Detection

The server automatically detects your project root by looking for:
- `.git` (Git repository)
- `pyproject.toml` (Modern Python project)
- `setup.py` (Classic Python project)
- `package.json` (Node.js with Python)
- `Makefile` / `GNUmakefile` (Build system)
- Falls back to current working directory

### Relative Paths

You can use relative paths naturally:

```
"Profile src/main.py"
"Analyze benchmarks/benchmark.py"
"Check tests/test_performance.py"
```

These are automatically resolved relative to your project root.

### Absolute Paths

Absolute paths work too:

```
"Profile /home/user/myapp/src/main.py"
```

### Override Detection

If auto-detection fails, you can tell Claude explicitly:

```
"Set the project root to /home/user/myapp and profile main.py"
```

Claude will use `set_project_context()` to override the detection.

## Profiling Options

When you ask Claude to profile, you can specify options:

**Memory profiling:**
- "Profile with memory tracking" → Includes memory analysis
- "Memory-only profile" → Skips CPU profiling

**GPU profiling:**
- "Profile GPU usage" → Includes NVIDIA GPU analysis (if available)

**Reduced output:**
- "Quick profile" → Only shows high-activity lines

**File/path filtering:**
- "Profile only src/ directory"
- "Exclude tests from profile"

**Custom thresholds:**
- "Show lines using more than 10% CPU"
- "Report allocations over 50MB"

## Troubleshooting

### Claude Code Doesn't See Scalene

**Problem:** Claude Code chat shows an error that Scalene isn't available

**Solutions:**
1. Verify settings are in `.vscode/settings.json`
2. Restart VSCode completely (not just the chat)
3. Check Scalene MCP is installed: `pip show scalene-mcp`
4. Try running `python -m scalene_mcp.server` in terminal to debug

### Profile Says File Not Found

**Problem:** "Profile script.py" → Error: file not found

**Solutions:**
1. Use relative path from project root: `src/script.py`
2. Ask Claude: "List my Python files" (uses `list_project_files()`)
3. Use absolute path instead
4. Check file actually exists in your project

### No Project Root Detected

**Problem:** Claude can't find your project

**Solutions:**
1. Create a `.git` directory: `git init`
2. Or create `pyproject.toml` with: `[tool.scalene]`
3. Explicitly set: "Set project root to /absolute/path"
4. Check you have the folder open as workspace root

### GPU Hotspots Return Empty

**Problem:** `metric_type="gpu"` shows no results

**Expected if:**
- You don't have NVIDIA GPU
- CUDA isn't installed
- Code doesn't use GPU (PyTorch, TensorFlow)
- Profile wasn't run with GPU enabled

**Solution:** Use `metric_type="cpu"` or `metric_type="memory"` instead

### Timeout or Slow Profiling

**Problem:** Profiling takes a long time

**Solutions:**
- Reduce the script's runtime: "Profile with a smaller dataset"
- Use reduced profile: "Quick performance check"
- Profile specific functions: "Profile the main() function only"
- Check what's slow: "Analyze previous profile for bottlenecks"

## Best Practices

### 1. Start with Full Analysis

```
"Profile main.py and show me everything"
```

Then drill down based on results.

### 2. Compare Before/After

```
"Profile the original version"
"Profile the optimized version"
"Compare the two profiles"
```

Claude remembers profiles in the session.

### 3. Use File-Level Analysis for Large Codebases

```
"Profile my app and show metrics for src/compute.py"
```

Better than analyzing entire codebase at once.

### 4. Combine Metrics

```
"Profile with memory tracking, then find CPU bottlenecks, then check for leaks"
```

Claude chains analyses together.

### 5. Ask for Concrete Suggestions

```
"What's the #1 optimization I should make?"
```

Claude provides specific code changes, not vague advice.

## Advanced: Using Claude Code Composer

Claude Code's composer mode lets you edit code directly. You can:

1. Ask Claude to optimize slow code
2. Claude shows improvements
3. Click "Accept" to apply changes
4. Profile again to verify improvement

Example workflow:

```
You: "Make calculate_stats() faster"
↓
Claude: Shows optimized version in composer
↓
You: Click "Apply Changes"
↓
You: "Profile again to validate"
↓
Claude: Profiles updated code, shows improvement metrics
```

## Complete Example Workflow

### Scenario: Optimizing a data pipeline

**Step 1: Initial Profile**
```
You: "Profile pipeline.py"
Claude: Returns initial metrics
```

**Step 2: Identify Bottlenecks**
```
You: "What's the slowest part?"
Claude: Uses analyze(metric_type="bottlenecks")
→ Shows data_loader is 45% of runtime
```

**Step 3: Optimize**
```
You: "Optimize data_loader.py"
Claude: Suggests vectorization, caching, etc.
```

**Step 4: Apply & Validate**
```
You: "Profile again to validate"
Claude: Shows 30% speedup
```

**Step 5: Continue Improving**
```
You: "Find the next bottleneck"
Claude: Analyzes updated profile
→ Next target: preprocessing function
```

## See Also

- [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) - Complete API reference
- [SETUP_VSCODE.md](SETUP_VSCODE.md) - General VSCode setup
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Project overview

## Getting Help

If you run into issues:

1. Check the [Troubleshooting section](#troubleshooting) above
2. Review [SETUP_VSCODE.md](SETUP_VSCODE.md) for general issues
3. Open an issue on GitHub with your configuration

## Key Differences from Manual CLI

| Task | Manual CLI | Claude Code |
|------|-----------|------------|
| Profile a script | `scalene script.py` | "Profile script.py" |
| Find CPU hotspots | Parse output manually | "What lines use the most CPU?" |
| Memory leak detection | `--memory-leak-detector` flag | "Find memory leaks" |
| Compare profiles | Manual diff | "Compare before and after" |
| Optimization suggestions | Manual analysis | "How can I optimize this?" |

With Claude Code, you just describe what you want in natural language. Claude handles the tool orchestration, interpretation, and explanation.
