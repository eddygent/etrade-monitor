#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from pretty_html_table import build_table
import time
import matplotlib.pyplot as plt

from redmail import gmail
import sys

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + '/../')
import etrade_config

gmail.username = etrade_config.sender_email
gmail.password = etrade_config.password

script_path = os.path.dirname(os.path.abspath(__file__))
DATA_PATH =  script_path + '/../data'

# check if path exists. if it does not exist then create it.
if not os.path.exists(DATA_PATH):
    print("MAKING NEW DIR FOR DATA")
    os.mkdir(DATA_PATH)
if not os.path.exists(os.path.join(DATA_PATH,'voldata')):
    print("MAKING NEW DIR VOLDATA")
    os.mkdir(os.path.join(DATA_PATH,'voldata'))

EOD_TIME = datetime.today().replace(hour=4,minute=0,second=0,microsecond=0)
HEADER = ['ticker', 'lastPrice', 'volatility', 'prevDayVolatility', 'percentMove', 'avgVolume']
TODAY = datetime.now().strftime("%Y-%m-%d")
EXCLUDE = pd.read_csv(os.path.join(DATA_PATH, 'exclude.csv'))['ticker'].values

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
    return [ticker, volatility, y.fast_info['lastPrice'],data['Volume'].mean()]

def ticker_volatility_matrix_with_time_period(ticker, time_period="3mo"):
    y = yf.Ticker(ticker)
    data = y.history(period=time_period)
    time_period = data.shape[0]
    data['Log returns'] = np.log(data['Close'] / data['Close'].shift())
    data['Log returns'].std()
    volatility = data['Log returns'].std() * np.sqrt(time_period)
    return [ticker, volatility, y.fast_info['lastPrice'],data['Volume'].mean()]

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

