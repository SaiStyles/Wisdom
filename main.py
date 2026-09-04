import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.db.migrations import ensure_schema
from src.bot.client import build_bot
import config

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    ensure_schema()
    logger.info("DB schema ready.")

    bot = build_bot()
    logger.info("Bot starting...")
    bot.run(config.BOT_TOKEN)


if __name__ == "__main__":
    main()
