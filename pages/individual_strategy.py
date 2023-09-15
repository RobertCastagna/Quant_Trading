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

# pick ticker and time interval
ticker_options = pd.read_excel('indicators.xlsx')

options = ', '.join(ticker_options['tickers'])

ticker = st.selectbox(
    'Which Security are we lookin at losing money on today?',
    (options))


lookback_duration = st.number_input("How many calendar days of history do you want to chart and test?", min_value=90, max_value=365, step=7)



# get data based on time interval until today
today = date.today() - dt.timedelta(lookback_duration)
one_month_lag_date = today.strftime('%Y-%m-%d')

stock = yf.download(ticker, start=one_month_lag_date)[
    ["Open", "High", "Low", "Close", "Volume"]
].reset_index()


# Calculate the RSI indicator 
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


# Plot RSI
fig_rsi, ax_rsi= plt.subplots()
plt.xticks(rotation=90)
ax_rsi.plot(stock['RSI'], label='RSI')
ax_rsi.set_xticklabels(labels=stock.index, fontdict={"fontsize": 8})
plt.legend()
ax_rsi.axhline(y=lower_bound, color='red', linestyle='--')
ax_rsi.axhline(y=upper_bound, color='green', linestyle='--')
st.pyplot(fig_rsi)

# Plot MACD
fig_macd, ax_macd= plt.subplots()
plt.xticks(rotation=90)
ax_macd.plot(stock['MACD'], label='MACD')
ax_macd.plot(stock['signal'], label='Signal')
ax_macd.bar(stock.index, stock['hist'], color = 'green', tick_label = stock.index)
ax_macd.set_xticklabels(labels=stock.index, fontdict={"fontsize": 8})
plt.legend()
ax_macd.axhline(y=0, color='black', linestyle='--')
st.pyplot(fig_macd)



