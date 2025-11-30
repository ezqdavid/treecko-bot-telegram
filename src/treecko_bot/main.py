"""Main entry point for the Treecko Finance Bot."""

from .bot import TreeckoBot
from .config import get_config
from .logging_config import get_logger, setup_logging

# Set up logging before anything else
setup_logging()

logger = get_logger(__name__)


def main() -> None:
    """Main entry point."""
    try:
        logger.info("Initializing Treecko Finance Bot...")
        config = get_config()
        bot = TreeckoBot(config)
        bot.run()
    except ValueError as e:
        logger.error("Configuration error", error=str(e))
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Unexpected error", exc_info=True, error=str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
