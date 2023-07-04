#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 04/07/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
import math
from datetime import datetime, timedelta
import os
import sys

import pandas as pd
import yfinance as yf
from volatility import TODAY, ticker_volatility_matrix_with_time_period_df

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + '/../')

import etrade_config
RATE = etrade_config.RATE  # Annualized risk free rate
from yop import get_friday_option_for_ticker_date_closest_to_price, get_friday_options_chain_for_ticker_date

import matplotlib.pyplot as plt

from redmail import gmail
gmail.username = etrade_config.email
gmail.password = etrade_config.password

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

def black_scholes_price(S:float, K:float, time:int, sigma:float, divrate:int=0) -> dict:
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
    return {"call": callPrice, "put": putPrice}

def black_scholes_price_date(S:float , K:float, date:str, sigma:float, divrate:int=0) -> dict:
    #statistics
    start_date = datetime.strptime(TODAY, '%Y-%m-%d')
    expiry_date = datetime.strptime(date, '%Y-%m-%d')
    time = count_business_days(start_date, expiry_date)  # count business days

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
    return {"call": callPrice, "put": putPrice, "sigma":sigma}


def black_scholes_price_date_target_price(S:float, K:float, date:str, targetPrice:float, divrate:float=0) -> dict:
    '''
    Get the black scholes calculation given a S=Spot Price, K=Strike Price, date=in str format "%Y-%m-%d" and dividend rate.
    '''
    # statistics
    start_date = datetime.strptime(TODAY, '%Y-%m-%d')
    expiry_date = datetime.strptime(date, '%Y-%m-%d')
    time = count_business_days(start_date, expiry_date)  # count business days

    sigma = abs(((targetPrice/S)-1)*2) # the volatility we expect/needed to expire itm using target price

    sigTsquared = sqrt(Decimal(time) / 365) * sigma
    edivT = exp((-divrate * time) / 365)
    ert = exp((-RATE * time) / 365)
    d1 = (log(S * edivT / K) + (RATE + .5 * (sigma ** 2)) * time / 365) / sigTsquared
    d2 = d1 - sigTsquared
    Nd1 = (1 + erf(d1 / sqrt(2))) / 2
    Nd2 = (1 + erf(d2 / sqrt(2))) / 2
    iNd1 = (1 + erf(-d1 / sqrt(2))) / 2
    iNd2 = (1 + erf(-d2 / sqrt(2))) / 2

    # Outputs
    callPrice = round(S * edivT * Nd1 - K * ert * Nd2, 2)
    putPrice = round(K * ert * iNd2 - S * edivT * iNd1, 2)
    return {"call": callPrice, "put": putPrice,'sigma':sigma}

def count_business_days(start_date:str, end_date:str):
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

def black_scholes_ticker_symbol(ticker:str, option_chain:pd.DataFrame, targetPrice:float) -> pd.DataFrame:
    '''
    Get the black scholes calculation given a ticker, options chain, and target price.
    '''
    underlyingPrice = yf.Ticker(ticker).fast_info['lastPrice']
    sigma = abs(((targetPrice/underlyingPrice)-1)*2)  # the volatility we expect/needed to expire itm using target price
    strike = option_chain.iloc[0]['Strike']
    start_date = datetime.strptime(TODAY,'%Y-%m-%d')
    expiry_date = datetime.strptime(option_chain.iloc[0]['date'], '%Y-%m-%d')
    time = count_business_days(start_date, expiry_date) # count business days
    bsp = black_scholes_price(underlyingPrice,strike,time, sigma=sigma)
    option_chain['BS_sigma'] = sigma
    option_chain['BS_targetPrice'] = targetPrice
    option_chain['BS_Call'] = bsp['call']
    option_chain['BS_Put'] = bsp['put']

    iv =  option_chain.iloc[0]['Implied Volatility']
    impliedVolBSP = black_scholes_price(underlyingPrice,strike,time, sigma=iv)
    option_chain['_BS_IVPut'] = impliedVolBSP['put']
    option_chain['_BS_IVCall'] = impliedVolBSP['call']

    return option_chain

