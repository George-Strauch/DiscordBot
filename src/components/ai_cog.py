import discord
from discord.ext import commands
from discord import app_commands
from .discord_bll.ai_bll import AIBll
from .utils import log_events, chunk_message, read_file


class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.log_file = "/opt/bot/data/ai.log"
        self.bot = bot
        self.ai = AIBll()

    @commands.hybrid_command(
        name="gpt",
        description="Use Chat GPT"
    )
    @app_commands.describe(prompt="Prompt for GPT4")
    @app_commands.describe(model="GPT model (default GPT4-Turbo)")
    @app_commands.choices(model=[
        discord.app_commands.Choice(name="GPT4-Turbo", value="gpt-4-1106-preview"),
        discord.app_commands.Choice(name="GPT4", value="gpt-4"),
        discord.app_commands.Choice(name="GPT3", value="gpt-3.5-turbo-1106"),

    ])
    async def ask_gpt(
            self,
            ctx: commands.Context,
            *,
            prompt: str,
            model: discord.app_commands.Choice[str] = "gpt-4-1106-preview"
    ):
        """
        Query GPT
        todo try / except
        """
        prompt_context = self.ai.context_definer(content=prompt, role="user")
        model = model if isinstance(model, str) else model.value
        log_events(f"[{ctx.author.name}] ASKED GPT: {prompt} with model: {model}", self.log_file)

        await ctx.reply("Working on that ...")
        print(self.ai.gpt_schema)
        print("asdf")
        reply = self.ai.ask_gpt(
            prompt=prompt,
            additional_context=self.ai.gpt_schema["context"],
            model=model,
            temperature=0.4
        )
        print(reply)
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
        description="Generate an image with DALL-E"
    )
    @app_commands.describe(prompt="Thing you want an image of")
    async def image_generator(
            self,
            ctx: commands.Context,
            *,
            prompt: str,):
        """
        Generate an image using from Open AI
        """
        log_events(f"[{ctx.author.name}] WANTS TO GENERATE IMAGE: {prompt}", self.log_file)
        await ctx.reply("Working on that ...")
        reply = self.ai.image(prompt)
        if "error" in reply:
            await ctx.reply(content=f"An error occurred | {reply['url']}")
        else:
            log_events(f"Reply is {reply}", self.log_file)
            await ctx.reply(content=reply['url'])

