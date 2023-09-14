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

# What I want to do:
#   have the app take in a stock ticker from our list (read an xlsx sheet mitch made)

ticker = st.selectbox(
    'Which Security are we lookin at losing money on today?',
    ('MSFT', 'GOOG', 'AAPL'))

tickerData = yf.Ticker(ticker)
Data = tickerData.history(period='30d',interval='5m')

todayData = Data.reset_index()
todayData = todayData[['Datetime','Close']]

todayData['Datetime'] = todayData['Datetime'].dt.tz_localize(None) 
todayData['TimeOfDay'] = todayData['Datetime'].apply(lambda x: pd.Timestamp(x))

today = dt.datetime.today()
filtered_df = todayData[todayData['Datetime'] > today - dt.timedelta(1)]
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].dt.time
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].apply(lambda x: str(x))
filtered_df = filtered_df.set_index('TimeOfDay').drop('Datetime', axis = 1)

fig, ax1= plt.subplots()
plt.title(f"Today's {ticker} Data")
plt.style.use('fivethirtyeight')
plt.xticks(rotation=90)
ax1.set_xticklabels(labels=filtered_df.index, fontdict={"fontsize": 5})
ax1.plot(filtered_df['Close'])

st.pyplot(fig)


#   this will be the run through each of our strategies and a coloured button will be green or red if it has shown a buy signal on the day

lookback_duration = st.number_input("How many calendar days of history do you want to chart and test?", min_value=90, max_value=365, step=7)

today = date.today() - dt.timedelta(lookback_duration)
one_month_lag_date = today.strftime('%Y-%m-%d')

stock = yf.download(ticker, start=one_month_lag_date)[
    ["Open", "High", "Low", "Close", "Volume"]
].reset_index()

rsi_stock = yf.download(ticker, start=one_month_lag_date)[
    ["Open", "High", "Low", "Close", "Volume"]
].reset_index()

# Calculate the MACD indicator using TA-Lib
macd, signal, hist = ta.MACD(stock['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
daily_rsi = ta.RSI(rsi_stock['Close'], 14)
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


strat = st.selectbox("pick a strategy:", ('','SwingTrading', 'MACD', 'MeanReversion', 'RsiOscillator'))
if st.button(f"Backtest from {stock.index[0]} to {stock.index[-1]}"):

    if strat == 'SwingTrading':
        bt = Backtest(stock, SwingTrading, commission=0.002, cash=100000)
        stats = bt.run()
        st.dataframe(pd.DataFrame(stats['_trades']).drop('Duration', axis = 1))

    if strat == 'MACD':
            bt = Backtest(stock, MACD, commission=0.002, cash=100000)
            stats = bt.run()
            st.dataframe(pd.DataFrame(stats['_trades']).drop('Duration', axis = 1))

    if strat == 'MeanReversion':
            bt = Backtest(stock, MeanReversion, commission=0.002, cash=100000)
            stats = bt.run()
            st.dataframe(pd.DataFrame(stats['_trades']).drop('Duration', axis = 1))

    if strat == 'RsiOscillator':
            bt = Backtest(stock, RsiOscillator, commission=0.002, cash=100000)
            stats = bt.run()
            st.dataframe(pd.DataFrame(stats['_trades']).drop('Duration', axis = 1))

    st.write("raw output of backtest stats:")
    st.write(stats)

