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
import math
from scipy.stats import norm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from st_pages import Page, show_pages
sys.path.insert(0, './other_pages')
from backtest import MACD, MeanReversion, SwingTrading, RsiOscillator

# pick security and time frame

show_pages(
    [
        Page("streamlit_app.py", "Home"),
        Page("other_pages/individual_strategy.py", "Strategy"),
        Page("other_pages/portfolio_builder.py", "Watchlist")
    ]
)

st.set_page_config(layout="wide")

# pick ticker and time interval
ticker_options = pd.read_excel('indicators.xlsx')

options = ticker_options[ticker_options['removed'] == False]['tickers']

ticker = st.selectbox(
    'Which Security are we lookin at losing money on today?',
    (options))


# ------------------------------- Options Pricing ----------------------------------------- #

st.title("Options Pricing")

col1, col2, col3 = st.columns([1,1,1])

with col1:
    pricing_model = st.selectbox(
    'Which Pricing Model?',
    (['Black Scholes','Binomial'])
)
    
with col2:
    strike_price = st.number_input("Enter Strike Price", min_value=0.00, max_value=2000.00, step=1.,format="%.2f")
with col3:
    time_to_expiration = st.date_input("Enter Expiration Date", dt.date.today() + dt.timedelta(30))

today = date.today() - dt.timedelta(365)
stock = yf.download(ticker, start=today.strftime('%Y-%m-%d'))[["Close"]]

if pricing_model == 'Black Scholes':
    # get underlying asset price and calculate stdev.
    
    S = stock["Close"].iloc[-1:].values[0]   # underlying asset price
    K = strike_price 
    time_delta = time_to_expiration - dt.date.today()
    T = (time_delta.total_seconds() / 86400.0) / 365.0
    r = 0.03997 # risk-free rate:  [{"country": "United States", "type": "CPI", "period": "august 2023", "monthly_rate_pct": 0.437, "yearly_rate_pct": 3.665}]
                                # [{"country": "Canada", "type": "CPI", "period": "august 2023", "monthly_rate_pct": 0.38, "yearly_rate_pct": 3.997}]
    vol = stock['Close'].std() # volatility (sigma)


    # Black Scholes Option Pricing

    d1 = (math.log(S/K) + T*(r + 0.5 * vol**2)) / (vol * math.sqrt(T))
    d2 = d1 - vol*math.sqrt(T)

    # caculate call option price
    C = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)

    # calculate put option price 
    P = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    C = np.round(C,2)
    P = np.round(P,2)

if pricing_model == 'Binomial':
    S = stock["Close"].iloc[-1:].values[0]       # initial stock price
    K = strike_price  
    time_delta = time_to_expiration - dt.date.today()
    T = (time_delta.total_seconds() / 86400.0) / 365.0       # time to maturity in years
    r = 0.03997 # risk-free rate:  [{"country": "United States", "type": "CPI", "period": "august 2023", "monthly_rate_pct": 0.437, "yearly_rate_pct": 3.665}]
                                # [{"country": "Canada", "type": "CPI", "period": "august 2023", "monthly_rate_pct": 0.38, "yearly_rate_pct": 3.997}]
    N = 5000      # number of time steps
    u = 1.1       # up-factor in binomial models
    d = 1/u       # ensure recombining tree

    def binomial_tree_fast(K, T, S0, r, N, u, d, opttype):
        #precompute constants
        dt = T/N
        q = (np.exp(r*dt) - d) / (u-d)
        disc = np.exp(-r*dt)
        
        # initialise asset prices at maturity - Time step N
        C = S * d ** (np.arange(N,-1,-1)) * u ** (np.arange(0,N+1,1)) 
        
        # initialise option values at maturity
        C = np.maximum( C - K , np.zeros(N+1) )
            
        # step backwards through tree
        for i in np.arange(N,0,-1):
            C = disc * ( q * C[1:i+1] + (1-q) * C[0:i] )

        return np.round(C[0], 2)
    
    C = binomial_tree_fast(K,T,S,r,N,u,d,opttype='C')
    P = '..only built for calls.. sry'

