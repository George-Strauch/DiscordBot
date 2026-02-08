import asyncio
import json
import logging

from discord.ext import commands
from discord import app_commands

from bot.bll.ava import AvaBll
from bot.utils import chunk_message

logger = logging.getLogger(__name__)


class AvaNlp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        logger.info("loading ava cog")
        self.ava = AvaBll()
        self.bot = bot

    @commands.hybrid_command(
        name="ava",
        description="Provide a natural language input for the bot to do things, powered by GPT",
    )
    @app_commands.describe(prompt="Prompt for what action you want the bot to do")
    async def ava(self, ctx: commands.Context, *, prompt: str):
        logger.info("prompt is %s", prompt)
        await ctx.reply("Working on that...")
        response = self.ava.call_ava(prompt=prompt)
        tokens = response["tokens"]
        logger.info("TOTAL TOKENS USED IN CALL: %d | AT A COST OF $%.2f", tokens, tokens * (0.06 / 1000))
        display_objects = response["display_content"]
        for x in display_objects:
            logger.debug("sending response: %s", x)
            await ctx.reply(**x)
            await asyncio.sleep(1)
