import logging
import traceback
import discord
from discord import app_commands
from discord.ext import commands
import config

logger = logging.getLogger(__name__)


def register(bot: commands.Bot) -> None:

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        logger.exception("Slash command error", exc_info=error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"⚠️ Error: {type(error).__name__}: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ Error: {type(error).__name__}: {error}", ephemeral=True)
        except Exception:
            logger.exception("Failed to report error to user")
        await _notify_admin(bot, error)

    @bot.event
    async def on_error(event_method: str, *args, **kwargs):
        tb = traceback.format_exc()
        logger.error("Unhandled error in %s:\n%s", event_method, tb)
        await _notify_admin(bot, RuntimeError(f"{event_method}: {tb.splitlines()[-1] if tb else '?'}"))


async def _notify_admin(bot: commands.Bot, error: BaseException) -> None:
    try:
        admin = bot.get_user(config.ADMIN_DISCORD_ID) or await bot.fetch_user(config.ADMIN_DISCORD_ID)
        await admin.send(f"⚠️ Bot error: {type(error).__name__}: {error}")
    except Exception:
        logger.exception("Failed to DM admin about error")
