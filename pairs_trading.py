
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



msft = yf.download('MSFT', '2020-01-01', '2021-12-31')
aapl = yf.download('AAPL', '2020-01-01', '2021-12-31')
data = pd.concat([msft, aapl], axis=1)



def optim_func(series):
    if series['# Trades'] < 10:
        return -1
    return series["Equity Final [$]"] / series ["Exposure Time [%]"]


class PairsTradingStrategy(Strategy):

    def init(self):
        self.msft = self.data.MSFT
        self.aapl = self.data.AAPL
        self.spread = self.msft - self.aapl

    def next(self):
        if self.spread.crossed_above(0):
            self.buy('MSFT', 1)
            self.sell('AAPL', 1)
        elif self.spread.crossed_below(0):
            self.buy('AAPL', 1)
            self.sell('MSFT', 1)


bt = Backtest(data, PairsTradingStrategy, cash=100000, commission=0.001, exclusive_orders=True)

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


