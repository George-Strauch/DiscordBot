import logging
import traceback

import discord
from discord.ext import commands
from discord import app_commands

from bot.bll.news import NewsBll, param_descriptions, news_choices
from bot.database.news_db import NewsNotificationDatabase
from bot import config

logger = logging.getLogger(__name__)


class News(commands.Cog):
    def __init__(self, bot: commands.Bot, guilds=None):
        if guilds is None:
            guilds = []
        self.bot = bot
        self.news_bll = NewsBll()
        self.db = NewsNotificationDatabase(config.DB_PATH)

    @commands.hybrid_command(name="news")
    @app_commands.describe(**param_descriptions)
    @app_commands.choices(source=news_choices["sources"])
    async def get_news(
        self,
        ctx: commands.Context,
        *,
        text: str = "",
        n: int = 5,
        source: discord.app_commands.Choice[str] = "",
    ):
        """
        Shows most recent news
        """
        await ctx.reply("Working on that ...")
        source = source.value if not isinstance(source, str) else ""
        sources = [] if source in ["x", ""] else source
        if isinstance(sources, str):
            sources = [sources]
        try:
            response = self.news_bll.get_news(text=text, sources=sources, n=n)
            await ctx.reply(**response)
        except Exception:
            await ctx.reply(content="Something went wrong getting news :[")
            logger.exception("Error getting news")

    @commands.hybrid_command(name="notifications")
    async def get_news_notifications(self, ctx: commands.Context):
        try:
            response = self.news_bll.get_news_notifications(guild_id=ctx.guild.id)
            await ctx.reply(**response)
        except Exception as e:
            await ctx.reply(content="Something went wrong getting news notifications")
            logger.exception("Error getting news notifications")

    @commands.hybrid_command(name="stop_news_notification")
    @app_commands.describe(
        ids="id of news notification loop. Multiple may be provided separated by space (Use /notifications to get list)"
    )
    async def stop_news_notifications(self, ctx: commands.Context, *, ids: str):
        problems = []
        success = []
        for x in ids.split(" "):
            if not x.isdigit():
                problems.append(f"Invalid id {x}")
            else:
                x = int(x)
                try:
                    response = self.news_bll.stop_news_notifications(guild_id=ctx.guild.id, _id=x)
                    success.append(response["content"])
                except Exception as e:
                    problems.append(f"Issue occurred canceling notification loop with id: {x}")
                    logger.exception("Error stopping notification %d", x)
        success = "\n".join(success)
        problems = "\n".join(problems)
        msg = f"{success}\n{problems}"
        await ctx.reply(content=msg, ephemeral=True)
