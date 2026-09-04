import discord
from discord.ext import commands
from src.db.repositories import members, predictions
from src.bot.formatting import WELCOME_TEXT
from src.utils.timezones import today_et


def register(bot: commands.Bot) -> None:

    @bot.tree.command(name="status", description="Check if you've submitted today")
    async def cmd_status(interaction: discord.Interaction):
        member = members.get_by_discord_id(str(interaction.user.id))
        if not member:
            await interaction.response.send_message(
                "You're not on the Council roster. Contact the admin to be added.",
                ephemeral=True,
            )
            return
        today = today_et()
        submitted = predictions.has_submitted(member.id, today)
        msg = "✅ Submitted today." if submitted else "⏳ Not yet submitted today."
        await interaction.response.send_message(msg, ephemeral=True)

    @bot.tree.command(name="welcome", description="About the Council")
    async def cmd_welcome(interaction: discord.Interaction):
        member = members.get_by_discord_id(str(interaction.user.id))
        if not member:
            await interaction.response.send_message(
                "You're not on the Council roster. Contact the admin to be added.",
                ephemeral=True,
            )
            return
        today = today_et()
        submitted = predictions.has_submitted(member.id, today)
        status = "✅ Submitted today" if submitted else "⏳ Not yet submitted today"
        await interaction.response.send_message(
            f"{WELCOME_TEXT}\n\n— — —\nToday's status: {status}",
            ephemeral=True,
        )
