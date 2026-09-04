import logging

import discord
from discord import app_commands
from discord.ext import commands
from src.db.repositories import members
from src.bot.handlers.admin import is_admin
from src.bot.formatting import WELCOME_TEXT

log = logging.getLogger(__name__)


def register(bot: commands.Bot) -> None:

    @bot.tree.command(name="add_member", description="Add a council member")
    @app_commands.describe(
        user="Pick the Discord user to add",
        framework="Their trading framework (e.g. ICT, SMC)",
        source="Where you found them",
    )
    async def cmd_add_member(
        interaction: discord.Interaction,
        user: discord.User,
        framework: str,
        source: str,
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("⛔ Admin only.", ephemeral=True); return
        uname = user.display_name or user.name or str(user.id)
        try:
            members.add(str(user.id), uname, framework, source)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Could not add: {e}", ephemeral=True); return
        dm_note = ""
        try:
            await user.send(WELCOME_TEXT)
            dm_note = "\n📩 Welcome DM sent."
        except discord.Forbidden:
            dm_note = "\n⚠️ Couldn't DM them (DMs closed or no shared guild). Ask them to run `/welcome`."
        except discord.HTTPException as e:
            log.warning("Welcome DM failed for %s: %s", user.id, e)
            dm_note = "\n⚠️ Welcome DM failed to send. Ask them to run `/welcome`."
        await interaction.response.send_message(
            f"✅ Added {user.mention} as **{uname}** ({framework}){dm_note}",
            ephemeral=True,
        )

    @bot.tree.command(name="remove_member", description="Deactivate a council member")
    @app_commands.describe(user="Pick the Discord user to remove", reason="Reason (violations only)")
    async def cmd_remove_member(
        interaction: discord.Interaction,
        user: discord.User,
        reason: str = "",
    ):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message("⛔ Admin only.", ephemeral=True); return
        members.deactivate(str(user.id))
        await interaction.response.send_message(
            f"✅ Removed {user.mention} from the roster", ephemeral=True
        )