st.write(f"Current Price: {np.round(S,2)}")
st.write(f'Call Option Price: $ {C}')
st.write(f'Put Option Price: $ {P}')


# ------------------------------ Backtesting ------------------------------------------ #


st.title("Backtesting")

lookback_duration = st.number_input("How many calendar days of history do you want to chart and test?", min_value=10, max_value=365, step=7)


# get data based on time interval until today
today = date.today() - dt.timedelta(lookback_duration)
one_month_lag_date = today.strftime('%Y-%m-%d')

stock = yf.download(ticker, start=one_month_lag_date)[
    ["Open", "High", "Low", "Close", "Volume"]
]

# Backtesting section 

def optim_func(series):
    if series['# Trades'] < 10:
        return -1
    # highest return for lowest time in the market & # trades >= 10 
    return series["Equity Final [$]"] / series ["Exposure Time [%]"]


# select strategy picklist 
strategy = st.selectbox(
    'Strategy to test?',
    ('MACD','MeanReversion','SwingTrading','RsiOscillator'))

if strategy == 'MACD':
    with st.spinner("testing.."):
        bt = Backtest(stock, MACD, cash=100000, commission=0.002)
        stats = bt.optimize(position_size = range(25,100,5), maximize = optim_func, max_tries = 500)
        st.write(f"{len(stats['_trades'].index)} Trade(s) Placed:")
        st.dataframe(stats['_trades'][['Size', 'EntryBar', 'ExitBar',  'EntryPrice', 'ExitPrice', 'PnL', 'ReturnPct', 'EntryTime', 'ExitTime']], use_container_width = True)
        st.write("Backtesting Stats:")
        st.dataframe(stats, use_container_width = True)
        st.write("Optimized Model Parameters:")
        st.write(stats['_strategy'])

elif strategy == 'MeanReversion':
    with st.spinner("testing.."):
        bt = Backtest(stock, MeanReversion, cash=100000, commission=0.002)
        stats = bt.optimize(position_size = range(25,100,5), maximize = optim_func, max_tries = 500)
        st.write(f"{len(stats['_trades'].index)} Trade(s) Placed:")
        st.dataframe(stats['_trades'][['Size', 'EntryBar', 'ExitBar',  'EntryPrice', 'ExitPrice', 'PnL', 'ReturnPct', 'EntryTime', 'ExitTime']], use_container_width = True)
        st.write("Backtesting Stats:")
        st.dataframe(stats, use_container_width = True)
        st.write("Optimized Model Parameters:")
        st.write(stats['_strategy'])
        
elif strategy == 'SwingTrading':
    with st.spinner("testing.."):
        bt = Backtest(stock, SwingTrading, cash=100000, commission=0.002, trade_on_close=True)
        stats = bt.optimize(position_size = range(25,100,5),
                            rsi_swing_window = range(3,6,1),
                            bar_limit = range(10,30,5),
                            rsi_limit = range(30,50,5),
                            maximize = optim_func, max_tries = 500)
        st.write(f"{len(stats['_trades'].index)} Trade(s) Placed:")
        st.dataframe(stats['_trades'][['Size', 'EntryBar', 'ExitBar',  'EntryPrice', 'ExitPrice', 'PnL', 'ReturnPct', 'EntryTime', 'ExitTime']], use_container_width = True)
        st.write("Backtesting Stats:")
        st.dataframe(stats, use_container_width = True)
        st.write("Optimized Model Parameters:")
        st.write(stats['_strategy'])

elif strategy == 'RsiOscillator':
    with st.spinner("testing.."):
        bt = Backtest(stock, RsiOscillator, cash=100000, commission=0.002)
        stats = bt.optimize(position_size = range(25,100,5),
                            upper_bound = range(50,90,10),
                            lower_bound = range(10,60,10),
                            rsi_window = range(10,18,2),
                            maximize = optim_func, max_tries = 500)
        st.write(f"{len(stats['_trades'].index)} Trade(s) Placed:")
        st.dataframe(stats['_trades'][['Size', 'EntryBar', 'ExitBar',  'EntryPrice', 'ExitPrice', 'PnL', 'ReturnPct', 'EntryTime', 'ExitTime']], use_container_width = True)
        st.write("Backtesting Stats:")
        st.dataframe(stats, use_container_width = True)
        st.write("Optimized Model Parameters:")
        st.write(stats['_strategy'])

