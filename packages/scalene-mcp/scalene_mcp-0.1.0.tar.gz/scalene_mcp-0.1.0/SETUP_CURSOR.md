# Scalene MCP Setup for Cursor

Complete guide to integrating Scalene MCP with Cursor, the all-in-one AI IDE.

## What is Cursor?

[Cursor](https://www.cursor.com/) is a modern code editor built on VSCode with integrated AI capabilities from Claude or GPT-4. It comes with first-class MCP support, making it ideal for Scalene MCP integration.

## Prerequisites

- **Cursor** (latest version) - Download from [cursor.com](https://www.cursor.com/)
- **Python 3.10+**
- **Scalene MCP package** (this project)
- Claude API key (if using Claude) or OpenAI API key (if using GPT-4)

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

### Step 2: Configure Cursor

Open your Cursor settings. You have two options:

**Option A: Using the Setup Script (Recommended)**

```bash
python scripts/setup_vscode.py
```

The script auto-detects your setup and configures Cursor for you.

**Option B: Manual Configuration**

In Cursor, open **Settings** → **Features** → **MCP** and add:

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

Or if using pip install (not uv):

```json
{
  "mcp": {
    "servers": {
      "scalene": {
        "command": "python",
        "args": ["-m", "scalene_mcp.server"]
      }
    }
  }
}
```

### Step 3: Restart Cursor

Close and reopen Cursor completely. Scalene MCP server will initialize on startup.

## Using Scalene MCP with Cursor

### Opening Cursor Chat

1. Open any Python project folder in Cursor
2. Press `Ctrl+K` (Windows/Linux) or `Cmd+K` (Mac) to open chat
3. Or click the Chat icon in the left sidebar

### Example: Profile and Analyze Code

**You:** "Profile my main.py and show me the bottlenecks"

**Cursor does automatically:**
- Detects your project root
- Finds `main.py` in your project
- Profiles it with Scalene
- Shows CPU/memory hotspots
- Suggests optimizations

**Cursor's response includes:**
- Profile summary (runtime, peak memory, CPU time)
- Hotspots (lines using most CPU/memory)
- Bottleneck analysis
- Concrete optimization suggestions

### Available Tools (What Cursor Can Use)

Cursor has access to 7 Scalene MCP tools:

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

## Cursor-Specific Features

### Cursor Tab (Chat Mode)

Press `Ctrl+K` to open the Cursor Tab, which combines chat and code editing:

```
You ask: "Profile main.py"
↓
Cursor shows analysis in chat
↓
Cursor suggests optimizations
↓
Click to apply suggestions directly in editor
```

### Agent Mode

Cursor can run in "Agent" mode where it can:
- Profile your code automatically
- Suggest optimizations
- Apply changes
- Validate with re-profiling

Enable in Settings → Agent Mode.

### Composer (Enhanced Editing)

Use Composer Mode for complex changes:

```
You: "Optimize the data processing pipeline"
↓
Cursor: Opens Composer with full file view
↓
Cursor: Shows optimized version side-by-side
↓
You: Review and accept changes
↓
You: "Profile again to validate"
↓
Cursor: Shows performance improvement
```

### Multi-file Selection

Ask Cursor to profile multiple files:

```
"Profile everything in src/ and show me which files are slowest"
```

Cursor can analyze multiple files at once.

## Example Conversations

### Example 1: Quick Performance Check

**You:** "What's the performance profile of src/main.py?"

**Cursor:**
```
1. Detects your project at /home/user/myapp
2. Profiles src/main.py
3. Returns:
   - Total runtime: 2.45 seconds
   - Peak memory: 142.3 MB
   - CPU hotspots in compute.py (lines 45, 78)
   - Memory hotspots in data_loader.py (line 23)
```

### Example 2: Find and Fix Memory Leaks

**You:** "Find and fix memory leaks in my application"

**Cursor:**
```
1. Profiles your main script
2. Analyzes with metric_type="leaks"
3. Opens Composer showing:
   - Problematic code patterns
   - Suggested fixes
4. You click "Apply Changes"
5. Cursor profiles again to validate
```

### Example 3: Optimize with Instant Feedback

**You:** "The calculate_stats() function is slow. Show me how to fix it."

**Cursor:**
```
1. Profiles your script
2. Analyzes with metric_type="bottlenecks"
3. Opens Composer showing:
   - Current slow implementation
   - Optimized version side-by-side
4. Click "Apply" to replace
5. Cursor profiles updated code
6. Shows % improvement: 45% faster
```

### Example 4: Bulk Optimization

**You:** "Optimize everything that's slower than average"

**Cursor:**
```
1. Profiles entire codebase
2. Finds all functions above 5% CPU threshold
3. For each one:
   - Opens in Composer
   - Shows optimization options
   - You approve/reject each
4. Final profile shows total improvement
```

### Example 5: Investigate Performance Regression

**You:** "Something got slower. Find what changed."

**Cursor:**
```
1. Profiles current version
2. Compares with previous commit
3. Shows:
   - Which functions regressed
   - How much slower they are
   - Suggested fixes
4. Composer opens with problem areas highlighted
```

## How Path Resolution Works

Cursor and Scalene MCP work together to find your files automatically.

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

If auto-detection fails, you can tell Cursor explicitly:

```
"Set the project root to /home/user/myapp and profile main.py"
```

Cursor will use `set_project_context()` to override the detection.

## Profiling Options

When you ask Cursor to profile, you can specify options:

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

## Workflow Examples

### Workflow 1: Iterative Optimization

```
1. You: "Profile main.py and find the slowest functions"
2. Cursor: Profiles and ranks functions by CPU time
3. You: "Optimize the top 3"
4. Cursor: Opens Composer with optimizations
5. You: Click "Apply"
6. You: "Profile again"
7. Cursor: Shows 40% improvement
8. You: "Find remaining bottlenecks"
9. Repeat until satisfied
```

### Workflow 2: Before/After Validation

```
1. You: "Profile my optimization branch"
2. Cursor: Profiles current branch
3. You: "Compare with main branch"
4. Cursor: Checks out main, profiles, compares
5. Cursor: Shows detailed diff:
   - Functions that improved
   - Functions that regressed
   - Overall impact
```

### Workflow 3: Code Review with Performance

```
1. Colleague: Sends pull request
2. You: "Profile this PR"
3. Cursor: Profiles the PR code
4. You: "Compare with main branch"
5. Cursor: Shows performance impact
6. If regression: "Suggest fixes for performance"
7. Cursor: Opens Composer with improvements
8. You: Review and request changes
```

### Workflow 4: Continuous Optimization

```
1. Set recurring task: "Weekly profile check"
2. Cursor: Profiles your app
3. If performance degraded:
   - Cursor identifies what changed
   - Suggests fixes
   - Opens in Composer
4. You review and accept changes
5. Next week: Compare with previous week
```

## Troubleshooting

### Cursor Doesn't See Scalene

**Problem:** Chat shows "No tools available" or Scalene isn't listed

**Solutions:**
1. Verify MCP config in Cursor settings under **Features → MCP**
2. Restart Cursor completely
3. Check Scalene MCP is installed: `pip show scalene-mcp`
4. Try the setup script: `python scripts/setup_vscode.py`

### Profile Says File Not Found

**Problem:** "Profile script.py" → Error: file not found

**Solutions:**
1. Use relative path from project root: `src/script.py`
2. Ask Cursor: "List my Python files" (uses `list_project_files()`)
3. Use absolute path instead
4. Check file actually exists in your project

### No Project Root Detected

**Problem:** Cursor can't find your project

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

### Composer Not Opening

**Problem:** Changes suggested but Composer doesn't open

**Solutions:**
1. Check Cursor version is latest
2. Enable Composer in Settings if disabled
3. Try clicking the "Edit" button manually
4. Restart Cursor

### MCP Server Not Connecting

**Problem:** Settings → MCP shows connection error

**Solutions:**
1. Verify command works: `python -m scalene_mcp.server`
2. Check Python version: `python --version` (need 3.10+)
3. Try running manually in terminal to see error
4. Reinstall: `pip install --upgrade scalene-mcp`

## Best Practices for Cursor

### 1. Use Agent Mode for Complex Tasks

```
Enable Agent Mode for:
- Multi-step optimizations
- Validating changes automatically
- Continuous performance monitoring
```

### 2. Leverage Composer for Code Review

```
Use Composer when:
- Reviewing optimization suggestions
- Comparing old vs new code
- Making complex changes
```

### 3. Chain Commands Together

```
"Profile main.py, find bottlenecks, suggest optimizations,
open suggestions in Composer, validate after applying"
```

### 4. Use Multi-file Analysis

```
"Show me which files in src/ need the most optimization"
"Compare performance across all test files"
```

### 5. Validate Changes Automatically

```
"Apply optimizations and profile again to verify improvement"
```

Cursor can chain these together automatically.

## See Also

- [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) - Complete API reference
- [SETUP_VSCODE.md](SETUP_VSCODE.md) - General VSCode setup
- [SETUP_CLAUDE.md](SETUP_CLAUDE.md) - Claude Code setup
- [SETUP_GITHUB_COPILOT.md](SETUP_GITHUB_COPILOT.md) - GitHub Copilot setup
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Project overview

## Getting Help

If you run into issues:

1. Check the [Troubleshooting section](#troubleshooting) above
2. Review [SETUP_VSCODE.md](SETUP_VSCODE.md) for general VSCode/Cursor issues
3. Check [Cursor documentation](https://docs.cursor.com/)
4. Open an issue on GitHub with your configuration

## Why Cursor for Scalene?

| Feature | Cursor | VSCode + Copilot | VSCode + Claude Code |
|---------|--------|------------------|----------------------|
| Built-in AI | ✅ First-class | ✅ Extension | ✅ Extension |
| MCP Support | ✅ Native | ✅ Good | ✅ Good |
| Composer Mode | ✅ Yes | ❌ No | ❌ No |
| Agent Mode | ✅ Yes | ❌ No | ❌ No |
| Code Apply | ✅ One-click | Manual | Manual |
| Multi-file Edit | ✅ Yes | Limited | Limited |
| Price | One-time or subscription | Subscription | Subscription |

Cursor is purpose-built for AI-powered development, making it an excellent choice for Scalene MCP workflow.
