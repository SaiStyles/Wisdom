import logging
import discord
from discord.ext import commands
import config

logger = logging.getLogger(__name__)


def build_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.members = True  # needed to resolve Member objects and DM users reliably

    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        logger.info("Logged in as %s (id=%s)", bot.user, bot.user.id)

    async def setup_hook():
        from src.bot.views import PredictionView, ResultView
        from src.bot.handlers import admin, membership, lifecycle, errors

        admin.register(bot)
        membership.register(bot)
        lifecycle.register(bot)
        errors.register(bot)

        bot.add_view(PredictionView())
        bot.add_view(ResultView())

        guild = discord.Object(id=config.GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        logger.info("Synced %d slash commands to guild %s", len(synced), config.GUILD_ID)

        from src.scheduler.runner import build_scheduler
        scheduler = build_scheduler(bot)
        scheduler.start()
        bot._scheduler = scheduler
        logger.info("Scheduler started.")

    bot.setup_hook = setup_hook
    return bot
