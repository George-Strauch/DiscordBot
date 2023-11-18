import traceback
import matplotlib.pyplot as plt
import yfinance as yf


class TickerInfo:
    def __init__(self):
        self.log_file = "/opt/bot/data/ticker.log"


    def get_ticker_price_data(self, tickers, period="1mo"):
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
                    "embed_str": "",
                    "interval": intervals.get(period, "1d")
                }
                for instant in list(h):
                    t_ = str(instant.name).split(" ")
                    if period == "1d":
                        t_ = t_[1].split("-")[0][:-3] + " EST"
                        t_ = t_.ljust(str_adjust, " ")
                    else:
                        t_ = t_[0].ljust(str_adjust, " ")
                    this_tickers_data["dates"].append(t_)
                    this_tickers_data["prices"].append(instant.Close)
                    this_tickers_data["volume"].append(instant.Volume)
                data[t_n.upper()] = this_tickers_data
            return data
        except Exception as e:
            print(str(e.args))
            print(traceback.format_exc())
            return {"error": "There was an issues with the query"}





if __name__ == '__main__':
    pass
