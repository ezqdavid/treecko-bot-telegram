# Copilot Coding Agent Instructions for Treecko Bot Telegram

## Repository Summary

**Treecko Finance Bot** is a personal finance Telegram bot that processes MercadoPago transaction receipts, stores them in SQLite, and syncs to Google Sheets. It's a Python 3.10+ project using `python-telegram-bot`, `pdfplumber`, `gspread`, and `sqlalchemy`.

- **Language**: Python 3.10+
- **Type**: Telegram Bot Application
- **Size**: Small (~600 lines of Python code, 6 modules)
- **Deployment Target**: Google Cloud Run with webhook mode, or local development with polling mode

---

## Build & Test Commands

### Installation (Required First)

```bash
# Always install dependencies first
pip install -r requirements.txt

# For development (enables running as module and console script)
pip install -e .

# For tests
pip install pytest
```

### Running Tests

```bash
# Run all tests (16 tests, ~0.5s)
python -m pytest tests/ -v
```

Tests do not require any environment variables or external services.

### Running the Application

The bot requires `TELEGRAM_BOT_TOKEN` environment variable. Without a token, it exits with an error.

```bash
# Option 1: Module execution (requires pip install -e .)
python -m treecko_bot.main

# Option 2: Console script (requires pip install -e .)
treecko-bot
```

**Expected error without token**: `Configuration error: TELEGRAM_BOT_TOKEN environment variable is required`

### Docker Build

```bash
docker build -t treecko-bot .
docker run --env-file .env treecko-bot
```

---

## Project Layout

```
treecko-bot-telegram/
├── src/treecko_bot/           # Main application package
│   ├── __init__.py            # Package init, version
│   ├── main.py                # Entry point (main function)
│   ├── config.py              # Config dataclass, loads from env vars
│   ├── bot.py                 # Telegram bot handlers (TreeckoBot class)
│   ├── database.py            # SQLAlchemy models, DatabaseManager class
│   ├── pdf_parser.py          # MercadoPagoPDFParser for PDF parsing
│   └── sheets.py              # Google Sheets integration
├── tests/                     # Pytest tests
│   ├── __init__.py
│   ├── test_config.py         # Config loading tests
│   ├── test_database.py       # Database operation tests
│   └── test_pdf_parser.py     # PDF parsing tests
├── pyproject.toml             # Project config, pytest settings
├── requirements.txt           # Pinned dependencies
├── Dockerfile                 # Production container (python:3.12-slim)
├── .env.example               # Template for environment variables
├── CHANGELOG.md               # Changelog and improvement roadmap for agents
└── README.md                  # User documentation
```

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, pytest config, entry points |
| `requirements.txt` | Pinned production dependencies |
| `src/treecko_bot/main.py` | Application entry point |
| `src/treecko_bot/config.py` | Environment variable loading |
| `src/treecko_bot/bot.py` | Core bot logic (TreeckoBot class) |
| `CHANGELOG.md` | Changelog and improvement roadmap (agents must update) |

---

## Configuration

Environment variables (set in `.env` or directly):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token |
| `WEBHOOK_BASE_URL` | No | "" | Cloud Run URL (enables webhook mode) |
| `PORT` | No | 8080 | HTTP server port |
| `GOOGLE_CREDENTIALS_PATH` | No | credentials.json | Google service account JSON |
| `GOOGLE_SHEET_ID` | No | "" | Google Sheets document ID |
| `DATABASE_PATH` | No | transactions.db | SQLite database path |

---

## Important Notes

1. **Always run `pip install -e .`** before using `python -m treecko_bot.main` or `treecko-bot` command. Without editable install, module import fails.

2. **Tests are self-contained** and use temporary databases. No env setup required for tests.

3. **No CI/CD workflows exist** in this repository. Validation is manual.

4. **No linting tools configured** (no ruff, flake8, black, etc. in config).

5. **Pytest configuration** is in `pyproject.toml` under `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["src"]`.

6. **Entry points defined** in `pyproject.toml`: `treecko-bot = "treecko_bot.main:main"`

7. **SQLite database and credentials.json are gitignored**. Never commit these files.

---

## Making Changes

### Adding New Bot Commands

1. Add handler method in `src/treecko_bot/bot.py` in the `TreeckoBot` class
2. Register handler in `create_application()` method using `CommandHandler`
3. Add tests in `tests/` directory following existing patterns

### Modifying Database Schema

1. Update `Transaction` model in `src/treecko_bot/database.py`
2. Add new fields as nullable to avoid migration issues
3. Update `add_transaction()` method if needed
4. Add corresponding tests in `tests/test_database.py`

### Adding New Dependencies

1. Add to both `requirements.txt` (pinned version) and `pyproject.toml` (minimum version)
2. Run `pip install -r requirements.txt` to validate
3. Run tests to ensure compatibility

---

## Improvement Proposals (Required)

**All agents must review and update `CHANGELOG.md` when working on this repository.**

### Before Starting Work

1. Read the "Improvement Roadmap" section in `CHANGELOG.md`
2. Review existing proposals to avoid duplicates
3. Update status of any items you plan to work on to "🔄 In Progress"

### When Identifying Improvements

If you identify potential improvements while working:

1. Add new proposals to the appropriate priority section in `CHANGELOG.md`:
   - 🔴 **High Priority**: Security, testing, CI/CD, critical bugs
   - 🟡 **Medium Priority**: Performance, code quality, developer experience
   - 🟢 **Low Priority**: New features, documentation, nice-to-haves

2. Use the template provided in `CHANGELOG.md`

### After Completing Work

1. Update the status of implemented items to "✅ Completed"
2. Add an entry under `[Unreleased]` section describing your changes
3. Follow [Keep a Changelog](https://keepachangelog.com/) format

---

## Trust These Instructions

These instructions have been validated by running the actual commands. If build or test commands fail, first verify the environment setup steps above before searching for alternatives.
