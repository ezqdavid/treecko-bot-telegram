# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## 📋 Improvement Roadmap for Future Agents

> **Instructions for AI Agents**: When working on this repository, always review this section and propose improvements here. Add new improvement proposals under the appropriate priority section before implementing changes. Update the status of items as you work on them.

### Evaluation Summary (as of November 2024)

**Repository Status**: ✅ Healthy (136/136 tests passing)

| Area | Status | Notes |
|------|--------|-------|
| Core Functionality | ✅ Complete | Bot, database, PDF parsing, Sheets integration |
| Test Coverage | ✅ Good | All modules have unit tests |
| Code Quality | ✅ Linting | Ruff configured and passing |
| CI/CD | ✅ Configured | GitHub Actions for lint + test |
| Documentation | ✅ Good | README is comprehensive |
| Type Hints | ✅ Complete | All modules have type hints |
| Error Handling | ⚠️ Basic | Could be more robust |
| Input Validation | ✅ Added | PDF size and content validation |
| Config Validation | ✅ Added | URL, port, token format validation |
| Health Check | ✅ Added | /health endpoint for monitoring |
| Logging | ✅ Enhanced | Structured logging with configurable levels |
| Rate Limiting | ✅ Added | Configurable request rate limiting |
| Authorization | ✅ Added | Whitelist and admin-only modes |
| Async Database | ✅ Added | AsyncDatabaseManager for non-blocking ops |

---

### 🔴 High Priority Improvements

| ID | Improvement | Description | Status |
|----|-------------|-------------|--------|
| H1 | Add CI/CD Pipeline | Create GitHub Actions workflow for testing on PRs and pushes | ✅ Completed |
| H2 | Add Linting | Configure ruff or flake8 for code quality checks | ✅ Completed |
| H3 | Test Coverage for bot.py | Add unit tests for TreeckoBot class handlers | ✅ Completed |
| H4 | Test Coverage for sheets.py | Add unit tests for GoogleSheetsManager (with mocking) | ✅ Completed |
| H5 | Input Validation | Add validation for PDF file size and content security | ✅ Completed |

### 🟡 Medium Priority Improvements

| ID | Improvement | Description | Status |
|----|-------------|-------------|--------|
| M1 | Type Annotations | Complete type hints across all modules | ✅ Completed |
| M2 | Async Database Operations | Use async SQLAlchemy for better performance | ✅ Completed |
| M3 | Rate Limiting | Add rate limiting to prevent abuse | ✅ Completed |
| M4 | User Authorization | Add whitelist or admin-only mode | ✅ Completed |
| M5 | Logging Improvements | Add structured logging with different levels | ✅ Completed |
| M6 | Configuration Validation | Validate config values (URL format, port range, etc.) | ✅ Completed |

### 🟢 Low Priority Improvements

| ID | Improvement | Description | Status |
|----|-------------|-------------|--------|
| L1 | Documentation | Add docstrings to all public methods | 🔲 Proposed |
| L2 | Contributing Guide | Create CONTRIBUTING.md | 🔲 Proposed |
| L3 | Transaction Reports | Add /report command for summaries | 🔲 Proposed |
| L4 | Export Functionality | Add /export command to download CSV | 🔲 Proposed |
| L5 | Multi-language Support | Support for English in addition to Spanish | 🔲 Proposed |
| L6 | Category Management | Allow users to define custom categories | 🔲 Proposed |
| L7 | Health Check Endpoint | Add /health endpoint for monitoring | ✅ Completed |

### 📝 Improvement Proposal Template

When proposing new improvements, use this format:

```markdown
| ID | Improvement | Description | Status |
|----|-------------|-------------|--------|
| XX | [Short Title] | [Brief description of the improvement] | 🔲 Proposed |
```

**Status Legend**:
- 🔲 Proposed - Not yet started
- 🔄 In Progress - Currently being implemented
- ✅ Completed - Implemented and tested
- ❌ Rejected - Not suitable or deprecated

---

## [Unreleased]

### Added
- Initial CHANGELOG.md with improvement roadmap for future agents
- GitHub Actions CI workflow for linting and testing on PRs and pushes (.github/workflows/ci.yml)
- Ruff linting configuration in pyproject.toml
- Unit tests for TreeckoBot class handlers (tests/test_bot.py)
- Unit tests for GoogleSheetsManager with mocking (tests/test_sheets.py)
- PDF file size validation (max 10 MB limit)
- PDF content validation (magic bytes check for valid PDF files)
- pytest-asyncio dev dependency for async tests
- Configuration validation for:
  - Telegram bot token format validation
  - Webhook URL format and scheme validation
  - Port range validation (1-65535)
  - Database path extension validation (.db, .sqlite, .sqlite3)
- Health check HTTP endpoint (/health) for container monitoring
  - Configurable via HEALTH_CHECK_PORT environment variable (default: 8081)
  - Returns JSON with database and sheets configuration status
  - Runs as a separate background server thread
- Structured logging with configurable levels and formats
  - LOG_LEVEL environment variable (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - LOG_FORMAT environment variable (text, json)
  - JSON formatter for structured log analysis
  - Enhanced text formatter with extra context fields
- Async database operations (AsyncDatabaseManager) using aiosqlite
  - Non-blocking database operations for use in async contexts
  - Same API as synchronous DatabaseManager
  - Added aiosqlite dependency
- Rate limiting functionality to prevent abuse
  - Configurable via RATE_LIMIT_ENABLED, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
  - Default: 10 requests per 60 seconds
  - Sliding window algorithm for accurate rate tracking
- User authorization with multiple modes
  - AUTH_MODE: open (default), whitelist, admin_only
  - AUTH_ADMIN_IDS: Comma-separated list of admin user IDs
  - AUTH_WHITELIST_IDS: Comma-separated list of whitelisted user IDs
  - Admin users bypass whitelist restrictions
- Comprehensive type hints across all modules

### Changed
- Updated code to pass ruff linting (modernized type hints, fixed imports, formatting)
- Improved code quality with consistent style across all modules
- Enhanced main.py to use structured logging
- Bot handlers now check authorization and rate limiting before processing requests

---

## [0.1.0] - TBD

### Added
- Initial release of Treecko Finance Bot
- Telegram bot with /start, /help, /status commands
- MercadoPago PDF receipt parsing
- SQLite database for transaction storage
- Google Sheets integration for reporting
- Webhook mode support for Google Cloud Run deployment
- Polling mode support for local development
- Docker support with Python 3.12
- Environment-based configuration

### Technical Details
- Built with python-telegram-bot (v21.6 or later)
- Uses pdfplumber for PDF text extraction
- SQLAlchemy ORM for database operations
- gspread for Google Sheets API integration

---

## Guidelines for Future Contributors

### For AI Agents

1. **Before making changes**: Review the "Improvement Roadmap" section above
2. **When identifying new improvements**: Add them to the appropriate priority section
3. **When implementing an improvement**: 
   - Update the status to "🔄 In Progress"
   - After completion, update to "✅ Completed" and add entry under [Unreleased]
4. **Keep changelog entries concise**: Focus on what changed, not how

### For Human Contributors

- Follow [Keep a Changelog](https://keepachangelog.com/) format
- Use present tense for unreleased changes
- Use past tense for released changes
- Group changes by type: Added, Changed, Deprecated, Removed, Fixed, Security
