import discord
from discord.ext import commands
from discord import app_commands
from .functions.ai import OpenAIwrapper
from .utils import log_events, chunk_message


class AI(commands.Cog):
    def __init__(self, bot: commands.Bot, api_key: str=""):
        self.bot = bot
        self.log_file = "/opt/bot/data/ai.log"
        self.open_ai = OpenAIwrapper(api_key)

    @app_commands.command(name="gpt", description="use chat GPT")
    @app_commands.describe(prompt="Prompt for GPT4")
    @app_commands.describe(model="GPT model (default GPT4)")
    @app_commands.choices(model=[
        discord.app_commands.Choice(name="GPT4", value="gpt-4"),
        discord.app_commands.Choice(name="GPT3", value="gpt-3.5-turbo-0613"),
    ])
    async def ask_gpt(
            self,
            interaction: discord.Interaction,
            prompt: str,
            model: discord.app_commands.Choice[str] = "gpt-4"
    ):
        """
        Query GPT
        """
        # todo remove mention instructions from context
        model = model if isinstance(model, str) else model.value
        log_events(f"[{interaction.user.name}] ASKED GPT: {prompt} with model: {model}", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        reply = self.open_ai.generate_response_gpt(prompt, model=model)
        if "```" not in reply:
            reply = f"``{reply}``"
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

