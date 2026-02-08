import logging
import traceback

import discord
from discord.ext import commands

from bot import config
from bot.cogs.ai import AI
from bot.cogs.news import News
from bot.cogs.trends import Trends
from bot.cogs.finance import Finance
from bot.cogs.interactions import Interactions
from bot.cogs.admin import AdminActions
from bot.cogs.ava import AvaNlp
from bot.cogs.misc import Misc

logger = logging.getLogger(__name__)


class BasedClient(commands.Bot):
    def __init__(self, **kwargs):
        if "command_prefix" not in kwargs:
            kwargs["command_prefix"] = config.COMMAND_PREFIX
        if "intents" not in kwargs:
            intents = discord.Intents.default()
            intents.message_content = True
            kwargs["intents"] = intents
        super().__init__(**kwargs)

        self.bot_channel_ids = config.load_json_config("bot_channels.json", default=[])
        self.news_channels_ids = config.load_json_config("news_channels.json", default=[])
        self.bot_channel = []
        self.news_channels = []

    async def on_ready(self):
        try:
            await self.load_cogs()
        except Exception:
            logger.exception("Exception occurred while loading cogs")
        logger.info("Logged on as %s", self.user)

    async def on_message(self, message):
        if message.author.bot:
            return
        logger.debug("%s SAID: %s", message.author.name, message.content)
        await super().on_message(message)

    async def load_cogs(self):
        logger.info("Loading Cogs")
        await self.add_cog(AI(self))
        await self.add_cog(News(self, guilds=self.guilds))
        await self.add_cog(Trends(self))
        await self.add_cog(Finance(self))
        await self.add_cog(AvaNlp(self))
        await self.add_cog(AdminActions(self))
        await self.add_cog(Misc(self))
