import io
from PIL import Image
import matplotlib.pyplot as plt
import yfinance as yf



class TickerInfo:
    def __init__(self):
        self.log_file = "data/ticker.log"


    # def get_raw_ticker_data(self, ticker):
    #     try:
    #         t = yf.Ticker(ticker.upper())
    #         h = t.history(period="1mo")
    #         return h
    #     except Exception as e:
    #         self.


    def ticker_data(self, ticker):
        try:
            t = yf.Ticker(ticker.upper())
            h = t.history(period="1mo")
            day1 = h.iloc[0]
            day2 = h.iloc[-1]
            d1 = str(day1.name).split(" ")[0]
            d2 = str(day2.name).split(" ")[0]
            p1 = round(day1.Open, 2)
            p2 = round(day2.Close, 2)

            return (
                f"{ticker.upper()}:\n"
                f"{d1}: ${p1}\n"
                f"{d2}: ${p2}\n"
                f"Change: ${round(p2-p1, 2)} ({round(((p2-p1)/p2)*100, 2)}%)\n"
                f"Today's Volume: {round(day2.Volume)}\n"
                # f"More info will be coming to this response soon!"
            ), list(h.Open)

        except Exception as e:
            print(e)
            return "An error occurred, sorry"

    def get_img(self, y):
        plt.rcParams["figure.figsize"] = [2, .75]
        plt.rcParams["figure.autolayout"] = True

        plt.figure()
        plt.plot(y)
        plt.axis('off')
        return plt



if __name__ == '__main__':
    a = TickerInfo()
    x = a.ticker_data("msft")
    print(x)
