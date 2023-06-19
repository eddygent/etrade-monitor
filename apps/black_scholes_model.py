import math
from datetime import datetime, timedelta
import os
import sys
import yfinance as yf
from volatility import TODAY

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + '/../')

import etrade_config
RATE = etrade_config.RATE  # Annualized risk free rate
from yop import get_friday_option_for_ticker_date_closest_to_price, get_friday_options_chain_for_ticker_date
import matplotlib.pyplot as plt


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
    return {"call": callPrice, "put": putPrice}

def black_scholes_price_date(S, K, date, sigma, divrate=0):
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
    return {"call": callPrice, "put": putPrice}


def black_scholes_price_date_target_price(S, K, date, targetPrice, divrate=0):
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

def black_scholes_option_pricer(ticker, target_price, days=30):
    option_chain = get_friday_option_for_ticker_date_closest_to_price(ticker=ticker, price=target_price, call_or_put='c',
                                                                      days=days, long=True)
    ticker = option_chain.iloc[0]['Underlying']
    bspricer = black_scholes_ticker_symbol(ticker, option_chain, target_price)
    return bspricer

def black_scholes_pricer_entire_chain(option_chain):

    option_chain['BS_Call'] = option_chain.apply(
        lambda row: black_scholes_price_date_target_price(yf.Ticker(row['Underlying']).fast_info['lastPrice'], row['Strike'], row['date'], row['Strike'])['call'], axis=1)
    option_chain['BS_Put'] = option_chain.apply(
        lambda row: black_scholes_price_date_target_price(yf.Ticker(row['Underlying']).fast_info['lastPrice'],
                                                          row['Strike'], row['date'], row['Strike'])['put'], axis=1)
    option_chain['BS_sigma'] = option_chain.apply(
        lambda row: black_scholes_price_date_target_price(yf.Ticker(row['Underlying']).fast_info['lastPrice'],
                                                          row['Strike'], row['date'], row['Strike'])['sigma'], axis=1)
    return option_chain

def visualize_impl_vs_real(option_chain):
    option_chain = black_scholes_pricer_entire_chain(option_chain)
    ticker = option_chain.iloc[0]['Underlying']

    plt.title(f'{ticker} Impl. Vol. vs. Real Vol.')

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

def main():
    # # inputs
    # undprice = 16.06  # S
    # strike = 16  # K
    # time = 24  # time until expiration in days
    #
    # sigma = .038  # Standard Deviation of stock's returns
    # divrate = 0  # Dividend yield on stock
    # print(black_scholes_price(S=undprice, K=strike, time=time, sigma=sigma))
    #
    # ticker = 'T'
    # targetPrice = 16.37
    # option_chain = get_friday_option_for_ticker_date_closest_to_price(ticker=ticker, price=targetPrice, call_or_put='c',
    #                                                                   days=30, long=True)
    # ticker = option_chain.iloc[0]['Underlying']
    # bspricer = black_scholes_ticker_symbol(ticker, option_chain, targetPrice)
    # print(bspricer)
    # print(bspricer.columns)
    # opt = black_scholes_option_pricer('T', 16.37)
    # print(opt)
    t_chain = get_friday_options_chain_for_ticker_date(ticker='T', call_or_put='c', days=30, tries=0)
    visualize_impl_vs_real(t_chain)
    # print(t_chain)
    # print(t_chain.columns)
    # t_chain = black_scholes_pricer_entire_chain(t_chain)
    # print(t_chain)
    # plt.figure()
    # plt.title("T")
    # cols = ['BS_Call', 'Last Price']
    # colors = ['red', 'blue']
    # line_style = ['-.', '-']
    # for idx, col in enumerate(cols):
    #     plt.plot(t_chain['Strike'], t_chain[col], color=colors[idx], linestyle=line_style[idx])
    # plt.xlabel("Strikes", fontweight='bold')
    # plt.ylabel("Price", fontweight='bold')
    #
    # ax = plt.gca()
    # ax.set_facecolor("black")
    #
    # plt.show()
main()
