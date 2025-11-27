"""Main entry point for the Treecko Finance Bot."""

import logging

from .bot import TreeckoBot
from .config import get_config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point."""
    try:
        config = get_config()
        bot = TreeckoBot(config)
        bot.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
