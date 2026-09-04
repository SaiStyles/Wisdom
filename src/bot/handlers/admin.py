import io
import logging
import csv
import discord
from discord import app_commands
from discord.ext import commands
from src.bot.views import ResultView
from src.db.repositories import results, aggregates, members
from src.domain import stats
from src.utils.timezones import today_et
from src.db.connection import get_conn
import config

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_DISCORD_ID


async def _deny(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("⛔ Admin only.", ephemeral=True)


async def handle_result(interaction: discord.Interaction, outcome: int) -> None:
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("⛔ Admin only.", ephemeral=True)
        return

    today = today_et()
    agg = aggregates.get_for_date(today)
    if agg is None:
        await interaction.response.edit_message(
            content="⚠️ No aggregate for today — cannot record result.", view=None
        )
        return

    results.save(
        today=today,
        actual_outcome=outcome,
        consensus_prediction=agg.leading_option,
        consensus_percentage=agg.leading_pct,
        avg_confidence=agg.avg_confidence,
        total_submissions=agg.total_submissions,
        signal_type=agg.signal_type,
    )

    label = config.PREDICTION_LABELS[outcome]
    await interaction.response.edit_message(content=f"✅ Outcome recorded: **{label}**", view=None)


def register(bot: commands.Bot) -> None:

    @bot.tree.command(name="stats", description="Show council accuracy")
    async def cmd_stats(interaction: discord.Interaction):
        if not is_admin(interaction.user.id):
            await _deny(interaction); return
        data = stats.overall_accuracy()
        await interaction.response.send_message(
            f"📊 **Council Accuracy**\n\n"
            f"Total days tracked: {data['total']}\n"
            f"Correct predictions: {data['correct']}\n"
            f"Accuracy: {data['accuracy_pct']}%",
            ephemeral=True,
        )

    @bot.tree.command(name="member_stats", description="Per-member attendance stats")
    async def cmd_member_stats(interaction: discord.Interaction):
        if not is_admin(interaction.user.id):
            await _deny(interaction); return
        all_members = members.get_all()
        if not all_members:
            await interaction.response.send_message("No members found.", ephemeral=True); return
        lines = ["👥 **Member Stats**\n"]
        for m in all_members:
            data = stats.member_stats(m.id)
            lines.append(
                f"• {m.username or m.discord_id} ({m.framework}): "
                f"{data.get('submissions', 0)}/{data.get('total_days', 0)} days "
                f"({data.get('attendance_pct', 0)}%)"
            )
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @bot.tree.command(name="add_result", description="Record actual NY AM outcome for today")
    async def cmd_add_result(interaction: discord.Interaction):
        if not is_admin(interaction.user.id):
            await _deny(interaction); return
        today = today_et()
        agg = aggregates.get_for_date(today)
        if not agg:
            await interaction.response.send_message(
                "No aggregate found for today. Was the signal posted?", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"📋 What was the actual NY AM outcome for {today}?",
            view=ResultView(),
            ephemeral=True,
        )

    @bot.tree.command(name="skip_today", description="Skip today's prediction cycle")
    async def cmd_skip_today(interaction: discord.Interaction):
        if not is_admin(interaction.user.id):
            await _deny(interaction); return
        today = today_et()
        with get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO skips (date, reason) VALUES (?, ?)",
                (today.isoformat(), "admin skip")
            )
        await interaction.response.send_message(f"⏭️ Skipped for {today}.", ephemeral=True)

    @bot.tree.command(name="export", description="Export all results as CSV")
    async def cmd_export(interaction: discord.Interaction):
        if not is_admin(interaction.user.id):
            await _deny(interaction); return
        all_results = results.get_all()
        text_buf = io.StringIO()
        writer = csv.writer(text_buf)
        writer.writerow(["date", "actual_outcome", "consensus_prediction", "consensus_pct", "avg_confidence", "total_submissions", "signal_type"])
        for r in all_results:
            writer.writerow([r.date, r.actual_outcome, r.consensus_prediction, r.consensus_percentage, r.avg_confidence, r.total_submissions, r.signal_type])
        bio = io.BytesIO(text_buf.getvalue().encode())
        file = discord.File(bio, filename="council_results.csv")
        await interaction.response.send_message(file=file, ephemeral=True)

    if config.TEST_MODE:

        @bot.tree.command(name="test_broadcast", description="[TEST] Fire the broadcast job now")
        async def cmd_test_broadcast(interaction: discord.Interaction):
            if not is_admin(interaction.user.id):
                await _deny(interaction); return
            await interaction.response.defer(ephemeral=True, thinking=True)
            from src.scheduler.jobs import job_broadcast_question
            await job_broadcast_question(bot)
            await interaction.followup.send("✅ Test broadcast fired.", ephemeral=True)

        @bot.tree.command(name="test_consensus", description="[TEST] Fire the consensus job now")
        async def cmd_test_consensus(interaction: discord.Interaction):
            if not is_admin(interaction.user.id):
                await _deny(interaction); return
            await interaction.response.defer(ephemeral=True, thinking=True)
            from src.scheduler.jobs import job_post_consensus
            await job_post_consensus(bot)
            await interaction.followup.send("✅ Test consensus fired.", ephemeral=True)

        @bot.tree.command(name="test_reset", description="[TEST] Clear all of today's data")
        async def cmd_test_reset(interaction: discord.Interaction):
            if not is_admin(interaction.user.id):
                await _deny(interaction); return
            today = today_et()
            with get_conn() as conn:
                conn.execute("DELETE FROM predictions WHERE date = ?", (today.isoformat(),))
                conn.execute("DELETE FROM daily_aggregates WHERE date = ?", (today.isoformat(),))
                conn.execute("DELETE FROM broadcast_log WHERE date = ?", (today.isoformat(),))
                conn.execute("DELETE FROM results WHERE date = ?", (today.isoformat(),))
                conn.execute("DELETE FROM skips WHERE date = ?", (today.isoformat(),))
            await interaction.response.send_message(f"🗑️ Test data cleared for {today}.", ephemeral=True)
