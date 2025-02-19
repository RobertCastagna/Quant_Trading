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
from other_pages.backtest import MACD, MeanReversion, SwingTrading, RsiOscillator
import subprocess
import sys
import os
if "openbb" not in os.listdir('./custom_package'):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--target=./custom_package", 'https://files.pythonhosted.org/packages/56/26/28d6c88f876d040ee8f3813a4c11eb54e5cecb3d57fe0a4b79908edd7817/openbb-4.1.3.tar.gz'])

sys.path.append('./custom_package')
from openbb import obb

# pick security and time frame

show_pages(
    [
        Page("streamlit_app.py", "Home"),
        Page("other_pages/individual_strategy.py", "Strategy"),
        Page("other_pages/analysis.py", "Correlation Tool"),
        Page("other_pages/portfolio_builder.py", "Watchlist")
    ]
)

st.set_page_config(layout="wide")

ticker_options = pd.read_excel('indicators.xlsx')

options = ticker_options[ticker_options['removed'] == False]['tickers']

ticker = st.selectbox(
    'Which security are we trading today?',
    (options))


# get only todays data and post dataframe of live open, close, etc..
today = dt.datetime.today()
current_date = dt.datetime.now().strftime("%Y-%m-%d")

obb.account.login(pat=st.secrets["open_bb_pat"])
ticker_prices = obb.equity.price.historical(symbol = "spy", provider="fmp", start_date=current_date, end_date=current_date, interval='5m').to_df()

todayData = ticker_prices.reset_index()

todayData['date'] = todayData['date'].dt.tz_localize(None) 
todayData['TimeOfDay'] = todayData['date'].apply(lambda x: pd.Timestamp(x))

filtered_df = todayData[todayData['date'] > today - dt.timedelta(1)]
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].dt.time
filtered_df['TimeOfDay'] = filtered_df['TimeOfDay'].apply(lambda x: str(x))
filtered_df = filtered_df.drop('date', axis = 1)


st.write(filtered_df['volume'], filtered_df['close'], filtered_df['close'].shape)

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    row_heights=[0.8, 0.2],  # ratio of top/bottom chart
    vertical_spacing=0.05    # spacing between the two subplots
)

fig.add_trace(
    go.Scatter(
        x=filtered_df['TimeOfDay'],
        y=filtered_df['close'][0].astype(float),
        name='Price',
        line=dict(color='blue')
    ),
    row=1, col=1
)

fig.add_trace(
    go.Bar(
        x=filtered_df['TimeOfDay'],
        y=filtered_df['volume'].astype(float),
        name='Volume',
        marker_color='green',
        opacity=0.8
    ),
    row=2, col=1
)

# 4) Update layout for clarity
fig.update_layout(
    title=f"{ticker} Daily Data",
    showlegend=False,
    height=800  
)

fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="Volume", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# output securites basics 
basics_data = yf.Ticker(ticker)
basics = basics_data.history(period='1d', interval='1d')[['Open','High','Low','Close','Volume']].reset_index().drop(['Date'], axis=1)
st.title("Securties Basics")
#perf_ratios = si.get_quote_table(ticker, dict_result=False).set_index('attribute').T[['PE Ratio (TTM)','Beta (5Y Monthly)','52 Week Range','Market Cap']].reset_index().drop(['index'], axis=1)
#st.dataframe(basics.join(perf_ratios).set_index('Open'), use_container_width = True)
st.dataframe(basics, use_container_width = True)

# get data for input security and timeframe
today = date.today() - dt.timedelta(90)
one_month_lag_date = today.strftime('%Y-%m-%d')

indicator_data = yf.download(ticker, start=one_month_lag_date)[
    ["Open", "High", "Low", "Close", "Volume"]
]#.reset_index()


# here, use indicator_data dataframe to calculate all indicators and pass daily trade signals to web

# Calculate RSI
macd, signal, hist = ta.MACD(indicator_data['Close'].to_numpy(), fastperiod=12, slowperiod=26, signalperiod=9)
daily_rsi = ta.RSI(indicator_data['Close'].to_numpy(), 14)
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

st.title("Indicator Based Signals")
st.dataframe(stock_output[:2].style.apply(highlight), use_container_width = True) #
