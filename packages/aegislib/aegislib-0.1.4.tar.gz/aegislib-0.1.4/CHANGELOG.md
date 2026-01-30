# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Approval Workflow System**: Background polling and execution for approval-required decisions
  - `ApprovalExecutor` for managing background approval polling with exponential backoff
  - `ApprovalTask` and `ApprovalTaskQueue` for thread-safe task management
  - Automatic task lifecycle management with status tracking (pending, approved, denied, completed, failed, timeout)
  - Configurable polling parameters (initial delay, max delay, max attempts, jitter)
- **Task Management System**: Comprehensive task tracking and querying capabilities
  - `TaskManager` for internal task lifecycle management
  - `TaskInfo` model with detailed task metadata and status
  - Global task manager instance with filtering and statistics
  - Task cleanup utilities for completed/failed tasks
- **Enhanced Configuration**: Extended `AegisConfig` with approval workflow settings
  - `approval_polling_enabled`: Enable/disable background approval polling
  - `approval_polling_initial_delay_s`: Initial polling delay
  - `approval_polling_max_delay_s`: Maximum polling delay
  - `approval_polling_max_attempts`: Maximum polling attempts before timeout
  - `approval_polling_jitter_ratio`: Random jitter for exponential backoff
  - Environment variable support for all new configuration options
- **Enhanced Guard Decorator**: Extended `@aegis_guard` with approval workflow support
  - `approval_callback` parameter for handling approval completion
  - Automatic background polling for approval-required decisions
  - Global executor management functions (`get_global_executor`, `set_global_executor`, `shutdown_global_executor`)
- **New Type Definitions**: Additional types for approval workflows
  - `ApprovalTaskCallback` type for approval completion callbacks
  - `DecisionStatusResponse` for polling API responses
  - Enhanced `Decision` and `DecisionResponse` models with approval support
- **Developer Integration Features**: Tools for building approval-aware applications
  - Global task manager access (`get_global_task_manager`, `reset_global_task_manager`)
  - Task querying and monitoring APIs
  - Production-ready examples with FastAPI and LangChain integration

### Security
- Enhanced security for approval workflows with proper error handling and timeouts
- Thread-safe task management to prevent race conditions

## [0.1.4] - 2025-11-06

### Added
- Initial release of Aegis Python SDK
- Core `@aegis_guard` decorator for tool protection
- `AegisConfig` for SDK configuration with environment variable support
- `DecisionClient` for interacting with Aegis Data Plane
- Full support for allow/deny/sanitize/approval_needed decisions
- Async/await compatibility for async functions
- Built-in retry logic and resilience features
- Type hints and py.typed marker for type checking
- Comprehensive error handling with custom exception hierarchy
- Debug logging and console output utilities
- Complete unit test suite with 100% code coverage
- CI/CD workflows for automated testing and publishing
- Production-ready packaging for PyPI distribution

### Security
- Secure API key handling with Pydantic SecretStr
- Safe model dumping with masked sensitive fields

[Unreleased]: https://github.com/mrsidrdx/aegis-python-sdk/compare/v0.1.4...HEAD
[0.1.1]: https://github.com/mrsidrdx/aegis-python-sdk/releases/tag/v0.1.1
[0.1.3]: https://github.com/mrsidrdx/aegis-python-sdk/releases/tag/v0.1.3
[0.1.4]: https://github.com/mrsidrdx/aegis-python-sdk/releases/tag/v0.1.4
