from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from pretty_html_table import build_table
import time

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

def volatility_scanner(symbols=[], volatility=".25", time_period="3mo", price=None,to_csv=True,to_html=False):
    volatility = float(volatility)
    price = float(price) if price else 0
    seconds = time.time()
    if symbols == []:
        symbols = []
        f = open("/Users/trapbookpro/Development/Etrade/etrade-monitor/etrade_python_client/data/us_symbols.csv", "r")
        f.readline()
        for line in f:
            symbol,_,_ = line.strip("\n").split(",")
            symbols.append(symbol)
        f.close()
    vol_list = []
    count = 0
    for i, tick in enumerate(symbols):
        count += 1
        try:
            vol_list.append(ticker_volatility_matrix_with_time_period(tick, time_period))
        except:
            print("Error with accessing ticker information for:", tick, ", omitting.")
        print(".", end="")

    df = pd.DataFrame(vol_list, columns=['Ticker','Volatility','LastPrice'])

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f'volatility_scanner_result_{time_period}_baseline_{today}.csv'
    df.to_csv(f'/Users/trapbookpro/Development/Etrade/etrade-monitor/etrade_python_client/data/voldata/{filename}')

    df = df[df["Volatility"] >= volatility]
    df = df[df['LastPrice'] >= price]
    seconds = time.time() - seconds

    if to_csv:
        df = df.reset_index(drop=True)
        filename = f'volatility_scanner_result_{time_period}{"_price_"+str(price)+"_" if price else ""}_{today}.csv'
        df.to_csv(f'/Users/trapbookpro/Development/Etrade/etrade-monitor/etrade_python_client/data/voldata/{filename}')
    if to_html:
        if df.shape[0] == 0:
            "No Ticker Fits Search Parameters.", count, seconds
        return build_table(df, 'green_dark'),count,seconds
    return df,count,seconds
