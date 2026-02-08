import logging

from discord.ext import commands

from bot.bll.misc import MiscBll

logger = logging.getLogger(__name__)


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.misc = MiscBll()

    @commands.hybrid_command(name="invite")
    async def generate_invite_link(self, ctx: commands.Context):
        """
        generate an invite link
        """
        try:
            response = await self.misc.generate_invite_link(ctx.channel)
            await ctx.reply(**response)
        except Exception:
            logger.exception("Error generating invite link")
