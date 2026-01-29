# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-17

### Added
- **Tool Consolidation**: Reduced from 16 tools to 7 core tools for better LLM reasoning
  - `profile()` - Unified script and code profiling
  - `analyze()` - Mega-tool supporting 9 different analysis metric types
  - `get_project_root()` - Auto-detect project structure
  - `list_project_files()` - File discovery
  - `set_project_context()` - Manual context override
  - `compare_profiles()` - Profile comparison
  - `list_profiles()` - Session tracking
- **Backward Compatibility**: 11 deprecated wrapper functions for existing code
  - `profile_script()`, `profile_code()` → `profile(type=...)`
  - `analyze_profile()`, `get_cpu_hotspots()`, `get_memory_hotspots()`, `get_gpu_hotspots()`, `get_bottlenecks()`, `get_memory_leaks()`, `get_file_details()`, `get_function_summary()`, `get_recommendations()` → `analyze(metric_type=...)`
- **Editor-Specific Setup Guides**
  - SETUP_CLAUDE.md - Claude Code integration guide
  - SETUP_GITHUB_COPILOT.md - GitHub Copilot integration guide  
  - SETUP_CURSOR.md - Cursor editor integration guide
- **Comprehensive Documentation**
  - TOOLS_REFERENCE.md - Detailed tool descriptions with examples
  - QUICKSTART.md - Getting started guide
  - Architecture overview in fastmcp-overview.md and scalene-overview.md
- **CI/CD Integration**
  - GitHub Actions workflows for testing
  - Automated pytest runs with coverage reports
  - Support for Python 3.10, 3.11, 3.12, 3.13
  - Codecov integration for coverage tracking
- **Full Test Coverage**
  - 225 tests covering all functionality
  - 88% code coverage
  - Tests for backward-compatibility layer

### Changed
- Refactored server.py from 570 lines to 450 lines (21% reduction)
- Improved response structure consistency across all tools
- Enhanced error messages with actionable information
- Better LLM-optimized output formatting

### Technical Details
- All tests passing: 225/225 ✅
- Server consolidation complete: 16 → 7 tools
- Backward compatibility fully maintained
- Python 3.10+ support with type hints

[0.1.0]: https://github.com/yourusername/scalene-mcp/releases/tag/v0.1.0
