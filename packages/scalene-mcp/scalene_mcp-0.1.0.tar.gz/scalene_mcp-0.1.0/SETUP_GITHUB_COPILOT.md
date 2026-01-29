# Scalene MCP Setup for GitHub Copilot

Complete guide to integrating Scalene MCP with GitHub Copilot in VSCode.

## What is GitHub Copilot?

[GitHub Copilot](https://github.com/features/copilot) is GitHub's AI assistant for VSCode. With Copilot Chat and MCP support, you can ask Copilot to profile and analyze your Python code's performance using Scalene MCP.

## Prerequisites

- **VSCode** (latest version)
- **GitHub Copilot** extension installed
- **GitHub Copilot Chat** extension installed (enables chat interface)
- **Python 3.10+**
- **Scalene MCP package** (this project)
- Active GitHub Copilot subscription (chat feature)

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

### Step 2: Configure GitHub Copilot

Open your VSCode settings. You have two options:

**Option A: Using the Setup Script (Recommended)**

```bash
python scripts/setup_vscode.py
```

The script auto-detects your setup and configures Copilot for you.

**Option B: Manual Configuration**

Open `.vscode/settings.json` (create it if it doesn't exist):

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

Or if using pip install (not uv):

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

### Step 3: Restart VSCode

Close and reopen VSCode completely. GitHub Copilot will initialize the Scalene MCP server on startup.

## Using Scalene MCP with GitHub Copilot

### Opening Copilot Chat

1. Open any Python project folder in VSCode
2. Press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Shift+I` (Mac) to open Copilot Chat
3. Or click the Copilot icon in the sidebar

### Example: Profile and Analyze Code

**You:** "Profile my main.py and show me the bottlenecks"

**Copilot does automatically:**
- Detects your project root
- Finds `main.py` in your project
- Profiles it with Scalene
- Shows CPU/memory hotspots
- Suggests optimizations

**Copilot's response includes:**
- Profile summary (runtime, peak memory, CPU time)
- Hotspots (lines using most CPU/memory)
- Bottleneck analysis
- Concrete optimization suggestions

### Available Tools (What Copilot Can Use)

Copilot Chat has access to 7 Scalene MCP tools:

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

**Copilot:**
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

**Copilot:**
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

**Copilot:**
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

**Copilot:**
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

**Copilot:**
```
1. Profiles your code
2. Analyzes with metric_type="file", filename="src/processing.py"
3. Shows:
   - Every line with CPU/memory metrics
   - Which functions are slowest
   - Memory allocation patterns
```

## How Path Resolution Works

GitHub Copilot and Scalene MCP work together to find your files automatically.

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

If auto-detection fails, you can tell Copilot explicitly:

```
"Set the project root to /home/user/myapp and profile main.py"
```

Copilot will use `set_project_context()` to override the detection.

## Profiling Options

When you ask Copilot to profile, you can specify options:

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

## Copilot Chat Features

### Inline Chat

Press `Ctrl+I` in the editor to open inline Copilot Chat:

```python
# Select a function
def slow_function():
    ...

# Press Ctrl+I and ask:
# "Profile this function and suggest optimizations"
```

Copilot will analyze just that function.

### Chat History

Copilot remembers your conversation. You can:

1. Profile version 1
2. Make changes
3. Profile version 2
4. Say "Compare the two profiles"

Copilot keeps track of all profiles in the chat session.

### Code Block Context

Copilot can profile code you paste:

```
You: "Profile this code:
    for i in range(1000):
        x = expensive_operation(i)"

Copilot: Profiles the code snippet, shows results
```

## Troubleshooting

### Copilot Chat Doesn't See Scalene

**Problem:** Chat shows "No tools available" or Scalene isn't listed

**Solutions:**
1. Verify MCP config in `.vscode/settings.json` under `github.copilot.chat.mcp.servers`
2. Restart VSCode completely (not just the chat window)
3. Check Scalene MCP is installed: `pip show scalene-mcp`
4. Try the setup script: `python scripts/setup_vscode.py`

### Profile Says File Not Found

**Problem:** "Profile script.py" → Error: file not found

**Solutions:**
1. Use relative path from project root: `src/script.py`
2. Ask Copilot: "List my Python files" (uses `list_project_files()`)
3. Use absolute path instead
4. Check file actually exists in your project

### No Project Root Detected

**Problem:** Copilot can't find your project

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

### MCP Server Error in Output

**Problem:** Terminal/Output shows MCP server errors

**Solutions:**
1. Try running manually: `python -m scalene_mcp.server` to see full error
2. Verify Python version: `python --version` (need 3.10+)
3. Check Scalene works: `python -m scalene --help`
4. Try reinstalling: `pip install --upgrade scalene-mcp`

## Best Practices

### 1. Start with Full Analysis

```
"Profile main.py and show me everything"
```

Then drill down based on results.

### 2. Use the Profile History

```
"Profile the original version"
"Profile the optimized version"
"Compare the two profiles"
```

Copilot maintains profile IDs across the conversation.

### 3. Focus on One Metric

```
"Profile and focus on CPU hotspots"
```

Rather than asking for everything at once, drill down.

### 4. Ask for Concrete Suggestions

```
"What's the #1 optimization I should make?"
```

Copilot provides specific code changes, not vague advice.

### 5. Validate Changes

```
"Profile again to see if my optimization worked"
```

Use comparison to measure actual improvement.

## Complete Example Workflow

### Scenario: Optimizing a data pipeline

**Step 1: Initial Profile**
```
You: "Profile pipeline.py"
Copilot: Returns initial metrics
```

**Step 2: Identify Bottlenecks**
```
You: "What's the slowest part?"
Copilot: Uses analyze(metric_type="bottlenecks")
→ Shows data_loader is 45% of runtime
```

**Step 3: Get Optimization Suggestions**
```
You: "How should I optimize data_loader.py?"
Copilot: Suggests vectorization, caching, etc.
```

**Step 4: Validate**
```
You: "Profile again to see the improvement"
Copilot: Shows 30% speedup
```

**Step 5: Continue**
```
You: "Find the next bottleneck"
Copilot: Analyzes updated profile
→ Next target: preprocessing function
```

## See Also

- [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) - Complete API reference
- [SETUP_VSCODE.md](SETUP_VSCODE.md) - General VSCode setup
- [SETUP_CLAUDE.md](SETUP_CLAUDE.md) - Claude Code setup
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Project overview

## Getting Help

If you run into issues:

1. Check the [Troubleshooting section](#troubleshooting) above
2. Review [SETUP_VSCODE.md](SETUP_VSCODE.md) for general VSCode issues
3. Open an issue on GitHub with your configuration

## Key Differences from Manual CLI

| Task | Manual CLI | Copilot Chat |
|------|-----------|------------|
| Profile a script | `scalene script.py` | "Profile script.py" |
| Find CPU hotspots | Parse output manually | "What lines use the most CPU?" |
| Memory leak detection | `--memory-leak-detector` flag | "Find memory leaks" |
| Compare profiles | Manual diff | "Compare before and after" |
| Optimization suggestions | Manual analysis | "How can I optimize this?" |
| Code editing | Manual text editor | Copilot suggests, you click Accept |

With GitHub Copilot Chat, you just describe what you need. Copilot handles the Scalene integration and explains results in natural language.
