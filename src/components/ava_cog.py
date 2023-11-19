import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from .discord_bll.ava_bll import AvaBll
from .utils import chunk_message



class AvaNlp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        print("loading ava cog")
        self.ava = AvaBll()
        self.bot = bot
        self.log_file = "/opt/bot/data/ava_cog.log"

    @commands.hybrid_command(
        name="ava",
        description="Provide a natural language input for the bot to do things, powered by GPT"
    )
    @app_commands.describe(prompt="Prompt for what action you want the bot to do")
    async def ava(
            self,
            ctx: commands.Context,
            *,
            prompt: str,
    ):
        print(f"prompt is {prompt}")
        await ctx.reply("Working on that...")
        response = self.ava.call_ava(prompt=prompt)
        for x in response:
            await ctx.reply(**x)
            await asyncio.sleep(1)

