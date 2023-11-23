import asyncio
import json

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
        tokens = response["tokens"]
        print(f"TOTAL TOKENS USED IN CALL: {tokens} | AT A COST OF ${tokens*(0.06/1000):.2f}")
        display_objects = response["display_content"]
        for x in display_objects:
            print(f"sending response: {x}")
            await ctx.reply(**x)
            await asyncio.sleep(1)
        del response["display_content"]
        print(json.dumps(response, indent=4))

