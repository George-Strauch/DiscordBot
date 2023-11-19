import datetime

import pandas as pd
import discord
from ..functions.finance import TickerInfo
from ..utils import log_events, theme_colors
import matplotlib.pyplot as plt
from PIL import Image
import io


class FinanceBll:
    def __init__(self):
        # self.bot = bot
        self.log_file = "/opt/bot/data/finance.log"
        self.ticker_info = TickerInfo()
        periods = ["1d" "5d", "1mo", "3mo", "6mo", "5y", "ytd", "max"]


    def send_ticker_price(
            self,
            tickers: list,
            period: str = "1mo"
    ):
        """
        :param tickers: list of tickers, indexes like dji and spx need to be prefixed with '^' ex: ^dji and ^spx
        :param period: the period of time we are viewing the price over:
         ["1d" "5d", "1mo", "3mo", "6mo", "5y", "ytd", "max"]
        :return: content sent to discord
        """
        ticker_data = self.ticker_info.get_ticker_price_data(tickers, period=period)
        print(ticker_data)
        if "error" in ticker_data:
            # todo log
            return {
                "content": "I am having trouble getting information about those tickers at the moment"
            }
        else:
            for i, k in enumerate(ticker_data.keys()):
                ticker_data[k]["color"] = theme_colors[i]
            picture_plot = self._get_plt(ticker_data)
            with io.BytesIO() as image_binary:
                picture_plot.savefig(image_binary, format='PNG', bbox_inches='tight', pad_inches=0, transparent=True)
                pillow_image = Image.open(image_binary)
                im_flipped = pillow_image.transpose(method=Image.FLIP_LEFT_RIGHT)

            with io.BytesIO() as image_binary:
                im_flipped.save(image_binary, format='PNG')
                image_binary.seek(0)
                embeds = [
                    self._finance_embed(x, k)
                    for k, x in ticker_data.items()
                ]
                return {
                    "embeds": embeds,
                    "file": discord.File(fp=image_binary, filename='image.png')
                }

    def get_financial_statements(self, tickers: list, fields: list = []):
        try:
            response = self.ticker_info.get_financial_data(tickers=tickers)
            if not response:
                return {
                    "error": "An issue occurred getting ticker data from api"
                }
            ret_data = {}
            for ticker in response.tickers.values():
                ret_data[ticker.ticker] = {}
                cashflow = ticker.quarterly_cashflow
                cash_flow_data = {"dates": None}
                for key, row in cashflow.iterrows():
                    if cash_flow_data["dates"] is None:
                        dates = row.keys().values
                        dates = [pd.to_datetime(str(x)).strftime('%Y-%m-%d') for x in dates]
                        cash_flow_data["dates"] = dates
                    if key in fields:
                        cash_flow_data[key] = row.to_list()
                if len(cash_flow_data) > 1:
                    ret_data[ticker.ticker]["cashflow"] = cash_flow_data

                bs = ticker.quarterly_balance_sheet
                bs_data = {"dates": None}
                for key, row in bs.iterrows():
                    if bs_data["dates"] is None:
                        dates = row.keys().values
                        dates = [pd.to_datetime(str(x)).strftime('%Y-%m-%d') for x in dates]
                        bs_data["dates"] = dates
                    if key in fields:
                        bs_data[key] = row.to_list()

                if len(bs_data) > 1:
                    ret_data[ticker.ticker]["balance_sheet"] = bs_data

                if "earnings_dates" in fields:
                    dates = ticker.earnings_dates.T.keys().values
                    earnings_dates = [pd.to_datetime(str(x)).strftime('%Y-%m-%d') for x in dates]
                    ret_data[ticker.ticker]["earnings_dates"] = list(set(earnings_dates))
            return ret_data
        except Exception as ex:
            return {"Errors": "errors occurred when getting information for the provided tickers"}


    def _finance_embed(self, ticker_data, t_name):
        p1 = ticker_data['prices'][0]
        p2 = ticker_data['prices'][-1]
        interval = ticker_data['interval']
        wsp = "\u200b "

        e = discord.Embed(
            title=f"{t_name.upper()}\t\t$ **`{p2:.2f}`**",
            # description=f"``{ticker_data['embed_str']}``",
            color=int(ticker_data["color"].replace("#", ""), base=16)
        )
        dt = datetime.datetime.now() - ticker_data['date_times'][0]
        dt_units = round(dt.total_seconds())//60
        time_frame = "Minute"
        if dt_units // 60 > 0:
            time_frame = "Hour"
            dt_units = dt_units//60
            if dt_units // 24 > 0:
                time_frame = "Day"
                dt_units = dt_units // 24
                if dt_units // 7 > 0:
                    time_frame = "Week"
                    dt_units = dt_units // 7

        if dt_units > 1 or dt_units == 0:
            time_frame = f"{time_frame}s"

        e.insert_field_at(
            1,
            name=f"{ticker_data['dates'][0]} [{dt_units} {time_frame} Ago]",
            value=f"```${p1:.2f}\nΔ ${p2-p1:.2f} ({((p2-p1)/p1)*100:.2f})%```",
            inline = False
        )
        e.insert_field_at(
            2,
            name=f"Volume",
            value=f"```{str(round(ticker_data['volume'][-1])).ljust(18, ' ')}```",
            inline=False
        )
        e.insert_field_at(
            3,
            name=f"Time Frame",
            value=f"```Total Period: {ticker_data['period']}\nIntervals: {ticker_data['interval']}```",
            inline=False
        )
        e.set_footer(text=f"Source: YFinance")
        return e

    def _get_plt(self, tickers):
        # todo reverse then invert
        fig, ax = plt.subplots(figsize=(4.1/3, 1/3), dpi=300)
        # fig.yscale("log")
        for t, tdata in tickers.items():
            prices = list(reversed(tdata["prices"]))
            norm = prices[-1]
            prices = [x/norm for x in prices]
            ax.plot(prices, linewidth=.5, color=tdata["color"])
            base = [1]*len(prices)
            ax.plot(base, linewidth=.1, color="#000000", alpha=0.2)
        ax.axis('off')
        return fig
