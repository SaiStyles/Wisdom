import discord
from src.domain.aggregator import Aggregate
import config


QUESTION_TEXT = (
    "🏛️ **Council of Wise Men — Daily Signal**\n\n"
    "NY AM Session (9:30-11:00 ET) — What do you expect for **NQ**?\n\n"
    "⏰ Cutoff: 9:28 AM ET sharp. No late entries."
)


WELCOME_TEXT = (
    "🏛️ **Welcome to the Council of Wise Men.**\n\n"
    "Here's how this works:\n\n"
    "1. Every weekday at **9:20 AM New York time**, you'll receive a private DM from this bot.\n"
    "2. It asks **one question** about what you expect in the NY AM session (9:30-11:00) for **NQ**.\n"
    "3. You tap your prediction and confidence (1-10).\n"
    "4. At **9:29 AM**, the aggregated result is posted to the group channel — no individual names attached.\n"
    "5. You trade your own setup based on the crowd signal.\n\n"
    "**Rules:**\n"
    "• Submit independently. Don't discuss the market with anyone before submitting.\n"
    "• Don't share your vote with anyone.\n"
    "• You have 8 minutes to respond (9:20–9:28 AM ET).\n"
    "• No late submissions accepted.\n"
    "• Your individual accuracy is never shared publicly.\n\n"
    "That's it. One question. 8 minutes. Every day.\n\n"
    "_The power of this system comes from each person thinking independently._\n"
    "_Your honest opinion — right or wrong — makes the group smarter._"
)


SIGNAL_COLORS = {
    "HIGH": discord.Color.green(),
    "MODERATE": discord.Color.gold(),
    "NO_SIGNAL": discord.Color.red(),
}


def consensus_embed(agg: Aggregate, signal_type: str, today: str, roster_size: int) -> discord.Embed:
    label = config.PREDICTION_LABELS

    if signal_type == "HIGH":
        signal_line = f"🟢 **HIGH CONVICTION — {label[agg.leading_option].upper()}**"
    elif signal_type == "MODERATE":
        signal_line = f"🟡 **MODERATE — {label[agg.leading_option]}**"
    else:
        signal_line = "🔴 **NO SIGNAL — Stay out**"

    embed = discord.Embed(
        title=f"🏛️ COUNCIL SIGNAL — {today}",
        description=signal_line,
        color=SIGNAL_COLORS.get(signal_type, discord.Color.light_grey()),
    )
    embed.add_field(name="📈 Expansion Up", value=f"{agg.up}/{agg.total} ({agg.up_pct}%)", inline=True)
    embed.add_field(name="📉 Expansion Down", value=f"{agg.down}/{agg.total} ({agg.down_pct}%)", inline=True)
    embed.add_field(name="↔️ Expansion Both", value=f"{agg.both}/{agg.total} ({agg.both_pct}%)", inline=True)
    embed.add_field(name="⬜ Range", value=f"{agg.range_}/{agg.total} ({agg.range_pct}%)", inline=True)
    embed.add_field(name="🎯 Avg Confidence", value=f"{agg.avg_confidence}/10", inline=True)
    embed.add_field(name="👥 Submissions", value=f"{agg.total}/{roster_size}", inline=True)
    return embed
