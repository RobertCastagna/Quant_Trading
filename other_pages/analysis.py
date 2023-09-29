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
print(df.head())
df_pivot=df.pivot(index='Date',columns='Symbol',values='Close')
print(df_pivot)

corr_df = df_pivot.corr(method='pearson')
#reset symbol as index (rather than 0-X)
print(corr_df.head().reset_index())
#del corr_df.index.name
print(corr_df.head(10))

fig, ax = plt.subplots()
ax = seaborn.clustermap(corr_df, annot=True, cmap='RdYlGn')
plt.show()
st.write(fig)

