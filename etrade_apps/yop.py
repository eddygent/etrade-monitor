import yoptions as yo
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import time
import volatility
# Chain of all FORD MOTOR COMPANY call options for next expiration date
# chain = yo.get_chain_greeks(stock_ticker='TSLA', dividend_yield=0, option_type='c', risk_free_rate=None)
# ideal = chain[chain['Delta'].between(.2, .3)]
# print(chain.head().to_string())

# print(ideal)

def friday_after_days_out(days= 0, to_str = False):
    today = datetime.today() + timedelta(days=30)
    friday = today + timedelta( (4-today.weekday()) % 7 )
    if to_str:
        return friday.strftime("%Y-%m-%d")
    return friday

def get_friday_options_chain_for_ticker_date(ticker = 'SPY', call_or_put = 'c' , days = 0):
    start = time.time()
    chain = yo.get_chain_greeks_date(stock_ticker=ticker, dividend_yield=0 , option_type=call_or_put, expiration_date=friday_after_days_out(days, True))
    print(f'Getting Options Chain for {ticker} took {time.time()-start} seconds.')
    return chain

def get_last_price(ticker):
    sym = yf.Ticker(ticker)
    fi = sym.fast_info
    return fi['lastPrice']

def get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=0, vol_factor = 2, time_period_adj = 30):
    # this function will get options within the volatility measure of strike price, given time in days
    # volatility will check back days+30
    _time_period = f'{days+time_period_adj}d'
    chain = get_friday_options_chain_for_ticker_date(ticker, call_or_put, days )
    _,vol,curr_price,_ = volatility.ticker_volatility_matrix_with_time_period(ticker, f"{_time_period}")
    adj_vol = vol / vol_factor
    ranged_with_vol = chain[chain['Strike'].between((1-adj_vol)*curr_price, curr_price*(1+adj_vol))]
    print(f'Volatility range of {days+time_period_adj} days is: {vol}, with adjusted volatility of: {adj_vol}.')
    return ranged_with_vol

def main():
    print("working")
    df = get_options_chain_within_vol_of_strike_given_time(ticker='TSLA', call_or_put='p', days=30)
    print(df)
main()
# we want to get options date that is after x days out
# get last day of week