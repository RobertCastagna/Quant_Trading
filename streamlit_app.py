import streamlit as st
import yfinance as yf
import numpy as np 
import matplotlib.pyplot as plt
import datetime as dt
import talib as ta 
import pandas as pd
import yfinance as yf
import sys
from backtesting import Strategy, Backtest
from backtesting.test import SMA
from datetime import date
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from st_pages import Page, show_pages
sys.path.insert(0, './other_pages')
from backtest import MACD, MeanReversion, SwingTrading, RsiOscillator

# pick security and time frame

show_pages(
    [
        Page("streamlit_app.py", "Home"),
        Page("other_pages/individual_strategy.py", "Backtest")
    ]
)

st.set_page_config(layout="wide")

ticker_options = pd.read_excel('indicators.xlsx')

options = ticker_options['tickers']

ticker = st.selectbox(
    'Which Security are we lookin at losing money on today?',
    (options))


# get only todays data and post dataframe of live open, close, etc..

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


# plotly graph

price_chart = go.Scatter(
    x=filtered_df.index,
    y=filtered_df.Close,
    name = '5 min price'
)

volume_bars = go.Bar(
    x=filtered_df.index,
    y=filtered_df['Volume'],
    showlegend=False,
    marker={
        "color": "lightsteelblue",
    }
)

fig_candle = go.Figure(price_chart)
fig_candle = make_subplots(specs=[[{"secondary_y": True}]])
fig_candle.add_trace(price_chart, secondary_y=True)
fig_candle.add_trace(volume_bars, secondary_y=False)
fig_candle.update_layout(
    title=dict(text=f"{ticker} Daily Data", font=dict(size=24), yref='paper')
)
st.plotly_chart(fig_candle, use_container_width=True, height=800)

# output securites basics for 2 day history
basics_data = yf.Ticker(ticker)
basics = basics_data.history(period='2d', interval='1d')
st.write("Securties Basics:")
st.dataframe(basics.sort_index(ascending=False), use_container_width = True)


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

# Calculate RSI, IBS, Gap
rsi_swing_window = SwingTrading.rsi_swing_window
open_pct_change = SwingTrading.open_pct_change
bar_limit = SwingTrading.bar_limit
rsi_limit = SwingTrading.rsi_limit
position_size = SwingTrading.position_size

def IBS(high, low, close):
    return pd.Series((close - low)/ (high - low))

st_close = indicator_data.Close
st_high = indicator_data.High
st_low = indicator_data.Low
st_open = indicator_data.Open

bar_strength = IBS(st_high, st_low, st_close)
st_rsi = ta.RSI(st_close, rsi_swing_window)
indicator_data['st_bar_strength'] = bar_strength
indicator_data['st_rsi'] = st_rsi


# build out indicator based trade signal buy/sell for each series of indicators 
indicator_data['Swing_trade_signal'] = ['buy' if (indicator_data.Close.iloc[-2]*(100-(open_pct_change/100)) >= indicator_data.Open.iloc[-1]) and (indicator_data.st_bar_strength.iloc[-2] < bar_limit/100) and (indicator_data.st_rsi.iloc[-2] < rsi_limit) else 'sell' if (indicator_data.Close.iloc[-1] < indicator_data.Close.iloc[-2] and indicator_data.Close.iloc[-2] < indicator_data.Close.iloc[-3]) else 'NaN' for col in indicator_data.index]
indicator_data['Rsi_trade_signal'] = ['buy' if indicator_data.RSI.iloc[-1] < RsiOscillator.lower_bound else 'sell' if indicator_data.RSI.iloc[-1] > RsiOscillator.upper_bound else 'NaN' for col in indicator_data.index]
indicator_data['MACD_trade_signal'] = ['buy' if (indicator_data.MACD.iloc[-2] <= 0 and indicator_data.MACD.iloc[-1] > 0) else 'sell' if (indicator_data.MACD.iloc[-2] >= 0 and indicator_data.MACD.iloc[-1] < 0) else 'NaN' for col in indicator_data.index]
indicator_data["Pct_Change_Close"] = indicator_data['Close'].pct_change()

# select key columns and format output dataframe
stock = indicator_data.set_index('Date')
stock_output = stock[['Rsi_trade_signal','Swing_trade_signal','MACD_trade_signal','Pct_Change_Close','RSI','MACD','st_rsi','st_bar_strength']].sort_index(ascending=False)

def highlight(col):
    if col.name == 'Rsi_trade_signal':
        for c in col.values:
            return ['background-color: red' if c == 'sell' else 'background-color: green' if c == 'buy' else '' for c in col.values]
            
    if col.name == 'MACD_trade_signal':
        for c in col.values:
            return ['background-color: red' if c == 'sell' else 'background-color: green' if c == 'buy' else '' for c in col.values]

    if col.name == 'Swing_trade_signal':
        for c in col.values:
            return ['background-color: red' if c == 'sell' else 'background-color: green' if c == 'buy' else '' for c in col.values]

st.write("Indicator-based trade signals for last 2 days:")
st.dataframe(stock_output[:2].style.apply(highlight), use_container_width = True) #
