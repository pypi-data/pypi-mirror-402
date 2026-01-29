# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-31

### Breaking Changes

- **`message_id` parameter is now required** in both `get_recommendations_for_weave()` and `get_recommendations_for_weave_sync()`
  - Previously: `message_id` was auto-generated in async version and optional in sync version
  - Now: `message_id: str` (required parameter, must be provided by frontend)
  - Rationale: The message_id must be provided by the frontend to ensure proper tracking and consistency across client and server
  - Migration: Ensure all calls to these methods include a `message_id` parameter provided by the frontend

- **Format filtering**: Methods now only return recommendations with "weave" format
  - Previously: All recommendations were returned regardless of format
  - Now: If format is not "weave", method returns `{found: False, error: "Preferred format is not weave"}`
  - Rationale: Ensures weave-node SDK only handles weave format, allowing other format clients to handle their respective formats

- **HTTP timeout calculation**: Timeout is now calculated from `latency_budget_ms` when provided
  - Previously: Used `timeout_ms` parameter directly
  - Now: Calculates `max(latency_budget_ms * 3, 30000)` (3x latency budget or 30s minimum)
  - Rationale: Ensures HTTP request doesn't timeout before the auction completes

### Added

- `context_id` generation in UCP payload structure (`ctx_{timestamp}_{random}`)
- `conversation_id` field in `extensions.aip` (uses `session_id` as value)
- Format filtering to only return "weave" format recommendations
- `creative_input` normalization with `offer_summary` preservation
- `realtime_offer_id` preservation at top level of recommendation object
- `offer_summary` field added to `CreativeInput` type definition

### Changed

- `platform_surface` default changed from `"conversation"` to `"web"` (matches Node.js SDK)
- `confidence` in `identity` object now always `1.0` (removed conditional based on `user_id`)
- Payload structure updated to include `context_id` in `context` object
- Type definitions: `AdMeshSubscriptionOptions` now requires `message_id` field
- Updated all examples and documentation to reflect required `message_id` parameter
- Improved docstrings to clarify that `message_id` and `session_id` must be provided by frontend

### Fixed

- Aligned Python SDK with latest Node.js SDK implementation for consistency

## [0.2.0] - 2025-01-31

### Breaking Changes

- **`query` parameter is now required** in both `get_recommendations_for_weave()` and `get_recommendations_for_weave_sync()`
  - Previously: `query: Optional[str] = None`
  - Now: `query: str` (required parameter)
  - Rationale: The query parameter is essential for generating contextual recommendations and should always be provided
  - Migration: Ensure all calls to these methods include a non-empty `query` parameter

### Added

- Runtime validation for `query` parameter - throws `ValueError` if query is not provided or is empty
- Better error messages when query validation fails

### Changed

- Updated type definitions: `AdMeshSubscriptionOptions` now requires `query` field
- Updated all documentation and examples to reflect required `query` parameter
- Improved docstrings to clarify that `query` is required for contextual recommendations

## [0.1.1] - 2025-01-31

### Changed

- **Updated README.md for public distribution**
  - Added professional badges (PyPI version, Python versions, MIT license)
  - Added comprehensive "Getting Started" section with clear onboarding steps
  - Added "Security Best Practices" section with API key protection guidelines
  - Added "Support" section with links to GitHub Issues and Discussions
  - Added "Contributing" section with PR workflow and guidelines
  - Added FAQ section answering common questions
  - Removed internal implementation details (database specifics, internal endpoints)
  - Sanitized architecture descriptions to focus on user benefits
  - Improved professional tone throughout documentation
  - Added multiple installation methods (pip and poetry)
  - Added secrets manager integration examples

- **Updated package description** in pyproject.toml for better clarity

### Documentation

- Enhanced README with 653 lines of comprehensive, public-facing documentation
- Added security best practices for API key management
- Added community support channels and contribution guidelines
- Improved troubleshooting section with user-friendly language
- Added links to all relevant resources (GitHub, PyPI, AdMesh website)

## [0.1.0] - 2025-01-30

### Added

- Initial release of admesh-weave-python SDK
- `AdMeshClient` class for consuming recommendations from AdMesh Protocol
- `get_recommendations_for_weave()` async method for fetching recommendations
- `get_recommendations_for_weave_sync()` synchronous method for fetching recommendations
- Database-backed caching architecture (no Pub/Sub, no SSE)
- Direct HTTP POST to `/agent/recommend` endpoint
- Comprehensive type hints using TypedDict
- Full type safety with py.typed marker
- Support for Python 3.8+
- Comprehensive documentation and examples
- Basic usage examples demonstrating async and sync patterns
- Cache behavior demonstration example

### Features

- Lightweight backend SDK for Python (3.8+)
- Direct integration with admesh-protocol `/agent/recommend` endpoint
- Configurable timeout with default 12-second timeout
- Support for session ID and message ID tracking
- Query-based recommendation retrieval
- Exposure and click tracking URLs included
- Intent match and contextual relevance scoring
- Minimal dependencies (httpx, typing-extensions)
- Production-ready error handling
- Type-safe API with full type hints

### Dependencies

- httpx >= 0.23.0, < 1
- typing-extensions >= 4.5.0, < 5

### Dev Dependencies

- pytest >= 7.0.0
- pytest-asyncio >= 0.21.0
- ruff >= 0.1.0
- mypy >= 1.0.0
- black >= 23.0.0

### Architecture

- Simple request/response pattern
- Intelligent server-side caching for optimal performance
- Fast response times (< 100ms for cached recommendations)
- Simple integration with minimal setup

### Documentation

- Comprehensive README.md with installation, usage, and API reference
- Type definitions for all public APIs
- Example code demonstrating common usage patterns
- Troubleshooting guide for common issues
- Performance characteristics and benchmarks

### Notes

This is the Python equivalent of the `@admesh/weave-node` (v0.2.9) package for Node.js,
providing the same core functionality with Python-idiomatic naming conventions and patterns.

Key differences from Node.js version:
- Uses `snake_case` instead of `camelCase` for method names
- Provides both async and sync methods
- Uses TypedDict for type definitions instead of TypeScript interfaces
- Uses httpx instead of fetch API
- Follows Python packaging conventions (pyproject.toml, src layout)

[0.2.0]: https://github.com/GouniManikumar12/admesh-weave-python/releases/tag/v0.2.0
[0.1.1]: https://github.com/GouniManikumar12/admesh-weave-python/releases/tag/v0.1.1
[0.1.0]: https://github.com/GouniManikumar12/admesh-weave-python/releases/tag/v0.1.0

