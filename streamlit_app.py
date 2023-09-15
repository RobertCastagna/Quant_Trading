import streamlit as st
import yfinance as yf
import numpy as np 
import matplotlib.pyplot as plt
import datetime as dt
import talib as ta 
import pandas as pd
import yfinance as yf
from backtesting import Strategy, Backtest
from backtesting.test import SMA
from datetime import date
from backtest import MACD, MeanReversion, SwingTrading, RsiOscillator

# pick security and time frame

ticker_options = pd.read_excel('indicators.xlsx')

options = ticker_options['tickers']

ticker = st.selectbox(
    'Which Security are we lookin at losing money on today?',
    (options))




# get only todays data and post dataframe of live open, close, etc..

tickerData = yf.Ticker(ticker)
Data = tickerData.history(period='2d')

todayData = Data.reset_index()

todayData['Datetime'] = todayData['Datetime'].dt.tz_localize(None) 
todayData['TimeOfDay'] = todayData['Datetime'].apply(lambda x: pd.Timestamp(x))

today = dt.datetime.today()
filtered_df = todayData[todayData['Datetime'] > today - dt.timedelta(2)]
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].dt.time
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].apply(lambda x: str(x))
filtered_df = filtered_df.set_index('TimeOfDay').drop('Datetime', axis = 1)

daily_output_data = filtered_df.T
print(daily_output_data)
st.dataframe(daily_output_data)

fig, ax1= plt.subplots()
plt.title(f"Today's {ticker} Data")
plt.style.use('fivethirtyeight')
plt.xticks(rotation=90)
ax1.set_xticklabels(labels=filtered_df.index, fontdict={"fontsize": 5})
ax1.plot(filtered_df['Close'])

st.pyplot(fig)



# get data for input security and timeframe

today = date.today() - dt.timedelta(90)
one_month_lag_date = today.strftime('%Y-%m-%d')

indicator_data = yf.download(ticker, start=one_month_lag_date)[
    ["Open", "High", "Low", "Close", "Volume"]
].reset_index()

# here, use indicator_data dataframe to calculate all indicators and pass daily trade signals to web

# Calculate RSI
macd, signal, hist = ta.MACD(indicator_data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
daily_rsi = ta.RSI(indicator_data['Close'], 14)
upper_bound = RsiOscillator.upper_bound
lower_bound = RsiOscillator.lower_bound
indicator_data['RSI'] = daily_rsi

# Add the MACD indicator 
indicator_data['MACD'] = macd
indicator_data['signal'] = signal
indicator_data['hist'] = hist

indicator_data['Date'] = indicator_data['Date'].dt.tz_localize(None) 
indicator_data['Date'] = indicator_data['Date'].apply(lambda x: pd.Timestamp(x))
indicator_data['Date'] = indicator_data['Date'].dt.date
stock = indicator_data.set_index('Date')
st.dataframe(stock[['RSI','MACD']])












