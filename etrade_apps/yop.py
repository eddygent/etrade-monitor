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

# short strangle
def short_strangle_vol_neutral(ticker, days=0, vol_factor = 2, time_period_adj = 30, put_chain=pd.DataFrame(), call_chain=pd.DataFrame()):
    '''
    short a call and short a put atm + vol/vol_factor given time period
    '''

    # sell a put
    if put_chain.empty:
        put_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='p', days=days, vol_factor=vol_factor, time_period_adj=time_period_adj)
    short_put_contract = put_chain.head(1) # itm put
    # sell a call
    if call_chain.empty:
        call_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=days, vol_factor=vol_factor, time_period_adj=time_period_adj)
    short_call_contract = call_chain.tail(1) # itm call
    # combine positions
    short_strangle_vol_position = pd.concat([short_put_contract, short_call_contract]) # position dataframe

    spc = short_put_contract.head(1)
    scc = short_call_contract.head(1)

    _spc = spc.iloc[0]
    _scc = scc.iloc[0]
    method = BID if float(_spc[BID]) != 0 else LP

    max_credit = float(_scc[method]) + float(_spc[method])
    break_even_range = (float(_spc[STRIKE]) - float(_spc[method]), float(_scc[STRIKE]) + float(_scc[method]))

    return short_strangle_vol_position, break_even_range, max_credit

def short_strangle_vol_skewed_up(ticker, days=0, vol_factor = 2, time_period_adj = 30, put_chain=pd.DataFrame(), call_chain=pd.DataFrame()):
    '''
    short a call and short a put [skewed up] with atm put and (itm call + vol/vol_factor) given time period
    '''
    # sell a put
    if put_chain.empty:
        put_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='p', days=days, vol_factor=vol_factor, time_period_adj=time_period_adj)
    mid = int(put_chain.shape[0]/2)
    short_put_contract = put_chain.iloc[mid:mid+1] # atm put - double check method

    # sell a call
    if call_chain.empty:
        call_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=days, vol_factor=vol_factor, time_period_adj=time_period_adj)
    short_call_contract = call_chain.tail(1) # itm call
    # combine positions
    short_strangle_vol_position = pd.concat([short_put_contract, short_call_contract]) # position dataframe

    _spc = short_put_contract.iloc[0]
    _scc = short_call_contract.iloc[0]
    method = BID if float(_spc[BID]) != 0 else LP

    max_credit = float(_scc[method]) + float(_spc[method])
    break_even_range = (float(_spc[STRIKE]) - float(_spc[method]), float(_scc[STRIKE]) + float(_scc[method]))

    return short_strangle_vol_position, break_even_range, max_credit

def short_strangle_vol_skewed_down(ticker, days=0, vol_factor = 2, time_period_adj = 30, put_chain=pd.DataFrame(), call_chain=pd.DataFrame()):
    '''
    short a call and short a put [skewed down] with atm call and (atm call - vol/vol_factor) given time period
    '''
    # sell a put
    if put_chain.empty:
        put_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='p', days=days, vol_factor=vol_factor, time_period_adj=time_period_adj)
    short_put_contract = put_chain.head(1)

    # sell a call
    if call_chain.empty:
        call_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=days, vol_factor=vol_factor, time_period_adj=time_period_adj)
    mid = int(call_chain.shape[0] / 2)
    short_call_contract = call_chain.iloc[mid:mid+1] # atm put - double check method

    # combine positions
    short_strangle_vol_position = pd.concat([short_put_contract, short_call_contract]) # position dataframe

    _spc = short_put_contract.iloc[0]
    _scc = short_call_contract.iloc[0]
    method = BID if float(_spc[BID]) != 0 else LP

    max_credit = float(_scc[method]) + float(_spc[method])
    break_even_range = (float(_spc[STRIKE]) - float(_spc[method]), float(_scc[STRIKE]) + float(_scc[method]))

    return short_strangle_vol_position, break_even_range, max_credit


def get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=0, vol_factor = 2, time_period_adj = 30):
    # this function will get options within the volatility measure of strike price, given time in days
    # volatility will check back days+30
    _time_period = f'{days+time_period_adj}d'
    chain = get_friday_options_chain_for_ticker_date(ticker, call_or_put, days )
    _,vol,curr_price,_ = volatility.ticker_volatility_matrix_with_time_period(ticker, _time_period)
    adj_vol = vol / vol_factor
    ranged_with_vol = chain[chain['Strike'].between((1-adj_vol)*curr_price, curr_price*(1+adj_vol))]
    print(f'Volatility range of {days+time_period_adj} days is: {vol}, with adjusted volatility of: {adj_vol}.')
    ranged_with_vol = ranged_with_vol.reset_index(drop=True)
    return ranged_with_vol

def main():
    print("working")
    ticker = 'TSLA'
    put_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='p', days=30)
    call_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=30)
    # df = get_options_chain_within_vol_of_strike_given_time(ticker='TSLA', call_or_put='p', days=30, vol_factor=4)
    print('short strangle skewed down')
    sssd = short_strangle_vol_skewed_down(ticker='TSLA', put_chain=put_chain, call_chain=call_chain)
    print(sssd)

    print('short strangle neutral')
    ssn = short_strangle_vol_neutral(ticker='TSLA', put_chain=put_chain, call_chain=call_chain)
    print(ssn)

    print('short strangle skewed up')
    sssu = short_strangle_vol_skewed_up(ticker='TSLA', put_chain=put_chain, call_chain=call_chain)
    print(sssu)
main()


# chain = yo.get_chain_greeks_date(stock_ticker='TSLA', dividend_yield=1, option_type='p',
#                                  expiration_date='2023-05-19',risk_free_rate=None)
# print(chain)