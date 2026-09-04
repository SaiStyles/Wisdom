import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands
import config

ET = pytz.timezone(config.TIMEZONE)


def build_scheduler(bot: commands.Bot) -> AsyncIOScheduler:
    from src.scheduler.jobs import job_broadcast_question, job_post_consensus, job_session_end_reminder

    scheduler = AsyncIOScheduler(timezone=ET)

    scheduler.add_job(
        job_broadcast_question,
        CronTrigger(day_of_week="mon-fri", hour=config.BROADCAST_HOUR, minute=config.BROADCAST_MINUTE, timezone=ET),
        args=[bot],
        id="broadcast",
        misfire_grace_time=60,
    )

    scheduler.add_job(
        job_post_consensus,
        CronTrigger(day_of_week="mon-fri", hour=config.CONSENSUS_HOUR, minute=config.CONSENSUS_MINUTE, timezone=ET),
        args=[bot],
        id="consensus",
        misfire_grace_time=60,
    )

    scheduler.add_job(
        job_session_end_reminder,
        CronTrigger(day_of_week="mon-fri", hour=config.SESSION_END_HOUR, minute=config.SESSION_END_MINUTE, timezone=ET),
        args=[bot],
        id="session_end",
        misfire_grace_time=60,
    )

    return scheduler
