import logging
import re

import discord
from discord.ext import commands
from discord import app_commands

from bot.bll.finance import FinanceBll

logger = logging.getLogger(__name__)


class Finance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.finance = FinanceBll()

    @commands.hybrid_command(name="ticker")
    @app_commands.describe(
        tickers="Stock Tickers (up to 5) (separated by single space if multiple are provided. "
                "For crypto you must specify exchange currency, e.g. btc-usd)"
    )
    @app_commands.describe(period="Period of time over which you want to show data")
    @app_commands.choices(period=[
        discord.app_commands.Choice(name="1 Day", value="1d"),
        discord.app_commands.Choice(name="5 Day", value="5d"),
        discord.app_commands.Choice(name="1 Month", value="1mo"),
        discord.app_commands.Choice(name="3 Month", value="3mo"),
        discord.app_commands.Choice(name="6 Month", value="6mo"),
        discord.app_commands.Choice(name="1 Year", value="1y"),
        discord.app_commands.Choice(name="5 Year", value="5y"),
        discord.app_commands.Choice(name="MAX", value="max"),
    ])
    async def ticker(
        self,
        ctx: commands.Context,
        tickers: str,
        period: discord.app_commands.Choice[str] = "1mo",
    ):
        """
        Get info for stock ticker(s)
        """
        if not isinstance(period, str):
            period = period.value
        tickers = tickers.split(" ")
        for t in tickers:
            if not re.match(r"^\^?[A-Za-z\-]{1,10}$", t):
                await ctx.reply(content=f"Invalid ticker format: {t}")
                return
        data = self.finance.send_ticker_price(tickers=tickers, period=period)
        await ctx.reply(**data)
