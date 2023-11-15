import discord
from discord.ext import commands
from discord import app_commands, Interaction
from src.components.discord_bll.misc_bll import MiscBll



class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "/opt/bot/data/misc.log"
        self.misc = MiscBll()


    @commands.hybrid_command(name="invite")
    async def generate_invite_link(self, ctx: commands.Context):
        """
        generate an invite link
        """
        try:
            response = await self.misc.generate_invite_link(ctx.channel)
            await ctx.reply(
                **response
            )
        except Exception as ex:
            # todo log
            print(ex.args)
