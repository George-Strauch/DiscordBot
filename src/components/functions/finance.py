import io
import json
import traceback

from PIL import Image
import matplotlib.pyplot as plt
import yfinance as yf



class TickerInfo:
    def __init__(self):
        self.log_file = "data/ticker.log"


    def get_raw_ticker_data(self, tickers, period="1mo"):
        # intervals = "1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo"
        # periods = ["1d" "5d", "1mo", "3mo", "6mo", "5y", "ytd", "max"]
        print(tickers, period)
        intervals = {
            "1d": "15m",
            "5d": "1h",
            "1mo": "90m",
            "3mo": "1d",
            "6mo": "5d",
            "1y": "1wk",
            "5y": "1mo",
            "max": "3mo",
        }
        print("params ", tickers, period, intervals.get(period))

        try:
            str_adjust = 15
            data = {}
            tiks = yf.Tickers(tickers)
            for t_n, t_v in tiks.tickers.items():
                h = t_v.history(period=period, interval=intervals.get(period, "1d"))
                h = h.iloc
                this_tickers_data = {
                    "dates": [],
                    "prices": [],
                    "volume": [],
                    "embed_str": ""
                }
                for instant in list(h):
                    t_ = str(instant.name).split(" ")
                    if period == "1d":
                        t_ = t_[1].split("-")[0]
                        t_ = t_.ljust(str_adjust, " ")
                    else:
                        t_ = t_[0].ljust(str_adjust, " ")
                    this_tickers_data["dates"].append(t_)
                    this_tickers_data["prices"].append(instant.Open)
                    this_tickers_data["volume"].append(instant.Volume)

                p1 = this_tickers_data['prices'][0]
                p2 = this_tickers_data['prices'][-1]
                this_tickers_data["embed_str"] = (
                    f"{this_tickers_data['dates'][0]} ${p1:.2f}\n"
                    f"{this_tickers_data['dates'][-1]} ${p2:.2f}\n"
                    f"{'Δ'.ljust(str_adjust, ' ')} ${p2-p1:.2f} ({((p2-p1)/p2)*100:.2f}%)\n"
                    f"{'Volume'.ljust(str_adjust, ' ')} {round(this_tickers_data['volume'][-1])}\n"
                )
                data[t_n.upper()] = this_tickers_data
            return data
        except Exception as e:
            print(str(e.args))
            print(traceback.format_exc())
            return {"error": "There was an issues with the query"}




    def get_plt(self, tickers):
        # todo reverse then invert
        fig, ax = plt.subplots(figsize=(3.9/3, 1/3), dpi=300)
        # fig.yscale("log")
        for t, tdata in tickers.items():

            prices = list(reversed(tdata["prices"]))
            norm = prices[-1]
            prices = [x/norm for x in prices]
            ax.plot(prices, linewidth=.5, color=tdata["color"])
        ax.axis('off')
        return fig


if __name__ == '__main__':
    ti = TickerInfo()
    tickers = ["msft", "goog"]
    a = ti.get_raw_ticker_data(tickers, period="1mo")
    for t, v in a.items():
        print(t)
        print(v["embed_str"])

    # print(json.dumps(a, indent=4))


    # f = ti.get_plt(a)
    # f.show()
    # print(a)
