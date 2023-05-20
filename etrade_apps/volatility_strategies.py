import pandas as pd
import numpy as np
import os
import sys

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path)
from volatility import *
from yop import *

def get_latest_vol_df(time_period='3mo'):
    filename = f'voldata/volatility_scanner_result_{TODAY}_{time_period}.csv'
    filepath = os.path.join(DATA_PATH, filename)
    if os.path.exists(filepath): df = pd.read_csv(filepath)
    else: df = tick_vol_runner(time_period)
    return df

def filter_vol_all_symbols_find_outliers(volatility_time_period='3mo',  volume = 0 ):
    '''
        Look for Symbols with yesterday's move greater than or equal to perc_move avg volatility within time period.
    '''
    dataframe = get_latest_vol_df(volatility_time_period)
    df = dataframe.copy()
    df = df[(abs(df['percentMove']) >= df['prevDayVolatility']) & (df['avgVolume'] > volume) ]
    return df.sort_values(by='avgVolume',ascending=False).reset_index(drop=True)

def filter_vol_all_symbols_find_vol(volatility_time_period='3mo', perc_move=.15, volume = 0, avg_vol=0.5):
    '''
        Look for Symbols with yesterday's move greater than perc_move, avg volume over given period of time
        greater than volume and avg volatility less than avg_vol.
    '''
    dataframe = get_latest_vol_df(volatility_time_period)
    df = dataframe.copy()
    df = df[(abs(df['percentMove'])  >= perc_move) & (df['prevDayVolatility']<avg_vol) & (df['avgVolume'] > volume)]
    return df.sort_values(by='avgVolume',ascending=False).reset_index(drop=True)

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