stock = stock.reset_index()


# -------------------------------------- Plotting -------------------------------------- #


# candlestick plot w trade indicators
lower_bound, upper_bound = st.select_slider(
    'Select RSI bounds',
    options=range(10,95,5),
    value=(RsiOscillator.lower_bound, RsiOscillator.upper_bound))

# Calculate the RSI indicator 
macd, signal, hist = ta.MACD(stock['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
daily_rsi = ta.RSI(stock['Close'], 14)
stock['RSI'] = daily_rsi

# Add the MACD indicator to the DataFrame
stock['MACD'] = macd
stock['signal'] = signal
stock['hist'] = hist

stock['Date'] = stock['Date'].dt.tz_localize(None) 
stock['Date'] = stock['Date'].apply(lambda x: pd.Timestamp(x))
stock['Date'] = stock['Date'].dt.date


candle = go.Candlestick(x=stock['Date'],
                        open=stock['Open'],
                        high=stock['High'],
                        low=stock['Low'],
                        close=stock['Close'],
                        name = "Candles")

enter_trade = go.Scatter(
        x=stats['_trades']['EntryTime'],
        y=stats['_trades']['EntryPrice'].apply(lambda x: x*1.1),
        mode="markers",
        marker=dict(symbol='triangle-up-open'),
        name = "Entry Trade"
)

exit_trade = go.Scatter(
        x=stats['_trades']['ExitTime'],
        y=stats['_trades']['ExitPrice'].apply(lambda x: x*1.1),
        mode="markers",
        marker=dict(symbol='triangle-down-open'),
        name = "Exit Trade"
)

rsi_chart = go.Scatter(
    x=stock['Date'],
    y=stock['RSI'],
    name = "RSI",
    line_color='blue'
)

macd_line = go.Scatter(
    x=stock['Date'],
    y=stock['MACD'],
    name = "MACD"
)

ema_signal = go.Scatter(
    x=stock['Date'],
    y=stock['signal'],
    name = "EMA Signal"
)

volume_bars = go.Bar(
    x=stock['Date'],
    y=stock['hist'],
    marker={
        "color": "lightsteelblue",
    },
    opacity=0.5,
    name = "Difference"
)
tickmode='linear'

fig_trades = make_subplots(rows = 3, cols = 1, shared_xaxes=True, specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]])
# plot candles
fig_trades.add_trace(candle, row = 1, col = 1)
fig_trades.add_trace(enter_trade, row = 1, col = 1)
fig_trades.add_trace(exit_trade, row = 1, col = 1)
# plot rsi
fig_trades.add_trace(rsi_chart, row = 2, col = 1)
fig_trades.add_hline(y = lower_bound, opacity = 0.5, line_width = 1, row = 2, col = 1, line_dash="dash", line_color="green")
fig_trades.add_hline(y = upper_bound, opacity = 0.5, line_width = 1, row = 2, col = 1, line_dash="dash", line_color="red")

# plot macd
fig_trades.add_trace(volume_bars, row = 3, col = 1, secondary_y=False)
fig_trades.add_hline(y = 0, opacity = 0.5, line_width = 1, row = 3, col = 1, line_dash="dash", line_color="black")
fig_trades.add_trace(macd_line, row = 3, col = 1)
fig_trades.add_trace(ema_signal, row = 3, col = 1)
fig_trades.update_xaxes(
    rangebreaks=[dict(bounds=["sat", "mon"])]
)
fig_trades.update_layout(
    title=dict( text=f"{ticker} Backtested Trades", font=dict(size=24), yref='paper'),
    xaxis_rangeslider_visible=False,
    height=1200
)

st.plotly_chart(fig_trades, use_container_width=True, height=800)

