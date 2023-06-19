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

script_path = os.path.dirname(os.path.abspath(__file__))
DATA_PATH =  script_path + '/../data'

RATE = .0525  # Annualized risk free rate
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

def tick_vol_runner(time_period='3mo'):

    symbols = []

    f = open(f"{DATA_PATH}/us_symbols.csv", "r")
    f.readline()
    for line in f:
        symbol,_,_ = line.strip("\n").split(",")
        symbols.append(symbol)
    f.close()

    filename = f'voldata/volatility_scanner_result_{TODAY}_{time_period}.csv'
    filepath = os.path.join(DATA_PATH,filename)

    if not os.path.exists(filepath):
        print(f'creating csv file: {filepath}')
        f = open(filepath, 'w')
        print(f'{",".join(HEADER)}', file=f)
        f.close() # only want to write the first line
    count = 0

    df = pd.read_csv(filepath)

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

import math
from scipy.stats import norm

def american_black_scholes_price(S, K, r, T, sigma):
    """
    Calculates the price of an American call option using the Black-Scholes model.

    Args:
    S: The spot price of the underlying asset.
    K: The strike price of the option.
    r: The risk-free interest rate.
    T: The time to expiration of the option.
    sigma: The volatility of the underlying asset.

    Returns:
    The price of the American option.
    """

    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / sigma * math.sqrt(T)
    d2 = d1 - sigma * math.sqrt(T)

#Black Scholes Option Tool by Brian Hyde

from math import sqrt, exp, log, erf

from decimal import *
getcontext().prec = 5

def black_scholes_price(S, K, time, sigma, divrate=0):
    #statistics
    sigTsquared = sqrt(Decimal(time)/365)*sigma
    edivT = exp((-divrate*time)/365)
    ert = exp((-RATE*time)/365)
    d1 = (log(S*edivT/K)+(RATE+.5*(sigma**2))*time/365)/sigTsquared
    d2 = d1-sigTsquared
    Nd1 = (1+erf(d1/sqrt(2)))/2
    Nd2 = (1+erf(d2/sqrt(2)))/2
    iNd1 = (1+erf(-d1/sqrt(2)))/2
    iNd2 = (1+erf(-d2/sqrt(2)))/2

    #Outputs
    callPrice = round(S*edivT*Nd1-K*ert*Nd2, 2)
    putPrice = round(K*ert*iNd2-S*edivT*iNd1, 2)
    return {"call:": callPrice, "put": putPrice}

def count_business_days(start_date, end_date):
  """Counts the number of business days between two dates.

  Args:
    start_date: The start date.
    end_date: The end date.

  Returns:
    The number of business days between the two dates.
  """

  business_days = 0
  while start_date <= end_date:
    if start_date.weekday() < 5:
      business_days += 1
    start_date += timedelta(days=1)

  return business_days

def black_scholes_ticker_symbol(ticker, option_chain, targetPrice):
    underlyingPrice = yf.Ticker(ticker).fast_info['lastPrice']
    sigma = abs(((targetPrice/underlyingPrice)-1)*2) # the volatility we expect
    strike = option_chain.iloc[0]['Strike']
    start_date = datetime.strptime(TODAY,'%Y-%m-%d')
    expiry_date = datetime.strptime(option_chain.iloc[0]['date'], '%Y-%m-%d')
    time = count_business_days(start_date, expiry_date) # count business days
    bsp = black_scholes_price(underlyingPrice,strike,time, sigma=sigma)
    bsp['ticker'] = ticker
    bsp['strike'] = strike
    bsp['sigma'] = sigma
    bsp['targetPrice'] = targetPrice
    return bsp


# #Operations
# print("")
# print("Call Price = " + str(callPrice) )
# print("Put Price = " + str(putPrice) )

def main():
    # inputs
    undprice = 16.06  # S
    strike = 16  # K
    time = 24  # time until expiration in days

    sigma = .038  # Standard Deviation of stock's returns
    divrate = 0  # Dividend yield on stock
    print(black_scholes_price(S=undprice, K=strike, time=time, sigma=sigma))
#     # import yfinance as yf  # Import yahoo finance module
#     # tesla = yf.Ticker("TSLA")  # Passing Tesla Inc. ticker
#     #
#     # opt = tesla.option_chain('2023-06-23')  # retreiving option chains data for 17 June 2022
#     # print(opt.calls.columns)
#
main()