import yfinance as yf
from backtesting import Strategy, Backtest
from backtesting.test import SMA
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import talib as ta
import numpy as np
from backtesting.test import GOOG
import seaborn as sns

mpl.rcParams.update(mpl.rcParamsDefault)

import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter(action='ignore', category=FutureWarning)

# data imports 
# he = yf.download("he", start="2023-08-07", interval="15m")[
#     ["Open", "High", "Low", "Close", "Volume"]
# ]

# stock = yf.download("he", start="2022-10-16")[
#     ["Open", "High", "Low", "Close", "Volume"]
# ]



class MACD(Strategy):
    # when macd crosses 0 from above, bear indication & vice-versa
    macd_fast = 12
    macd_slow = 26
    position_size = 50
    tp_over_macd = 10
    tp_under_macd = 10


    
    def init(self):
        def zero_line(arr):
            return np.full_like(arr, 0)
        
        self.macd_close = self.data.Close
        self.macd_values, self.macd_signal, self.macd_hist = self.I(ta.MACD, self.macd_close, self.macd_fast, self.macd_slow)
        self.zero = self.I(zero_line, self.macd_close)

    def next(self):
        price = self.data.Close

        # macd crossing zero from above, short stock 
        if crossover(self.zero, self.macd_values):
            self.position.close()
            self.sell(size = self.position_size)
        
        # if a short exists and macd stays below zero for 5 consecutive days, close short position
        if self.position.is_short and barssince(self.macd_values > 0) == self.tp_over_macd:
            self.position.close()
        elif self.position.is_long and barssince(self.macd_values < 0) == self.tp_under_macd:
            self.position.close()

        # crossing from below zero line, buy stock
        if crossover(self.macd_values, self.zero):
            self.buy(size = self.position_size)


class SwingTrading(Strategy):

    rsi_swing_window = 5
    open_pct_change = 250 #2.5%
    bar_limit = 25
    rsi_limit = 45
    position_size = 1

    def init(self):
        def IBS(high, low, close):
            return pd.Series((close - low)/ (high - low))
        
        self.st_close = self.data.Close
        self.st_high = self.data.High
        self.st_low = self.data.Low
        self.st_open = self.data.Open

        self.bar_strength = self.I(IBS, self.st_high, self.st_low, self.st_close)
        self.st_rsi = self.I(ta.RSI, self.st_close, self.rsi_swing_window)

    def next(self):
        price = self.data.Close[-1]

        ## PREDICTS A RUN UP, AFTER A GAP DOWN ON THE PREVIOUS DAY
        # if sp gap down by a given %, yesterdays IBS 0.25 or lower, yesterdays RSI 45 or lower
        # then buy open
        if (self.st_close[-2]*(100-(self.open_pct_change/100)) >= self.st_open[-1]) and (self.bar_strength[-2] < self.bar_limit/100) and (self.st_rsi[-2] < self.rsi_limit):
            self.buy(size = self.position_size)

        # exit if the close is higher than yesterdays close
        if self.st_close[-1] < self.st_close[-2]:
            self.position.close()


class MeanReversion(Strategy):

    roll = 50
    
    
    def init(self):
        
        def std_3(arr, n):
            return pd.Series(arr).rolling(n).std() * 2
        
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


class RsiOscillator(Strategy):
    # above a value sell, below buy

    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    position_size = 1

    def init(self):
        self.daily_rsi = self.I(ta.RSI, self.data.Close, self.rsi_window)

    def next(self):
        
        price = self.data.Close[-1]

        if self.daily_rsi[-1] > self.upper_bound and barssince(self.daily_rsi < self.upper_bound) == 3:
            self.sell(size = self.position_size)
            self.position.close()
        
        elif self.lower_bound > self.daily_rsi[-1]:
            self.buy(size = self.position_size)



def optim_func(series):
    if series['# Trades'] < 10:
        return -1
    return series["Equity Final [$]"] / series ["Exposure Time [%]"]

#bt = Backtest(stock, SwingTrading, commission = 0.002, cash = 100000)

# #stats = bt.optimize(
#     tp_over_macd = range(5,20,1),
#     tp_under_macd = range(5,20,1),
#     position_size = range(25,100,5),
#     maximize = optim_func,
#     #constraint = lambda param: param.macd_fast < param.macd_slow,
#     #return_heatmap = True,
#     max_tries = 200
# )

#stats = bt.run()
# bt.plot()
# print(stats)

#print(heatmap)

#plot_heatmaps(heatmap, agg="mean")

#hm = heatmap.groupby(["upper_bound", "lower_bound"]).mean().unstack()
#sns.heatmap(hm, cmap = 'plasma')
#plt.show()