def black_scholes_ticker_symbol_vol(ticker:str, option_chain:pd.DataFrame) -> pd.DataFrame:
    underlyingPrice = yf.Ticker(ticker).fast_info['lastPrice']
    strike = option_chain.iloc[0]['Strike']
    start_date = datetime.strptime(TODAY,'%Y-%m-%d')
    expiry_date = datetime.strptime(option_chain.iloc[0]['date'], '%Y-%m-%d')
    time = count_business_days(start_date, expiry_date) # count business days

    vol_df = ticker_volatility_matrix_with_time_period_df(ticker, time_period=f"{int(time*1.33)}d") # get the volatility days out
    sigma = vol_df.iloc[0]['volatility']
    print(f"Generating Sigma from {int(time*1.33)} days out. Using Vol: {sigma}")
    bsp = black_scholes_price(underlyingPrice,strike,time, sigma=sigma)
    option_chain.loc[:,'BS_sigma_vol'] = sigma
    option_chain.loc[:,'BS_Call_vol'] = bsp['call']
    option_chain.loc[:,'BS_Put_vol'] = bsp['put']

    iv =  option_chain.iloc[0]['Implied Volatility']
    impliedVolBSP = black_scholes_price(underlyingPrice,strike,time, sigma=iv)
    option_chain['_BS_IVPut'] = impliedVolBSP['put']
    option_chain['_BS_IVCall'] = impliedVolBSP['call']

    return option_chain

def black_scholes_option_pricer(ticker:str, call_or_put:str, target_price:float=None, strike:float=None, days:int=30, long:bool=True) ->pd.DataFrame:
    '''
    Black Scholes Options Pricer that takes the target price as input to determine volatility, and days until expiration.
    Works for both long and short options.

    If the strike is specified not specified and the target price is,
    the strike will be that of closest to the target price.

    If the strike is not specified and the target price is not specified, the target price will use its volatility
    within past days(days) to generate a target price, then as a volatility measure and use as input to black scholes model.
    The strike will be that of whatever is closest to the target price.
    '''
    if strike == None and target_price != None:
        option_chain = get_friday_option_for_ticker_date_closest_to_price(ticker=ticker,
                                                                          price=target_price,
                                                                          call_or_put=call_or_put,
                                                                          days=days, long=long)
    elif strike == None and target_price == None:
        last_price = yf.Ticker(ticker).fast_info['lastPrice']
        vol_df = ticker_volatility_matrix_with_time_period_df(ticker,
                                                              time_period=f"{days}d")  # get the volatility days out
        sigma = vol_df.iloc[0]['volatility']
        sigma = sigma / 2 # divide the sigma by 2 to be conservative

        if (call_or_put == 'c' and long == True) or (call_or_put == 'p' and long == False):
            # add to the target price
            last_price += last_price*sigma
        elif (call_or_put == 'c' and long == False) or (call_or_put=='p' and long == True):
            # add to the target price
            last_price -= last_price * sigma
        target_price = last_price
        option_chain = get_friday_option_for_ticker_date_closest_to_price(ticker=ticker,
                                                                          price=target_price,
                                                                          call_or_put=call_or_put,
                                                                          days=days, long=long)
    elif strike != None and target_price == None:
        # TODO: Need to use the strike and get the target price options chain.
        pass

    else:
        chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put=call_or_put, days=days)
        option_chain = chain[ chain['Strike'] == strike]
    ticker = option_chain.iloc[0]['Underlying']
    if target_price:
        bspricer = black_scholes_ticker_symbol(ticker, option_chain, target_price)
    else:
        bspricer = black_scholes_ticker_symbol_vol(ticker, option_chain) # use volatility within date time period as vol
    return bspricer

