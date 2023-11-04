import discord
from discord.ext import commands
from discord import app_commands
from .functions.finance import TickerInfo
from .utils import log_events, chunk_message
import io


class Finance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "data/finance.log"
        self.ticker_info = TickerInfo()

    @app_commands.command(name="ticker")
    @app_commands.describe(ticker="Stock Ticker")
    async def get_ticker_info(self, interaction: discord.Interaction, ticker:str):
        """
        Get info from a stock
        """
        log_events(f"[{interaction.user.name}] WANTS TO GET TICKER DATA FOR: {ticker}", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        reply, prices = self.ticker_info.ticker_data(ticker)
        # await interaction.edit_original_response(content=reply)
        picture_plot = self.ticker_info.get_img(prices)
        with io.BytesIO() as image_binary:
            print(image_binary)
            picture_plot.savefig(image_binary, format='PNG', bbox_inches='tight', pad_inches=0, transparent=True)
            image_binary.seek(0)
            # await interaction.followup.send(file=discord.File(fp=image_binary, filename='image.png'))
            e = discord.Embed(
                title=ticker.upper(),
                description=reply,
                color=0x97acc2,
                # color=0x2e4155
            )
            # await interaction.channel.send(content=reply, file=discord.File(fp=image_binary, filename='image.png'))
            await interaction.channel.send(embed=e, file=discord.File(fp=image_binary, filename='image.png'))



