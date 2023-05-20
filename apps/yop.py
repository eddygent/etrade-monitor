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
    today = datetime.today() + timedelta(days=30)
    friday = today + timedelta( (4-today.weekday()) % 7 )
    if to_str:
        return friday.strftime("%Y-%m-%d")
    return friday

def get_friday_options_chain_for_ticker_date(ticker = 'SPY', call_or_put = 'c' , days = 0):
    start = time.time()
    chain = yo.get_chain_greeks_date(stock_ticker=ticker, dividend_yield=None, option_type=call_or_put, expiration_date=friday_after_days_out(days, True), risk_free_rate=None)
    print(f'Getting {"Call" if call_or_put == "c" else "Put"} Options Chain for {ticker} took {time.time()-start} seconds.')
    return chain

def get_last_price(ticker):
    sym = yf.Ticker(ticker)
    fi = sym.fast_info
    return fi['lastPrice']


# chain = yo.get_chain_greeks_date(stock_ticker='TSLA', dividend_yield=1, option_type='p',
#                                  expiration_date='2023-05-19',risk_free_rate=None)
# print(chain)