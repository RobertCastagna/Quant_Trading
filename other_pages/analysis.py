import numpy as np 
import pandas as pd 
import streamlit as st
# Used to grab the stock prices, with yahoo 
import yfinance as yf
import datetime as dt
from datetime import datetime 
# To visualize the results 
import matplotlib.pyplot as plt 
import seaborn
from st_pages import Page, show_pages

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


start = dt.date.today() - dt.timedelta(3)
col_L_pad, col1, col2, col_R_pad = st.columns([1,1,1,1])
with col1:
    st.title("Correlation Plot")
with col2:
    start = st.date_input("Enter Start Date for Historical Data", start)


symbols=[]

for ticker in options:     
    r = yf.download(ticker, start=start)[["Close"]]
    # add a symbol column   
    r['Symbol'] = ticker    
    symbols.append(r)

# concatenate into df
df = pd.concat(symbols)
df = df.reset_index()
df = df[['Date', 'Close', 'Symbol']]
df_pivot=df.pivot(index='Date',columns='Symbol',values='Close').reset_index()

corr_df = df_pivot.corr(method='pearson')
corr_df.reset_index()

fig, ax = plt.subplots()
ax = seaborn.heatmap(corr_df,  ax=ax, annot=True, cmap='RdYlGn')
st.write(fig)