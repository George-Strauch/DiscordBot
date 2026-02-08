import logging

import discord
from discord.ext import commands
from discord import app_commands

from bot.services.trends_client import get_trending_searches

logger = logging.getLogger(__name__)


class Trends(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="trending")
    async def trending(self, interaction: discord.Interaction):
        """
        Get a list of trending google searches
        """
        logger.info("[%s] QUERIED TRENDING", interaction.user.name)
        await interaction.response.send_message("Working on that, one sec ...")
        trends = get_trending_searches()
        await interaction.edit_original_response(content=trends[:2000])
