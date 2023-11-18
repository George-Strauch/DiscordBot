import discord
from discord.ext import commands
from discord import app_commands
from ..functions.trends import get_trending_searches
from ..utils import log_events, chunk_message


class Trends(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "/opt/bot/data/trending.log"
        self.trends_searcher = None

    async def trending(self):
        """
        Get a list of trending google searches
        """
        # todo
        trends = get_trending_searches()
        return trends
