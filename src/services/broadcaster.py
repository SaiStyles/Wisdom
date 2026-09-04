import asyncio
import logging
from datetime import date, datetime, timezone
import discord
from discord.ext import commands
from src.db.repositories.members import Member
from src.db.connection import get_conn
from src.bot.views import PredictionView
from src.bot.formatting import QUESTION_TEXT

logger = logging.getLogger(__name__)


async def send_question(bot: commands.Bot, member: Member, today: date) -> bool:
    try:
        user = bot.get_user(int(member.discord_id)) or await bot.fetch_user(int(member.discord_id))
        await user.send(QUESTION_TEXT, view=PredictionView())
        _mark_delivered(member.id, today)
        return True
    except discord.Forbidden:
        logger.warning("Cannot DM member %s (%s) — they haven't opened DMs or blocked bot", member.id, member.username)
        return False
    except discord.NotFound:
        logger.warning("Discord user %s not found for member %s", member.discord_id, member.id)
        return False
    except Exception as e:
        logger.error("Failed to send to member %s: %s", member.id, e)
        return False


async def broadcast(bot: commands.Bot, members_list: list[Member], today: date) -> None:
    import config
    undelivered = members_list if config.TEST_MODE else _get_undelivered(members_list, today)
    for member in undelivered:
        await send_question(bot, member, today)
        await asyncio.sleep(0.05)


def _mark_delivered(member_id: int, today: date) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO broadcast_log (date, member_id, delivered, delivered_at)
               VALUES (?, ?, TRUE, ?)
               ON CONFLICT(date, member_id) DO UPDATE SET delivered=TRUE, delivered_at=excluded.delivered_at""",
            (today.isoformat(), member_id, datetime.now(timezone.utc))
        )


def _get_undelivered(members_list: list[Member], today: date) -> list[Member]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT member_id FROM broadcast_log WHERE date = ? AND delivered = TRUE",
            (today.isoformat(),)
        ).fetchall()
    delivered_ids = {r["member_id"] for r in rows}
    return [m for m in members_list if m.id not in delivered_ids]
