import yfinance as yf
from backtesting import Strategy, Backtest
from backtesting.test import SMA
from backtesting.lib import crossover
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas_ta as ta

mpl.rcParams.update(mpl.rcParamsDefault)

import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter(action='ignore', category=FutureWarning)


he = yf.download("AAPL", start="2023-08-07", interval="15m")[
    ["Open", "High", "Low", "Close", "Volume"]
]

def std_3(arr, n):
    return pd.Series(arr).rolling(n).std() * 3

class MeanReversion(Strategy):
    roll = 50

    def init(self):
        self.he = self.data.Close

        self.he_mean = self.I(SMA, self.he, self.roll)
        self.he_std = self.I(std_3, self.he, self.roll)
        self.he_upper = self.he_mean + self.he_std
        self.he_lower = self.he_mean - self.he_std

        self.he_close = self.I(SMA, self.he, 1)

    def next(self):

        if self.he_close < self.he_lower:
            self.buy(
                tp = self.he_mean,
            )
            
        if self.he_close > self.he_upper:
            self.sell(
                tp = self.he_mean,
            )

macd = ta.macd(close=he['Close'])
print(macd)


#bt = Backtest(he, MeanReversion, cash=10000, commission=0.002)
#stats = bt.run()
#bt.plot()
#print(stats)