def black_scholes_pricer_entire_chain_target(option_chain:pd.DataFrame, target_price:float) -> pd.DataFrame:
    '''
    use volatility to reach target price as future volatility as input for black scholes model
    for the entire options chain
        Target Volatility: The minimum volatility required in order to reach the target price of an option.
    '''
    option_chain['BS_Call'] = 0
    option_chain['BS_Put'] = 0
    option_chain['BS_sigma'] = 0
    for index, row in option_chain.iterrows():
        black_scholes_dict = black_scholes_price_date_target_price(yf.Ticker(row['Underlying']).fast_info['lastPrice'], row['Strike'], row['date'],targetPrice=target_price)
        option_chain.iloc[index, option_chain.columns.get_loc('BS_Call_target')] = black_scholes_dict['call']
        option_chain.iloc[index, option_chain.columns.get_loc('BS_Put_target')] = black_scholes_dict['put']
        option_chain.iloc[index, option_chain.columns.get_loc('BS_sigma_target')] = black_scholes_dict['sigma']
    return option_chain

def black_scholes_pricer_entire_chain(option_chain:pd.DataFrame) -> pd.DataFrame:
    '''
    use ideal volatility as future volatility as input for black scholes model
    for the entire options chain
        Ideal Vol: The minimum volatility required in order to reach a particular options Strike.
    '''
    option_chain['BS_Call'] = 0
    option_chain['BS_Put'] = 0
    option_chain['BS_sigma'] = 0
    for index, row in option_chain.iterrows():
        black_scholes_dict = black_scholes_price_date_target_price(yf.Ticker(row['Underlying']).fast_info['lastPrice'], row['Strike'], row['date'],row['Strike'])
        option_chain.iloc[index, option_chain.columns.get_loc('BS_Call')] = black_scholes_dict['call']
        option_chain.iloc[index, option_chain.columns.get_loc('BS_Put')] = black_scholes_dict['put']
        option_chain.iloc[index, option_chain.columns.get_loc('BS_sigma')] = black_scholes_dict['sigma']
    return option_chain

def black_scholes_pricer_entire_chain_vol(option_chain:pd.DataFrame)-> pd.DataFrame:
    '''
    use the previous volatility (number of days back * 1.33) as future volatility as input for black scholes model
    for the entire options chain
    '''
    ticker = option_chain.iloc[0]['Underlying']
    date = option_chain.iloc[0]['date']
    start_date = datetime.strptime(TODAY, '%Y-%m-%d')
    expiry_date = datetime.strptime(date, '%Y-%m-%d')
    time = count_business_days(start_date, expiry_date)  # count business days

    vol_df = ticker_volatility_matrix_with_time_period_df(ticker, time_period=f"{int(time * 1.33)}d")  # get the volatility days out
    sigma = vol_df.iloc[0]['volatility']
    print(f"Generating Sigma from {int(time * 1.33)} days out. Using Vol: {sigma}")

    option_chain['BS_Call_vol'] = 0
    option_chain['BS_Put_vol'] = 0
    option_chain['BS_sigma_vol'] = 0
    for index, row in option_chain.iterrows():
        black_scholes_dict = black_scholes_price_date(yf.Ticker(row['Underlying']).fast_info['lastPrice'], row['Strike'], row['date'], sigma=sigma)
        option_chain.iloc[index, option_chain.columns.get_loc('BS_Call_vol')] = black_scholes_dict['call']
        option_chain.iloc[index, option_chain.columns.get_loc('BS_Put_vol')] = black_scholes_dict['put']
        option_chain.iloc[index, option_chain.columns.get_loc('BS_sigma_vol')] = black_scholes_dict['sigma']
    return option_chain

