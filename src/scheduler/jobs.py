import logging
from discord.ext import commands
from src.db.repositories import members, predictions, aggregates
from src.domain.aggregator import aggregate
from src.domain.classifier import classify
from src.bot.formatting import consensus_embed
from src.services.broadcaster import broadcast
from src.scheduler.calendar import is_trading_day
from src.utils.timezones import today_et
import config

logger = logging.getLogger(__name__)


async def job_broadcast_question(bot: commands.Bot) -> None:
    today = today_et()
    if not is_trading_day(today) and not config.TEST_MODE:
        logger.info("Not a trading day, skipping broadcast.")
        return
    active = members.get_all_active()
    logger.info("Broadcasting to %d members", len(active))
    await broadcast(bot, active, today)


async def job_post_consensus(bot: commands.Bot) -> None:
    today = today_et()
    if not is_trading_day(today) and not config.TEST_MODE:
        return

    agg_row = aggregates.get_for_date(today)
    if agg_row and agg_row.posted_to_group:
        logger.info("Consensus already posted for %s", today)
        return

    preds = predictions.get_for_date(today)
    agg = aggregate(preds)
    active = members.get_all_active()
    signal = classify(agg, len(active))

    aggregates.save(
        today, agg.up, agg.down, agg.both, agg.range_,
        agg.avg_confidence, agg.total,
        leading_option=agg.leading_option,
        leading_pct=agg.leading_pct,
        signal_type=signal,
    )

    if config.GROUP_CHANNEL_ID is None:
        logger.error("GROUP_CHANNEL_ID not configured; skipping group post for %s", today)
        return

    channel = bot.get_channel(config.GROUP_CHANNEL_ID) or await bot.fetch_channel(config.GROUP_CHANNEL_ID)
    embed = consensus_embed(agg, signal, str(today), len(active))
    await channel.send(embed=embed)
    aggregates.mark_posted(today)
    logger.info("Consensus posted for %s: %s", today, signal)


async def job_session_end_reminder(bot: commands.Bot) -> None:
    today = today_et()
    if not is_trading_day(today) and not config.TEST_MODE:
        return
    from src.db.repositories import results
    result = results.get_for_date(today)
    if result:
        return
    try:
        admin = bot.get_user(config.ADMIN_DISCORD_ID) or await bot.fetch_user(config.ADMIN_DISCORD_ID)
        await admin.send("📋 Don't forget to record today's actual outcome. Use /add_result")
    except Exception as e:
        logger.error("Failed to send session-end reminder to admin: %s", e)
