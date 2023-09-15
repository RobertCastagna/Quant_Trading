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

lookback_duration = st.number_input("How many calendar days of history do you want to chart and test?", min_value=90, max_value=365, step=7)

# get data for that security and timeframe

today = date.today() - dt.timedelta(lookback_duration)
one_month_lag_date = today.strftime('%Y-%m-%d')

stock = yf.download(ticker, start=one_month_lag_date)[
    ["Open", "High", "Low", "Close", "Volume"]
].reset_index()

st.dataframe(stock)

# also get only todays data and post dataframe of live open, close, etc..

tickerData = yf.Ticker(ticker)
Data = tickerData.history(period='2d',interval='5m')

todayData = Data.reset_index()

todayData['Datetime'] = todayData['Datetime'].dt.tz_localize(None) 
todayData['TimeOfDay'] = todayData['Datetime'].apply(lambda x: pd.Timestamp(x))

today = dt.datetime.today()
filtered_df = todayData[todayData['Datetime'] > today - dt.timedelta(1)]
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].dt.time
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].apply(lambda x: str(x))
filtered_df = filtered_df.set_index('TimeOfDay').drop('Datetime', axis = 1)

st.dataframe(filtered_df)

fig, ax1= plt.subplots()
plt.title(f"Today's {ticker} Data")
plt.style.use('fivethirtyeight')
plt.xticks(rotation=90)
ax1.set_xticklabels(labels=filtered_df.index, fontdict={"fontsize": 5})
ax1.plot(filtered_df['Close'])

st.pyplot(fig)


#  this will be the run through each of our strategies and a coloured button will be green or red if it has shown a buy signal on the day




# Calculate the indicators using TA-Lib
macd, signal, hist = ta.MACD(stock['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
daily_rsi = ta.RSI(stock['Close'], 14)
upper_bound = RsiOscillator.upper_bound
lower_bound = RsiOscillator.lower_bound
stock['RSI'] = daily_rsi

# Add the MACD indicator to the DataFrame
stock['MACD'] = macd
stock['signal'] = signal
stock['hist'] = hist

stock['Date'] = stock['Date'].dt.tz_localize(None) 
stock['Date'] = stock['Date'].apply(lambda x: pd.Timestamp(x))
stock['Date'] = stock['Date'].dt.date
#stock = stock[stock['MACD'].notna()]
stock = stock.set_index('Date')

st.dataframe(stock)
