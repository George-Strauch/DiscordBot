import logging

import discord
from discord.ext import commands
from discord import app_commands

from bot.bll.ai import AIBll
from bot.utils import chunk_message

logger = logging.getLogger(__name__)


class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ai = AIBll()

    @commands.hybrid_command(
        name="gpt",
        description="Use Chat GPT",
    )
    @app_commands.describe(prompt="Prompt for GPT")
    @app_commands.describe(model="GPT model (default GPT-4o)")
    @app_commands.choices(model=[
        discord.app_commands.Choice(name="GPT-4o", value="gpt-4o"),
        discord.app_commands.Choice(name="GPT-4o-mini", value="gpt-4o-mini"),
        discord.app_commands.Choice(name="GPT-4-Turbo", value="gpt-4-turbo"),
    ])
    async def ask_gpt(
        self,
        ctx: commands.Context,
        *,
        prompt: str,
        model: discord.app_commands.Choice[str] = "gpt-4o",
    ):
        prompt_context = self.ai.context_definer(content=prompt, role="user")
        model = model if isinstance(model, str) else model.value
        logger.info("[%s] ASKED GPT: %s with model: %s", ctx.author.name, prompt, model)

        await ctx.reply("Working on that ...")
        reply = self.ai.ask_gpt(
            prompt=prompt,
            additional_context=self.ai.gpt_schema["context"],
            model=model,
            temperature=0.4,
        )
        if "error" in reply:
            await ctx.reply("An issue occurred calling Open AI's API")
        else:
            chunks = reply["text"]
            if isinstance(chunks, str):
                chunks = [chunks]
            for c in chunks:
                await ctx.reply(content=c)
            if "total_tokens" in reply:
                await ctx.reply(content=f"Total Tokens: {reply['total_tokens']}")

    @commands.hybrid_command(
        name="image",
        description="Generate an image with DALL-E",
    )
    @app_commands.describe(prompt="Thing you want an image of")
    async def image_generator(self, ctx: commands.Context, *, prompt: str):
        logger.info("[%s] WANTS TO GENERATE IMAGE: %s", ctx.author.name, prompt)
        await ctx.reply("Working on that ...")
        reply = self.ai.image(prompt)
        if "error" in reply:
            await ctx.reply(content=f"An error occurred | {reply['url']}")
        else:
            logger.debug("Reply is %s", reply)
            await ctx.reply(content=reply["url"])
