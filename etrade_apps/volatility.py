import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from pretty_html_table import build_table
import time

#replace with the directory to your data path
DATA_PATH = '/Users/trapbookpro/Development/Etrade/etrade-monitor/etrade_python_client/data'

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
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0

    vol_file = ''
    vol_day_diff = float('inf')
    for assoc_file in os.listdir(f'{DATA_PATH}/voldata'):
        prefix = f'volatility_scanner_result_{time_period}_baseline'
        if prefix in assoc_file:
            try:
                ref_file_date = datetime.strptime(
                    f'{assoc_file}',
                    f'volatility_scanner_result_{time_period}_baseline_%Y-%m-%d.csv'
                )
            except Exception as e:
                print(e)
                continue
            else:
                # get the vol file with the closet day
                day_diff = (datetime.today() - ref_file_date).days
                if day_diff < vol_day_diff:
                    vol_day_diff = day_diff
                    vol_file = assoc_file
    df = pd.DataFrame()
    if vol_day_diff < 5:
        df = pd.read_csv(f'{DATA_PATH}/voldata/{vol_file}')
        df = df.reset_index(drop=True)
        df = df[['Ticker', 'Volatility','LastPrice']]
        count = df.shape[0]
    else:
        if symbols == []:
            symbols = []
            f = open(f"{DATA_PATH}/us_symbols.csv", "r")
            f.readline()
            for line in f:
                symbol,_,_ = line.strip("\n").split(",")
                symbols.append(symbol)
            f.close()

        vol_list = []
        for i, tick in enumerate(symbols):
            count += 1
            try:
                vol_list.append(ticker_volatility_matrix_with_time_period(tick, time_period))
            except:
                print("Error with accessing ticker information for:", tick, ", omitting.")
            print(".", end="")

        df = pd.DataFrame(vol_list, columns=['Ticker', 'Volatility', 'LastPrice'])
        if symbols == []: # only when we query for all symbols do we create baseline
            filename = f'volatility_scanner_result_{time_period}_baseline_{today}.csv'
            df.to_csv(f'{DATA_PATH}/voldata/{filename}')
    df = df[df["Volatility"] >= volatility]
    df = df[df['LastPrice'] >= price]

    sp = ticker_volatility_matrix_with_time_period('SPY', time_period)
    if not (df['Ticker'].eq(sp[0])).any():  # Add S&P to the vol list matrix
        sp[0]= "SPY BASELINE"
        spy_baseline = pd.DataFrame([sp], columns=['Ticker','Volatility','LastPrice'])
        df = pd.concat([spy_baseline, df]).reset_index(drop=True)

    seconds = time.time() - seconds

    if to_csv:
        df = df.reset_index(drop=True)
        filename = f'volatility_scanner_result_{time_period}{"_price_"+str(price)+"_" if price else ""}_{today}.csv'
        df.to_csv(f'{DATA_PATH}/voldata/{filename}')

    if to_html:
        df['yFinance Link'] = 'https://finance.yahoo.com/quote/' + df['Ticker']
        df = df.reset_index(drop=True)
        if df.shape[0] == 0:
            "No Ticker Fits Search Parameters.", count, seconds
        return build_table(df, 'green_dark'),count,seconds
    return df,count,seconds