def visualize_impl_vs_ideal(option_chain:pd.DataFrame):
    '''
    Visualize the implied vol vs ideal vol...
        Ideal Vol: The minimum volatility required in order to reach a particular options Strike.
        Realized Vol: The current volatility over the past (x) days of the underlying used as input to Black Scholes Model.
    '''
    option_chain = black_scholes_pricer_entire_chain(option_chain)
    ticker = option_chain.iloc[0]['Underlying']

    plt.title(f'{ticker} Impl. Vol. vs. Ideal Vol. - [Volatility To Reach Strike]')

    call_or_put = option_chain.iloc[0]['call_or_put']
    if call_or_put == 'CALL':
        cols = ['BS_Call', 'Last Price']
    else:
        cols = ['BS_Put', 'Last Price']

    label = ['Realized','Implied Volatility']
    colors = ['red', 'blue']
    line_style = ['-.', '-']
    for idx, col in enumerate(cols):
        plt.plot(option_chain['Strike'], option_chain[col], color=colors[idx], label=label[idx], linestyle=line_style[idx])
    plt.xlabel("Strikes", fontweight='bold')
    plt.ylabel("Price", fontweight='bold')
    plt.legend(loc="upper right")

    ax = plt.gca()
    ax.set_facecolor("black")
    plt.show()

def visualize_impl_vs_real_vol(option_chain:pd.DataFrame):
    '''
    Visualize the implied vol vs real vol...
        Implied Vol: What the Options Implied Volatility is in the market.
        Realized Vol: The current volatility over the past (x) days of the underlying used as input to Black Scholes Model.
    '''
    option_chain = black_scholes_pricer_entire_chain_vol(option_chain)
    ticker = option_chain.iloc[0]['Underlying']

    plt.title(f'{ticker} Impl. Vol. vs. Real Vol. - [Volatility Within Time Period]')

    call_or_put = option_chain.iloc[0]['call_or_put']
    if call_or_put == 'CALL':
        cols = ['BS_Call_vol', 'Last Price']
    else:
        cols = ['BS_Put_vol', 'Last Price']

    label = ['Realized','Implied Volatility']
    colors = ['red', 'blue']
    line_style = ['-.', '-']
    for idx, col in enumerate(cols):
        plt.plot(option_chain['Strike'], option_chain[col], color=colors[idx], label=label[idx], linestyle=line_style[idx])
    plt.xlabel("Strikes", fontweight='bold')
    plt.ylabel("Price", fontweight='bold')
    plt.legend(loc="upper right")

    ax = plt.gca()
    ax.set_facecolor("black")
    plt.show()

def visualize_impl_vs_real_combined(option_chain:pd.DataFrame):
    '''
    Visualize the implied vol vs real vol vs ideal vol...
        Implied Vol: What the Options Implied Volatility is in the market.
        Ideal Vol: The minimum volatility required in order to reach a particular options Strike.
        Realized Vol: The current volatility over the past (x) days of the underlying used as input to Black Scholes Model.
    '''
    option_chain = black_scholes_pricer_entire_chain_vol(option_chain)
    option_chain = black_scholes_pricer_entire_chain(option_chain)
    ticker = option_chain.iloc[0]['Underlying']

    fig = plt.figure()
    plt.title(f'{ticker} Impl. Vol. vs. Real Vol. vs. Ideal Vol')

    call_or_put = option_chain.iloc[0]['call_or_put']
    if call_or_put == 'CALL':
        cols = ['BS_Call', 'Last Price', 'BS_Call_vol']
    else:
        cols = ['BS_Put', 'Last Price', 'BS_Put_vol']

    label = ['Idealized Vol','Implied Volatility', 'Real Vol']
    colors = ['red', 'blue','yellow']
    line_style = ['-.', '-', ':']
    for idx, col in enumerate(cols):
        plt.plot(option_chain['Strike'], option_chain[col], color=colors[idx], label=label[idx], linestyle=line_style[idx])
    plt.xlabel("Strikes", fontweight='bold')
    plt.ylabel("Price", fontweight='bold')
    plt.legend(loc="upper right")

    ax = plt.gca()
    ax.set_facecolor("black")

    return fig

# def main():
# #     # price an option
#     ticker = 'T'
#     # target_price = 16.37
#     # print(black_scholes_option_pricer(ticker, target_price, call_or_put='c', days=30))
# #     # visualize black scholes
#     t_chain = get_friday_options_chain_for_ticker_date(ticker='T', call_or_put='c', days=30, tries=0)
#     print(black_scholes_pricer_entire_chain(t_chain))
#     # visualize_impl_vs_real_combined(t_chain)
# main()
