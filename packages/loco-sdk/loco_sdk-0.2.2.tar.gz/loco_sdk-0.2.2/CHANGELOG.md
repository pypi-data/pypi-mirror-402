# Changelog

All notable changes to the Loco SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-14

### Added

- Initial release
- NodePlugin base class for workflow nodes
- PluginBase abstract class
- ExtensionPlugin and TriggerPlugin base classes
- AuthContext helper for OAuth2, API key, and basic auth
- Exception hierarchy (PluginError, AuthenticationError, etc.)
- Comprehensive test suite with pytest
- Development tools: black, ruff, mypy
- uv support for dependency management
- DEVELOPMENT.md guide

### Changed

- N/A (initial release)

### Deprecated

- N/A

### Removed

- N/A

### Fixed

- N/A

### Security

- N/A

## [Unreleased]

### Planned

- Pydantic schemas for manifest validation
- Manifest loader utilities
- OAuth provider configurations
- Backwards invocation client (call Loco services from plugins)
- File operation helpers
- HTTP client with retry logic
- More authentication methods
