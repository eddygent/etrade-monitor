#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 04/07/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
from options_helper import *
from volatility import TODAY, tick_vol_runner, ticker_volatility_matrix_with_time_period
import pprint
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

    days_to_expiry = _spc["dte"]

    max_credit = float(_scc[method]) + float(_spc[method])
    break_even_range = (float(_spc[STRIKE]) - float(_spc[method]), float(_scc[STRIKE]) + float(_scc[method]))

    entry_cost = (float(_spc[STRIKE]) * 100) + get_last_price(ticker) * 100
    profit_to_investment_ratio = (max_credit * 100)/entry_cost

    year_dte_ratio = 365/days_to_expiry
    pos = {
        "position_df": short_strangle_vol_position,
        "break_even_range": break_even_range,
        "max_credit": max_credit,
        "max_profit": max_credit * 100,
        "profit_to_investment_ratio": profit_to_investment_ratio,
        "hypothetical_annualized_profit": year_dte_ratio*profit_to_investment_ratio ,
        "entry_cost": entry_cost
    }
    return pos

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

    days_to_expiry = _spc["dte"]

    max_credit = float(_scc[method]) + float(_spc[method])
    break_even_range = (float(_spc[STRIKE]) - float(_spc[method]), float(_scc[STRIKE]) + float(_scc[method]))

    entry_cost = (float(_spc[STRIKE]) * 100) + get_last_price(ticker) * 100
    profit_to_investment_ratio = (max_credit * 100) / entry_cost

    year_dte_ratio = 365 / days_to_expiry
    pos = {
        "position_df": short_strangle_vol_position,
        "break_even_range": break_even_range,
        "max_credit": max_credit,
        "max_profit": max_credit * 100,
        "profit_to_investment_ratio": profit_to_investment_ratio,
        "hypothetical_annualized_profit": year_dte_ratio * profit_to_investment_ratio,
        "entry_cost": entry_cost
    }
    return pos

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

    days_to_expiry = _spc["dte"]

    max_credit = float(_scc[method]) + float(_spc[method])
    break_even_range = (float(_spc[STRIKE]) - float(_spc[method]), float(_scc[STRIKE]) + float(_scc[method]))

    entry_cost = (float(_spc[STRIKE]) * 100) + get_last_price(ticker) * 100
    profit_to_investment_ratio = (max_credit * 100) / entry_cost

    year_dte_ratio = 365 / days_to_expiry
    pos = {
        "position_df": short_strangle_vol_position,
        "break_even_range": break_even_range,
        "max_credit": max_credit,
        "max_profit": max_credit * 100,
        "profit_to_investment_ratio": profit_to_investment_ratio,
        "hypothetical_annualized_profit": year_dte_ratio * profit_to_investment_ratio,
        "entry_cost": entry_cost
    }
    return pos


def get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=0, vol_factor = 2, time_period_adj = 30):
    '''
    ticker:     Ticker of the underlying
    call_or_put:    'c' for call and 'p' for put
    days:   how many days until expiration
    vol_factor:     what is the volatility factor that you want to use?
        ex...   if vol is at 8%, and curr price is at 100, we will grab the strikes 8/vol_factor (2) 4% up (104), and 4% down.
        note:   for more sensitive volatilities we will use a lower vol factor. for less sensitive use a higher vol factor
    time_period_adj:    how many extra days do we want to go out? by default if we pass in an expiry 30days out, we will get
        volatility back (30 days + time_period_adj (10)) = 40 days out
    '''
    # this function will get options within the volatility measure of strike price, given time in days
    _time_period = f'{days+time_period_adj}d'
    chain = get_friday_options_chain_for_ticker_date(ticker, call_or_put, days )
    _,vol,curr_price,_ = ticker_volatility_matrix_with_time_period(ticker, _time_period)
    adj_vol = vol / vol_factor
    ranged_with_vol = chain[chain['Strike'].between((1-adj_vol)*curr_price, curr_price*(1+adj_vol))]
    (f'Volatility range of {days+time_period_adj} days is: {vol}, with adjusted volatility of: {adj_vol}.')
    ranged_with_vol = ranged_with_vol.reset_index(drop=True)
    return ranged_with_vol

def low_vol(date=TODAY, volatility_less_than = .1, volume_more_than=10000000):
    df = tick_vol_runner(time_period='3mo', date=date, test=True)
    low_vol = df.query(f"volatility < {volatility_less_than} & avgVolume > {volume_more_than}")
    return low_vol

def iterate_through_low_vol(date=TODAY):
    low_vol_df = low_vol(date)
    short_strangles = {}
    for index, row in low_vol_df.iterrows():
        short_strangles[row['ticker']] = short_strangle_vol_neutral(row['ticker'], days=30, vol_factor = 2, time_period_adj = 30, put_chain=pd.DataFrame(), call_chain=pd.DataFrame())
        short_strangles[row['ticker']]['volatility'] = row['volatility']
    return short_strangles

def main():
    # ticker = 'KMI'
    # print(short_strangle_vol_neutral(ticker, days=30, vol_factor = 2, time_period_adj = 30, put_chain=pd.DataFrame(), call_chain=pd.DataFrame()))
    pprint.pprint(iterate_through_low_vol(date="20230707"))
if __name__ == '__main__':
    main()