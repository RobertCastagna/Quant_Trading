import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# config parameters 
plt.style.use('fivethirtyeight')

# import ticker data through API wrapper 
msft = yf.Ticker("MSFT")

msft_df = pd.DataFrame(data = msft.history(period='6mo'))
#print(msft_df.columns)

def SMA(data, period = 30, column = 'Close'):
    return data[column].rolling(window=period).mean()

# create new columns for analysis 
msft_df['SMA'] = SMA(msft_df, 21)
msft_df['Simple_Returns'] = msft_df['Close'].ffill().pct_change(1)
msft_df['Log_Returns'] = np.log(1+msft_df['Simple_Returns'])
# if close price > SMA, ratio > 1, vise-versa
msft_df['Ratios'] = msft_df['Close'] / msft_df['SMA'] 

# analyse results 
#print(msft_df['Ratios'].describe())

# get and show percentile values
percentiles = [15,20,50,80,85]
ratios = msft_df['Ratios'].dropna()
pct_values = np.percentile(ratios, percentiles)

# plot the ratios
plt.figure(figsize=(14,7))
plt.title('Ratios')
plt.plot(ratios)
plt.axhline(pct_values[0], c='green', label = '15th percentile')
plt.axhline(pct_values[2], c='yellow', label = '50th percentile')
plt.axhline(pct_values[-1], c='red', label = '85th percentile')

#print(plt.show())

# create buy and sell signals for the strategy

sell = float(pct_values[-1]) # 85% threshold to sell
buy = float(pct_values[0]) # 15% threshold to buy 
print(buy, msft_df['Ratios'])

# put a -1 where ratio is greater than the percentile threshold to sell else nan 
msft_df['Positions'] = np.where(msft_df['Ratios'] > sell, -1, np.nan)
msft_df['Positions'] = np.where(msft_df['Ratios'] <= buy, 1, msft_df['Positions'])

print(msft_df[msft_df['Positions'] == 1])

msft_df['Buy'] = np.where(msft_df['Positions'] == 1, msft_df['Close'], np.nan)
msft_df['Sell'] = np.where(msft_df['Positions'] == -1, msft_df['Close'], np.nan)


# vis the results
plt.figure(figsize=(14,7))
plt.title('Close Price With Signals')
plt.plot(msft_df['Close'], alpha=0.5, label = 'Close')
plt.plot(msft_df['SMA'], alpha=0.5, label = 'SMA')
plt.scatter(msft_df.index, msft_df['Buy'], color = 'green', label = 'Buy Signal', marker ='^', alpha = 1)
plt.scatter(msft_df.index, msft_df['Sell'], color = 'red', label = 'Sell Signal', marker ='v', alpha = 1)
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.legend()
plt.show()

