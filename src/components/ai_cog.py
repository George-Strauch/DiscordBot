import discord
from discord.ext import commands
from discord import app_commands
from .functions.ai import OpenAIwrapper
from .utils import log_events, chunk_message


class AI(commands.Cog):
    def __init__(self, bot: commands.Bot, api_key: str=""):
        self.bot = bot
        self.log_file = "data/ai.log"
        self.open_ai = OpenAIwrapper(api_key)

    @app_commands.command(name="gpt", description="use chat GPT")
    @app_commands.describe(prompt="Prompt for GPT4")
    async def ask4(self, interaction: discord.Interaction, prompt: str):
        """
        Query GPT4
        """
        # todo remove mention instructions from context
        log_events(f"[{interaction.user.name}] ASKED GPT: {prompt}", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        reply = self.open_ai.generate_response_gpt4(prompt)
        reply = chunk_message(reply)
        await interaction.edit_original_response(content=reply[0])

    @app_commands.command(name="image")
    @app_commands.describe(prompt="Thing you want an image of")
    async def image_generator(self, interaction: discord.Interaction, prompt: str):
        """
        Generate an image using from Open AI
        """
        log_events(f"[{interaction.user.name}] WANTS TO GENERATE IMAGE: {prompt}", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        reply = self.open_ai.image_generator(prompt)
        log_events(f"Reply is {reply}", self.log_file)
        await interaction.edit_original_response(content=reply)

