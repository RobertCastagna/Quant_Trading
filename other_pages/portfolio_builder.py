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

st.set_page_config(layout="wide")

show_pages(
    [
        Page("streamlit_app.py", "Home"),
        Page("other_pages/individual_strategy.py", "Strategy"),
        Page("other_pages/portfolio_builder.py", "Watchlist")

    ]
)

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():

    # https://docs.streamlit.io/library/api-reference/data/st.data_editor
    # need to lock user column and set index as current date
    ticker_options = pd.read_excel('indicators.xlsx')

    #dt.datetime.today().strftime('%Y-%m-%d') # todays date formatted properly

    edited_df = st.data_editor(ticker_options, disabled = ('date'), use_container_width =True, num_rows="dynamic", hide_index=True)
    st.write("Please make sure to fill out all fields before hitting Save <3")

    # add button to save portfolio to xlsx
    if st.button("Save", type="primary"):
        edited_df.to_excel('indicators.xlsx', index=False, header=True)
        st.write("Saved...")