def volatility_scanner(symbols=[], volatility=".3", time_period="3mo", price=None,to_csv=True,to_html=False,volume=1000000, gt=True):
    volatility = float(volatility)
    price = float(price) if price else 0
    seconds = time.time()
    # today = datetime.now().strftime("%Y-%m-%d")
    count = 0
    save_baseline = True if symbols == [] else False
    vol_file = ''
    vol_day_diff = float('inf')
    for assoc_file in os.listdir(f'{DATA_PATH}/voldata'):
        prefix = f'volatility_scanner_result_{time_period}_{volatility}_baseline_{TODAY}.csv'
        if prefix in assoc_file:
            try:
                ref_file_date = datetime.strptime(
                    f'{assoc_file}',
                    f'volatility_scanner_result_{time_period}_{volatility}_baseline_%Y-%m-%d.csv'
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
        df = df[['Ticker', 'Volatility','LastPrice','Mean Volume']]
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

        df = pd.DataFrame(vol_list, columns=['Ticker', 'Volatility', 'LastPrice','Mean Volume'])
        if save_baseline: # only when we query for all symbols do we create baseline
            filename = f'volatility_scanner_result_{time_period}_{volatility}_baseline_{TODAY}.csv'
            df.to_csv(f'{DATA_PATH}/voldata/{filename}')
    df = df[df["Volatility"] >= volatility]
    if gt:
        df = df[df['LastPrice'] >= price]
    else:
        df = df[df['LastPrice'] >= price]

    df = df.sort_values(by=['Volatility'])

    sp = ticker_volatility_matrix_with_time_period('SPY', time_period)
    if not (df['Ticker'].eq(sp[0])).any():  # Add S&P to the vol list matrix
        sp[0]= "SPY BASELINE"
        spy_baseline = pd.DataFrame([sp], columns=['Ticker','Volatility','LastPrice','Mean Volume'])
        df = pd.concat([spy_baseline, df]).reset_index(drop=True)

    seconds = time.time() - seconds

    if to_csv:
        df = df.reset_index(drop=True)
        filename = f'volatility_scanner_result_{time_period}{"_price_"+str(price)+"_" if price else ""}{TODAY}.csv'
        df.to_csv(f'{DATA_PATH}/voldata/{filename}')

    df = df[df['Mean Volume'] >= volume] # we want an average volume of at least 20,000,000

    if to_html:
        df['yFinance Link'] = 'https://finance.yahoo.com/quote/' + df['Ticker']
        df['Mean Volume'] = df['Mean Volume']/1000
        df = df.reset_index(drop=True)
        if df.shape[0] == 0:
            "No Ticker Fits Search Parameters.", count, seconds
        return build_table(df, 'green_dark'),count,seconds
    return df,count,seconds

def tick_vol_runner(time_period='3mo', date=TODAY, test=False):
    if "-" not in date:
        date = datetime.strptime(date, '%Y%m%d').strftime("%Y-%m-%d")
    symbols = []

    f = open(f"{DATA_PATH}/us_symbols.csv", "r")
    f.readline()
    for line in f:
        symbol,_,_ = line.strip("\n").split(",")
        symbols.append(symbol)
    f.close()

    filename = f'voldata/volatility_scanner_result_{date}_{time_period}.csv'
    filepath = os.path.join(DATA_PATH,filename)

    if not os.path.exists(filepath):
        print(f'creating csv file: {filepath}')
        f = open(filepath, 'w')
        print(f'{",".join(HEADER)}', file=f)
        f.close() # only want to write the first line
    else:
        print(f"Found file for {date}")
    count = 0

    df = pd.read_csv(filepath)
    if test:
        return df

    for i, tick in enumerate(symbols):
        count += 1
        if tick in df['ticker'].values:
            print("Skipping over," ,tick , "already included.")
            continue
        if tick in EXCLUDE:
            print("Purposely skipping over", tick)
            continue
        try:
            df = pd.concat([df, ticker_volatility_matrix_with_time_period_df(tick, time_period=time_period)])
        except:
            print("Error with accessing ticker information for:", tick, ", omitting.")
        else:
            df.tail(1).to_csv(filepath, mode='a', index=False,header=False )
            count += 1
            print("Adding " + tick)
    return df

def ticker_volatility_matrix_with_time_period_df(ticker, time_period="3mo"):
    y = yf.Ticker(ticker)
    data = y.history(period=time_period)
    time_period = data.shape[0]

    # curr_day = y.info['currentPrice']
    curr_day = y.fast_info['lastPrice']
    prev_day = data.iloc[-2].loc['Close']

    diff_days = curr_day/prev_day-1

    data['Log returns'] = np.log(data['Close'] / data['Close'].shift())
    data['Log returns'].std()

    volatility = data['Log returns'].std() * np.sqrt(time_period)

    # We want to us historical measures of volatility not including past day
    prev_day_data = data.copy().iloc[:time_period-1,]
    prev_day_data['Log returns'] = np.log(data['Close'] / data['Close'].shift())
    prev_day_data['Log returns'].std()
    prev_day_volatility = prev_day_data['Log returns'].std() * np.sqrt(time_period-1)

    df = pd.DataFrame(columns=HEADER)
    df.loc[0] = [ticker, y.fast_info['lastPrice'], volatility, prev_day_volatility,diff_days, data['Volume'].mean()]
    # df.loc[0] = [ticker, y.info['currentPrice'], volatility, prev_day_volatility,diff_days, data['Volume'].mean()]
    return df

def ticker_volatility_matrix_with_time_period_plt_vol(ticker, time_period="3mo"):
    y = yf.Ticker(ticker)
    try:
        data = y.history(period=time_period)
    except Exception:
        data = y.history(period=f'{time_period}d')
    time_period = data.shape[0]

    data['Log returns'] = np.log(data['Close'] / data['Close'].shift())
    data['Log returns'].std()

    volatility = data['Log returns'].std() * np.sqrt(time_period)
    str_vol = str(round(volatility, 4) * 100)

    fig, ax = plt.subplots()
    data['Log returns'].hist(ax=ax, bins=50, alpha=0.6, color='b')
    ax.set_xlabel("Log return")
    ax.set_ylabel("Freq of log return")
    ax.set_title(f"{ticker} volatility: " + str_vol + "%")

    return fig

def ticker_volatility_matrix_with_time_period_plt_stock(ticker, time_period="3mo"):
    y = yf.Ticker(ticker)
    try:
        data = y.history(period=time_period)
    except Exception:
        data = y.history(period=f'{time_period}d')
    tp = time_period
    data = data.reset_index()
    print(data)

    fig,ax = plt.subplots()
    plt.plot(data['Date'], data['Close'])
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.set_title(f"{ticker} Performance over {tp}")

    return fig



def main():
    pass

if __name__ == '__main__':
    main()
# perf_fig = ticker_volatility_matrix_with_time_period_plt_stock("T", time_period="3mo")
# gmail.send(
#             subject=f"test",
#             sender=f"{etrade_config.email}",
#             receivers=[f"{etrade_config.email}"],
#
#             # A plot in body
#             html=f"""
#
#                     {{{{ visualize_perf }}}}
#
#                 """,
#             body_images={
#                 "visualize_perf": perf_fig
#             }
#         )