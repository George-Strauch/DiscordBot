import logging

from discord.ext import commands
from discord import app_commands

logger = logging.getLogger(__name__)


class AdminActions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sync")
    async def sync(self, interaction):
        await interaction.response.send_message("Syncing")
        logger.info("syncing")
        x = await self.bot.tree.sync()
        logger.info("done syncing: %s", x)
