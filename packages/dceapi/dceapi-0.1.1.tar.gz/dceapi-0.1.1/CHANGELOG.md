# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-15

### Added
- Initial release of dceapi-py
- Client implementation with automatic token management
- Configuration management (from env or direct)
- Complete error handling with custom exceptions
- Common Service: get current trade date, get variety list
- News Service: get article list, get article detail
- Market Service: get day/night/week/month quotes, get contract statistics
- Trade, Settle, Member, Delivery services (placeholder)
- Type hints for all public APIs
- Comprehensive examples (basic and complete)
- Full documentation (README, DEVELOPMENT guide)
- Unit tests for core functionality

### Features
- Type-safe API access with Python type hints
- Automatic token management and refresh
- Complete error handling with custom exception types
- Support for futures and options trading types
- Support for Chinese and English languages
- Thread-safe token management
- Request retry on token expiration
- Configurable timeout and base URL

## [Unreleased]

### Planned
- Async/await support for async operations
- More comprehensive test coverage
- API rate limiting handling
- Request/response logging
- Caching support
- WebSocket support (if API supports)
- CLI tool for quick API access
