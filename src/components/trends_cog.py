import discord
from discord.ext import commands
from discord import app_commands
from .functions.trends import get_trending_searches
from .utils import log_events, chunk_message


class Trends(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "/opt/bot/data/trending.log"
        self.trends_searcher = None

    @app_commands.command(name="trending")
    async def trending(self, interaction: discord.Interaction):
        """
        Get a list of trending google searches
        """
        log_events(f"[{interaction.user.name}] QUERIED TRENDING", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        trends = get_trending_searches()
        await interaction.edit_original_response(content=trends[:2000])
