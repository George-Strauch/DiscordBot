import base64
import json

import discord
from discord.ext import commands
from discord import app_commands
from .functions.finance import TickerInfo
from .utils import log_events, chunk_message, theme_colors, blank_px
from PIL import Image
import io



class Finance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "data/finance.log"
        self.ticker_info = TickerInfo()
        # periods = ["1d" "5d", "1mo", "3mo", "6mo", "5y", "ytd", "max"]

    @app_commands.command(name="ticker")
    @app_commands.describe(tickers="Stock Tickers (up to 5) (seperated by single space if multiple are provided)"
                                   "For special tickers use ^ (^dji)"
                                   "For crypto you must specify exchange currency, (ex btc-usd)")
    @app_commands.describe(period="Period of time over which you want to show data")
    @app_commands.choices(period=[
        discord.app_commands.Choice(name="1 Day", value="1d"),
        discord.app_commands.Choice(name="5 Day", value="5d"),
        discord.app_commands.Choice(name="1 Month", value="1mo"),
        discord.app_commands.Choice(name="3 Month", value="3mo"),
        discord.app_commands.Choice(name="6 Month", value="6mo"),
        discord.app_commands.Choice(name="1 Year", value="1y"),
        discord.app_commands.Choice(name="5 Year", value="5y"),
        discord.app_commands.Choice(name="MAX", value="max"),
    ])
    async def get_ticker_info(
            self,
            interaction: discord.Interaction,
            tickers: str,
            period: discord.app_commands.Choice[str] = "1mo"
    ):
        """
        Get info for stock ticker(s)
        """
        if not isinstance(period, str):
            period = period.value
        tickers = tickers.split(" ")
        log_events(f"[{interaction.user.name}] WANTS TO GET TICKER DATA FOR: {tickers}", self.log_file)
        await interaction.response.send_message("Working on that, one sec ...")
        ticker_data = self.ticker_info.get_raw_ticker_data(tickers, period=period)  # todo
        print(ticker_data)
        if "error" in ticker_data:
            await interaction.edit_original_response(content="I am having trouble with that at the moment")
        else:
            for i, k in enumerate(ticker_data.keys()):
                ticker_data[k]["color"] = theme_colors[i]
            picture_plot = self.ticker_info.get_plt(ticker_data)
            with io.BytesIO() as image_binary:
                picture_plot.savefig(image_binary, format='PNG', bbox_inches='tight', pad_inches=0, transparent=True)
                pillow_image = Image.open(image_binary)
                im_flipped = pillow_image.transpose(method=Image.FLIP_LEFT_RIGHT)

            with io.BytesIO() as image_binary:
                im_flipped.save(image_binary, format='PNG')
                image_binary.seek(0)
                embeds = [
                    self.finance_embed(x, k)
                    for k, x in ticker_data.items()
                ]
                await interaction.channel.send(embeds=embeds, file=discord.File(fp=image_binary, filename='image.png'))


    def finance_embed(self, ticker_data, t_name):
        p1 = ticker_data['prices'][0]
        p2 = ticker_data['prices'][-1]
        interval = ticker_data['interval']
        wsp = "\u200b "

        e = discord.Embed(
            title=f"{t_name.upper()}\t\t$ **`{p2:.2f}`**",
            # description=f"``{ticker_data['embed_str']}``",
            color=int(ticker_data["color"].replace("#", ""), base=16)
        )
        e.insert_field_at(
            1,
            name=f"{ticker_data['dates'][0]}",
            value=f"```${p1:.2f}\nΔ ${p2-p1:.2f} ({((p2-p1)/p1)*100:.2f})%```",
            inline = True
        )
        e.insert_field_at(
            2,
            name=f"Volume (over {interval} period)",
            value=f"```{str(round(ticker_data['volume'][-1])).ljust(18, ' ')}```",
            inline=False
        )
        e.set_footer(text=f"Source: YFinance")

        return e
