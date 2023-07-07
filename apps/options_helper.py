# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
import yoptions as yo
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import time
import math
import volatility

# Chain of all FORD MOTOR COMPANY call options for next expiration date
# chain = yo.get_chain_greeks(stock_ticker='TSLA', dividend_yield=0, option_type='c', risk_free_rate=None)
# ideal = chain[chain['Delta'].between(.2, .3)]
# print(chain.head().to_string())

BID = "Bid"
LP = 'Last Price'
STRIKE = 'Strike'
def lastSymbolPrice(options_sym):
    '''
    get the last symbol price given a options symbol

    TODO: Make faster by passing in the option symbol base to get the last price using yfinance.Ticker.options
    '''
    return yo.get_plain_option_ticker(option_ticker=options_sym)['Last Price'][0]

def friday_after_days_out(days= 0, to_str = False):
    '''
    return the friday after days out
    '''
    today = datetime.today() + timedelta(days=days)
    friday = today + timedelta( (4-today.weekday()) % 7 )
    if to_str:
        return friday.strftime("%Y-%m-%d")
    return friday

def _get_friday_options_chain_for_ticker_date(ticker = 'SPY', call_or_put = 'c' , days = 0, tries=0):
    '''
    Get the friday options chain given a ticker and date - not used at the moment

    return df with options chain for either call or put
    '''
    start = time.time()
    try:
        # chain = yo.get_chain_greeks_date(stock_ticker=ticker, dividend_yield=None, option_type=call_or_put,
        #                                  expiration_date=friday_after_days_out(days, True), risk_free_rate=None)
        chain = get_chain_ticker_date(ticker, call_or_put, expiration_date=friday_after_days_out(days, True))
        if chain.empty:
            print(f"Error getting expiration date {friday_after_days_out(days, True)} for ticker: {ticker}, moving the days forward...")
            if tries == 14:
                print(f"Error getting the chain for: {ticker}")
                print(f"Tried: {tries} times. Returning Empty Dataframe.")
                return pd.DataFrame()
            chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put=call_or_put, days=days+7, tries=tries+1)
        print(f'Getting {"Call" if call_or_put == "c" else "Put"} Options Chain {friday_after_days_out(days, True)} days out for {ticker} took {time.time()-start} seconds.')
    except AttributeError:
        print(f"Error getting the chain for: {ticker}")
        print(f"Returning Empty Dataframe.")
        return pd.DataFrame()
    return chain

def get_chain_ticker_date(stock_ticker,option_type, expiration_date,week=None):
    '''
    get the chain for either calls or puts using yfinance.Ticker.option_chain lib and return for usage
    '''
    ticker = yf.Ticker(stock_ticker)
    try:
        opt = ticker.option_chain(expiration_date)
    except ValueError as e:
        print(f'Got ValueError: {e} when getting options chain. Returning empty to move forward.')
        return pd.DataFrame()
    #     add_7 = datetime.strptime(expiration_date,"%Y-%m-%d")+timedelta(days=7)
    #     print("Moving forward expiraiton date 7 days - not present.")
    #     get_chain_ticker_date(stock_ticker, option_type, add_7.strftime("%Y-%m-%d"))
    if option_type == 'c':
        opt = opt.calls
    elif option_type == 'p':
        opt = opt.puts
    elif option_type == '*':
        opt = pd.concat([opt.puts,opt.calls])
    if week!=None:
        opt['Week'] = week
    return opt

def get_friday_options_chain_for_ticker_date(ticker = 'SPY', call_or_put = 'c' , days = 0, tries=0, inclusive=False):
    '''
    Get the friday options chain given a ticker and date

    return df with options chain for either call or put
    '''
    start = time.time()
    try:
        print(f'Trying to get the options chain for: {ticker}.')
        if not inclusive:
            chain = get_chain_ticker_date(ticker, call_or_put, expiration_date=friday_after_days_out(days, True))
        else:
            chain = pd.DataFrame()
            for week in range(0,int(math.ceil(days/7))+1):
                chain = pd.concat([chain,get_chain_ticker_date(ticker, call_or_put, expiration_date=friday_after_days_out(week*7, True),week=week)])
        if chain.empty:
            print(f"Error getting expiration date {friday_after_days_out(days, True)} for ticker: {ticker}, moving the days forward...")
            if tries == 14:
                print(f"Error getting the chain for: {ticker}")
                print(f"Returning Empty Dataframe.")
                return pd.DataFrame()
            chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put=call_or_put, days=days+7, tries=tries+1)
        all_opts_str = f'{"Put" if call_or_put == "p" else "All"}'
        print(f'Getting {"Call" if call_or_put == "c" else all_opts_str} Options Chain {friday_after_days_out(days, True)} days out for {ticker} took {time.time()-start} seconds.')
    except ValueError:
        print(f"Error getting the chain for: {ticker}")
        print(f"Returning Empty Dataframe.")
        return pd.DataFrame()
    # rename columns to match that of the previous
    try:
        if not inclusive:
            chain = chain.rename(columns={'lastPrice': 'Last Price', 'bid': 'Bid','ask':'Ask', 'volume':'Volume', 'openInterest': 'Open Interest', 'contractSymbol':'Symbol', 'impliedVolatility': 'Implied Volatility', 'lastTradeDate':'Last Trade', 'strike':'Strike'})
        else:
            chain = chain.rename(columns={'Week':'Expiry Weeks Out','lastPrice': 'Last Price', 'bid': 'Bid','ask':'Ask', 'volume':'Volume', 'openInterest': 'Open Interest', 'contractSymbol':'Symbol', 'impliedVolatility': 'Implied Volatility', 'lastTradeDate':'Last Trade', 'strike':'Strike'})
    except Exception as e:
        print(f"In the original Form: {chain.columns}")
    chain['date'] = friday_after_days_out(days, True)
    if call_or_put == 'c': chain['call_or_put'] = 'CALL'
    elif call_or_put == 'p':
        chain['call_or_put'] = 'PUT'
    chain['Underlying'] = ticker
    return chain

def get_friday_option_for_ticker_date_closest_to_price(ticker = 'SPY', price=330, call_or_put = 'c' , days = 0, long=True):
    '''
    Get friday option for ticker and date closest to given price
    '''
    try:
        chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put=call_or_put, days=days)
    except IndexError:
        print("IndexError with", ticker)
        return pd.DataFrame()
    try:
        # return the options strike with value closest to target price
        strike = None
        diff = float('inf')
        for K in chain['Strike'].values:
            if abs(price-K) < diff:
                diff = abs(price-K)
                strike = K
    except KeyError as e:
        print(f"Error, {e}, Unable to get Options Chain for: {ticker}")
        return pd.DataFrame()
    abs_diff = abs(price-strike)
    chain = chain[chain['Strike'].between(price-abs_diff, price+abs_diff)]
    # drop unused columns
    chain = chain.drop(['contractSize', 'currency', 'change', 'percentChange', 'Last Trade'], axis=1)
    chain['Underlying'] = ticker
    if (long and call_or_put == 'c') or (not long and call_or_put == 'p'):
        # return conservative bull position
        return chain.head(1)
    else:
        # return conservative bear position
        return chain.tail(1)
def get_last_price(ticker):
    sym = yf.Ticker(ticker)
    fi = sym.fast_info
    return fi['lastPrice']

# print(get_friday_options_chain_for_ticker_date(ticker = 'SPY', call_or_put = 'c' , days = 0, tries=0))
# print(get_friday_option_for_ticker_date_closest_to_price(ticker = 'SPY', price=400, call_or_put = 'c' , days = 0, long=True))