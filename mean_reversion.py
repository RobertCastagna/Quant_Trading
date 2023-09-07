import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# config parameters 
plt.style.use('fivethirtyeight')


def SMA(data, period = 30, column = 'Close'):
    return data[column].rolling(window=period).mean()

def mean_reversion(ticker, history = '6mo', sma_interval = 21):
    # retrieve data
    stock_data = yf.Ticker(ticker)
    mr_df = pd.DataFrame(data = stock_data.history(period=history))

    # calculate columns
    mr_df['SMA'] = SMA(mr_df, sma_interval)
    mr_df['Simple_Returns'] = mr_df['Close'].ffill().pct_change(1)
    mr_df['Log_Returns'] = np.log(1 + mr_df['Simple_Returns'])

    # if close price > SMA, ratio > 1, vise-versa
    mr_df['Ratios'] = mr_df['Close'] / mr_df['SMA'] 
    
    # get percentile values
    percentiles = [15,20,50,80,85]
    ratios = mr_df['Ratios'].dropna()
    pct_values = np.percentile(ratios, percentiles)
    
    # create buy and sell signals for the strategy
    sell = float(pct_values[-1]) # 85% threshold to sell
    buy = float(pct_values[0]) # 15% threshold to buy 

    # put a -1 where ratio is greater than the percentile threshold to sell else nan 
    mr_df['Positions'] = np.where(mr_df['Ratios'] > sell, -1, np.nan)
    mr_df['Positions'] = np.where(mr_df['Ratios'] <= buy, 1, mr_df['Positions'])

    mr_df['Buy'] = np.where(mr_df['Positions'] == 1, mr_df['Close'], np.nan)
    mr_df['Sell'] = np.where(mr_df['Positions'] == -1, mr_df['Close'], np.nan)

    return mr_df

result = mean_reversion("MSFT")


# vis the results
plt.figure(figsize=(14,7))
plt.title('Close Price With Signals')
plt.plot(result['Close'], alpha=0.5, label = 'Close')
plt.plot(result['SMA'], alpha=0.5, label = 'SMA')
plt.scatter(result.index, result['Buy'], color = 'green', label = 'Buy Signal', marker ='^', alpha = 1)
plt.scatter(result.index, result['Sell'], color = 'red', label = 'Sell Signal', marker ='v', alpha = 1)
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.legend()
plt.show()

