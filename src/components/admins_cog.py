import discord
from discord.ext import commands
from discord import app_commands
from discord import ui
from discord import Interaction


class AdminActions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "/opt/bot/data/admins.log"

    @app_commands.command(name="sync")
    async def sync(self, interaction):
        await interaction.response.send_message("Syncing")
        print("syncing")
        x = await self.bot.tree.sync()
        print("done syncing")
        print(x)




