import logging
import traceback

import yfinance as yf

logger = logging.getLogger(__name__)


class TickerInfo:
    def __init__(self):
        pass

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
            data = {}
            tiks = yf.Tickers(tickers)
            for t_n, t_v in tiks.tickers.items():
                h = t_v.history(period=period, interval=intervals.get(period, "1d"))
                h = h.iloc
                this_tickers_data = {
                    "dates": [],
                    "date_times": [],
                    "prices": [],
                    "volume": [],
                    "embed_str": "",
                    "interval": intervals.get(period, "1d"),
                    "period": period,
                }
                str_adjust = 15
                for instant in list(h):
                    _dt = str(instant.name).split(" ")
                    if period == "1d":
                        t_ = _dt[1].split("-")[0][:-3] + " EST"
                        t_ = t_.ljust(str_adjust, " ")
                    else:
                        t_ = _dt[0].ljust(str_adjust, " ")
                    this_tickers_data["dates"].append(t_)
                    this_tickers_data["prices"].append(instant.Close)
                    this_tickers_data["volume"].append(instant.Volume)
                    this_tickers_data["date_times"].append(instant.name.replace(tzinfo=None))
                data[t_n.upper()] = this_tickers_data
            return data
        except Exception as e:
            logger.exception("Error getting ticker price data")
            return {"error": "There was an issue with the query"}

    def get_financial_data(self, tickers: list):
        try:
            return yf.Tickers(tickers)
        except Exception:
            return None
