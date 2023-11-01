import json
import discord
from discord.ext import commands
from discord import app_commands
from .functions.news import NewsFunctions
from .functions.warn_notice import get_new_warn_data
from .utils import log_events, chunk_message





# @bot.tree.command(name="log")
# async def get_log_data(interaction: discord.Interaction):
#     """
#     display log data in case of unexpected behavior
#     """
#     if not interaction.user.guild_permissions.administrator:
#         await interaction.response.send_message(
#             "NT buddy, but that's only for admins. Just for that you are now breathing manually and "
#             "aware there is no comfortable spot in your mouth for your tongue",
#             ephemeral=True
#         )
#         return
#     with open(LOG_FILE, 'r') as fp:
#         txt = fp.readlines()
#         txt = "".join(txt)
#     await interaction.response.send_message(txt[-2000:], ephemeral=True)
#     time.sleep(1)
#     with open("data/log.txt", 'r') as fp:
#         txt = fp.readlines()
#         txt = "".join(txt)
#     await interaction.response.send_message(txt[-2000:], ephemeral=True)