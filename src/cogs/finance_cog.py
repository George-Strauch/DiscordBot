import discord
from discord.ext import commands
from discord import app_commands
from .functions.finance import TickerInfo
from .utils import log_events, chunk_message


class Finance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "data/finance.log"
        self.ticker_info = TickerInfo()

    @app_commands.command(name="ticker")
    @app_commands.describe(ticker="Stock Ticker")
    async def get_ticker_info(self, interaction: discord.Interaction, ticker:str):
        """
        Get info from a stock
        """
        log_events(f"[{interaction.user.name}] WANTS TO GET TICKER DATA FOR: {ticker}", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        reply = self.ticker_info.ticker_data(ticker)
        await interaction.edit_original_response(content=reply)
