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
import volatility

# Chain of all FORD MOTOR COMPANY call options for next expiration date
# chain = yo.get_chain_greeks(stock_ticker='TSLA', dividend_yield=0, option_type='c', risk_free_rate=None)
# ideal = chain[chain['Delta'].between(.2, .3)]
# print(chain.head().to_string())

BID = "Bid"
LP = 'Last Price'
STRIKE = 'Strike'
def friday_after_days_out(days= 0, to_str = False):
    today = datetime.today() + timedelta(days=days)
    friday = today + timedelta( (4-today.weekday()) % 7 )
    if to_str:
        return friday.strftime("%Y-%m-%d")
    return friday

def get_friday_options_chain_for_ticker_date(ticker = 'SPY', call_or_put = 'c' , days = 0):
    start = time.time()
    chain = yo.get_chain_greeks_date(stock_ticker=ticker, dividend_yield=None, option_type=call_or_put, expiration_date=friday_after_days_out(days, True), risk_free_rate=None)
    try:
        if chain.empty:
            print(f"Error getting expiration date {friday_after_days_out(days, True)}, moving the days forward...")
            chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put=call_or_put, days=days+7)
        print(f'Getting {"Call" if call_or_put == "c" else "Put"} Options Chain {friday_after_days_out(days, True)} days out for {ticker} took {time.time()-start} seconds.')
    except AttributeError:
        print(f"Error getting the chain for:\n{chain}")
        print(f"Returning Empty Dataframe.")
        return pd.DataFrame()
    return chain

def get_friday_option_for_ticker_date_closest_to_price(ticker = 'SPY', price=330, call_or_put = 'c' , days = 0, long=True):
    try:
        chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put=call_or_put, days=days)
    except IndexError:
        print("IndexError with", ticker)
        return pd.DataFrame()
    try:
        print(chain)
        strike = min(chain['Strike'].values, key=lambda x: abs(price-x))
    except Exception as e:
        print(f"Error, {e}, Unable to get Options Chain for: {ticker}")
        return pd.DataFrame()
    abs_diff = abs(price-strike)
    chain = chain[chain['Strike'].between(abs_diff - price, price+abs_diff)]
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

# chain = yo.get_chain_greeks_date(stock_ticker='TSLA', dividend_yield=1, option_type='p',
#                                  expiration_date='2023-05-19',risk_free_rate=None)
# print(chain)