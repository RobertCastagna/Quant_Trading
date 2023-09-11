import yfinance as yf
from backtesting import Strategy, Backtest
from backtesting.test import SMA
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import talib as ta
from backtesting.test import GOOG
import seaborn as sns

mpl.rcParams.update(mpl.rcParamsDefault)

import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter(action='ignore', category=FutureWarning)

# data imports 
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


def optim_func(series):
    if series['# Trades'] < 10:
        return -1
    return series["Equity Final [$]"] / series ["Exposure Time [%]"]


class RsiOscillator(Strategy):
    # above a value sell, below buy

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    position_size = 1

    def init(self):
        self.daily_rsi = self.I(ta.RSI, self.data.Close, self.rsi_window)
        self.weekly_rsi = resample_apply(
            "W-FRI", ta.RSI, self.data.Close, self.rsi_window
        )

    def next(self):
        
        price = self.data.Close[-1]

        if self.daily_rsi[-1] > self.upper_bound and barssince(self.daily_rsi < self.upper_bound) == 3:
            self.position.close()
        
        elif self.lower_bound > self.daily_rsi[-1]:
            self.buy(size = self.position_size)


bt = Backtest(GOOG, RsiOscillator, cash = 10000)

stats, heatmap = bt.optimize(
    upper_bound = range(55,85,5),
    lower_bound = range(10,45,5),
    rsi_window = 14,
    position_size = range(1, 10, 1),
    maximize = 'Sharpe Ratio',
    #constraint = lambda param: param.upper_bound > param.lower_bound,
    return_heatmap = True,
    max_tries = 100
)


bt.plot()
print(stats)
#print(heatmap)

#plot_heatmaps(heatmap, agg="mean")

#hm = heatmap.groupby(["upper_bound", "lower_bound"]).mean().unstack()
#sns.heatmap(hm, cmap = 'plasma')
#plt.show()



#bt = Backtest(he, MeanReversion, cash=10000, commission=0.002)
