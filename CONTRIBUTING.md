# Contributing to Treecko Finance Bot

Thank you for your interest in contributing to Treecko Finance Bot! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all backgrounds and experience levels.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/treecko-bot-telegram.git
   cd treecko-bot-telegram
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/ezqdavid/treecko-bot-telegram.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Install test dependencies:
   ```bash
   pip install pytest pytest-asyncio
   ```

### Environment Variables

Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Required variables:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (get one from [@BotFather](https://t.me/BotFather))

Optional variables are documented in `.env.example`.

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-command` - For new features
- `fix/parsing-error` - For bug fixes
- `docs/update-readme` - For documentation changes
- `refactor/improve-database` - For code refactoring

### Commit Messages

Write clear, concise commit messages:
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues when applicable (e.g., "Fix #123")

Example:
```
Add /report command for transaction summaries

- Add get_transaction_summary method to DatabaseManager
- Implement report command handler with date range options
- Add tests for the new functionality
```

## Testing

### Running Tests

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_bot.py -v
```

Run tests with coverage:
```bash
pip install pytest-cov
python -m pytest tests/ --cov=treecko_bot --cov-report=term-missing
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with the `test_` prefix
- Name test functions with the `test_` prefix
- Use descriptive test names that explain what is being tested
- Use fixtures for common setup code
- Mock external dependencies (Telegram API, Google Sheets, etc.)

Example:
```python
@pytest.mark.asyncio
async def test_report_command_shows_summary(self, bot, mock_update, mock_context):
    """Test the /report command shows transaction summary data."""
    mock_context.args = []
    await bot.report(mock_update, mock_context)
    
    call_args = mock_update.message.reply_text.call_args
    response = call_args[0][0]
    assert "Income" in response
    assert "Expenses" in response
```

## Code Style

### Linting

We use [Ruff](https://docs.astral.sh/ruff/) for linting. Run the linter:
```bash
ruff check src/ tests/
```

Auto-fix issues:
```bash
ruff check --fix src/ tests/
```

### Type Hints

- Use type hints for all function parameters and return values
- Use modern Python type hints (e.g., `list[str]` instead of `List[str]`)
- Use `| None` for optional types (e.g., `str | None`)

### Docstrings

- Add docstrings to all public modules, classes, and functions
- Use Google-style docstrings
- Include Args, Returns, and Raises sections where applicable

Example:
```python
def add_transaction(
    self,
    date: datetime,
    description: str,
    amount: float,
) -> Transaction:
    """Add a new transaction to the database.

    Args:
        date: Transaction date.
        description: Transaction description.
        amount: Transaction amount.

    Returns:
        The created Transaction object.

    Raises:
        ValueError: If the amount is negative.
    """
```

## Submitting Changes

1. Ensure all tests pass locally
2. Run the linter and fix any issues
3. Push your changes to your fork
4. Create a Pull Request against the `main` branch
5. Fill out the PR template with:
   - Description of changes
   - Related issue number (if applicable)
   - Testing steps
   - Screenshots (for UI changes)

### PR Review Process

- PRs require at least one approval before merging
- CI checks must pass (tests, linting)
- Address review feedback promptly
- Keep PRs focused and reasonably sized

## Reporting Issues

### Bug Reports

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages or logs (if applicable)

### Feature Requests

When requesting features:
- Describe the use case
- Explain the expected behavior
- Consider how it fits with existing functionality

## Project Structure

```
treecko-bot-telegram/
├── src/treecko_bot/       # Main application package
│   ├── __init__.py        # Package init
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration
│   ├── bot.py             # Telegram bot handlers
│   ├── database.py        # Database operations
│   ├── pdf_parser.py      # PDF parsing
│   └── sheets.py          # Google Sheets integration
├── tests/                 # Test files
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
└── README.md              # Project documentation
```

## Questions?

If you have questions, feel free to:
- Open a GitHub issue
- Review existing documentation in the README

Thank you for contributing! 🌿
