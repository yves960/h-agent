# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-03-21

### Added
- **Singleton OpenAI Client** (`h_agent/core/client.py`): Centralized `@lru_cache` singleton client, all modules share one connection pool
- **Shared Agent Loop** (`h_agent/core/loop.py`): Extracted common `run_agent_loop()` function, eliminated code duplication

### Changed
- **Lazy Loading**: Plugins and extended tools now load on first use instead of at module import time, significantly improving startup speed
- **Config Lazy Loading**: Configuration files now load on first `get_config()` call, reducing unnecessary file I/O
- **Parallel Tool Execution**: Read-only tools (read, glob, git_status, docker_ps, etc. 12 total) now use `ThreadPoolExecutor` for parallel execution, reducing latency from sum(times) to max(times)
- **Dotenv Deduplication**: Removed duplicate `load_dotenv()` calls, unified to single call in `client.py`

### Fixed
- **Session File Locking**: Added cross-platform file locking (Unix `fcntl.flock` / Windows `msvcrt.locking`) to prevent data corruption from multi-process concurrent access to JSONL files

### Performance Improvements
| Optimization | Effect |
|--------------|--------|
| Singleton client | Memory usage reduced by ~50%, unified connection pool |
| Lazy loading | Startup time reduced by 200-500ms |
| Parallel tool execution | Multi-tool call latency reduced |
| Session file locking | Concurrent safety |

## [0.2.0] - 2024-03-20

### Added
- **Test Coverage**: Added comprehensive test suite using pytest with tests for:
  - `SessionManager` (CRUD, tags, groups, search, rename)
  - `ContextGuard` (token estimation, truncation, compaction)
  - `SessionStore` (JSONL persistence)
  - File operation tools (`file_read`, `file_write`, `file_edit`, `file_glob`, `file_exists`, `file_info`)
  - Shell tools (`shell_run`, `shell_env`, `shell_cd`, `shell_which`)
  - JSON utility tools (`json_parse`, `json_format`, `json_query`, `json_validate`)
  - Platform utilities (`which`, `shell_quote`, path utilities, process management)
  - Plugin system
  - Core agent imports
- **CI/CD**: GitHub Actions workflows for:
  - Automated testing on Ubuntu, macOS, Windows with Python 3.10, 3.11, 3.12
  - Automated PyPI release on version tags
- **Type Hints**: Added type annotations throughout the codebase
- **Code Formatting**: Configured `black` and `isort` for code formatting

### Changed
- **Version**: Updated from 0.1.0 to 0.2.0
- **Test Framework**: Migrated from ad-hoc tests to pytest with proper fixtures

## [0.1.0] - 2024-03-19

### Added
- Core agent loop with OpenAI API support
- Tool system (bash, read, write, edit, glob)
- Session management with JSONL persistence
- Context guard with overflow protection
- Multi-channel support
- RAG for codebase understanding
- Plugin system
- CLI with session, config, and daemon management
- Cross-platform support (Linux, macOS, Windows)
