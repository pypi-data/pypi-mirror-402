# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-21

### Added
- Initial release of TCBS Python SDK
- Authentication with API key and OTP
- Automatic JWT token management with 8-hour caching
- Stock trading operations (place, update, cancel orders)
- Derivative trading support
- Market data retrieval
- Account information and purchasing power queries
- Comprehensive error handling with custom exceptions
- Bilingual documentation (English and Vietnamese)
- Security warnings and best practices

### Features
- **Authentication**: Automatic token refresh and secure storage
- **Stock Trading**: Full order management (place, update, cancel, query)
- **Derivatives**: Support for derivative trading operations
- **Market Data**: Real-time market information and price history
- **Account Management**: Profile, assets, purchasing power, margin quota

### Security
- Token stored with restricted permissions (0600)
- Environment variable support for API keys
- Comprehensive security warnings in documentation

## [Unreleased]

### Planned
- Async/await support
- WebSocket streaming for real-time data
- Additional market data endpoints
- Enhanced error messages
- More comprehensive examples
