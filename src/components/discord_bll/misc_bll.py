import discord
from discord.ext import commands
from discord import app_commands, Interaction


class MiscBll():
    def __init__(self):
        self.log_file = "/opt/bot/data/misc_bll.log"


    async def generate_invite_link(self, channel):
        """
        generate an invite link
        """
        invite_link = await channel.create_invite(max_age=0)
        return {
            "content": invite_link,
            "ephemeral": True
        }
