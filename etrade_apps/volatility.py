import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime,timedelta

def ticker_volatility_matrix_ranged_time(
        ticker,
        start_date=(datetime.now() - timedelta(days=43)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d")
):
    y = yf.Ticker(ticker)
    data = yf.download(ticker, start=start_date, end=end_date)
    time_period = data.shape[0]
    data['Log returns'] = np.log(data['Close'] / data['Close'].shift())
    data['Log returns'].std()
    volatility = data['Log returns'].std() * np.sqrt(time_period)
    return [ticker, volatility, y.fast_info['lastPrice']]


def ticker_volatility_matrix_with_time_period(ticker, time_period="3mo"):
    y = yf.Ticker(ticker)
    data = y.history(period=time_period)
    time_period = data.shape[0]
    data['Log returns'] = np.log(data['Close'] / data['Close'].shift())
    data['Log returns'].std()
    volatility = data['Log returns'].std() * np.sqrt(time_period)
    return [ticker, volatility, y.fast_info['lastPrice']]

def four_week_vol(ticker,date):
    '''date in format %Y-%m-%d'''
    end_date = date
    start_date = (datetime.strptime(date,"%Y-%m-%d") - timedelta(days=30)).strftime('%Y-%m-%d')
    return ticker_volatility_matrix_ranged_time(ticker, start_date, end_date)

def two_week_vol(ticker,date):
    '''date in format %Y-%m-%d'''
    end_date = date
    start_date = (datetime.strptime(date,"%Y-%m-%d") - timedelta(days=15)).strftime('%Y-%m-%d')
    return ticker_volatility_matrix_ranged_time(ticker, start_date, end_date)
