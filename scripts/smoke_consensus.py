"""Smoke-test the consensus pipeline end-to-end.

Seeds one synthetic admin prediction for today, boots the bot, fires the
consensus job, then cleans up its synthetic data and exits.

Run: python scripts/smoke_consensus.py
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.migrations import ensure_schema
from src.db.connection import get_conn
from src.utils.timezones import today_et
from src.bot.client import build_bot
from src.scheduler.jobs import job_post_consensus
from src.scheduler import jobs as jobs_module
import config

jobs_module.is_trading_day = lambda d: True

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s — %(message)s", level=logging.INFO)
logger = logging.getLogger("smoke")


def seed_synthetic_prediction(today):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM members WHERE discord_id = ?", (str(config.ADMIN_DISCORD_ID),)
        ).fetchone()
        if not row:
            logger.error("Admin not in members table — run scripts/seed_members.py first.")
            return False
        member_id = row["id"]
        conn.execute("DELETE FROM predictions WHERE date = ?", (today.isoformat(),))
        conn.execute("DELETE FROM daily_aggregates WHERE date = ?", (today.isoformat(),))
        conn.execute(
            "INSERT INTO predictions (date, member_id, prediction, confidence, submitted_at) VALUES (?, ?, ?, ?, ?)",
            (today.isoformat(), member_id, 1, 8, datetime.now(timezone.utc)),
        )
    logger.info("Seeded synthetic prediction (member=%s pred=Up conf=8) for %s", member_id, today)
    return True


def cleanup(today):
    with get_conn() as conn:
        conn.execute("DELETE FROM predictions WHERE date = ?", (today.isoformat(),))
        conn.execute("DELETE FROM daily_aggregates WHERE date = ?", (today.isoformat(),))
    logger.info("Cleaned up synthetic predictions + aggregate for %s", today)


async def main():
    ensure_schema()
    today = today_et()
    if not seed_synthetic_prediction(today):
        return

    bot = build_bot()
    fired = asyncio.Event()

    async def on_ready_smoke():
        if fired.is_set():
            return
        fired.set()
        try:
            await asyncio.sleep(1.5)
            logger.info("Firing job_post_consensus...")
            await job_post_consensus(bot)
            logger.info("Consensus fired. Check #verdict for the embed.")
        except Exception as e:
            logger.exception("Smoke fire failed: %s", e)
        finally:
            cleanup(today)
            await bot.close()

    bot.add_listener(on_ready_smoke, "on_ready")
    await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
