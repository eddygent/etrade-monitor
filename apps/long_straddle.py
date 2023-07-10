#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 04/07/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
from options_helper import *
from volatility import TODAY, tick_vol_runner
import pprint

def get_opportunistic_long_straddles(long_straddles:dict, min_edge=5):
    """
    edwgent - 2023-07-10
    @param long_straddles:
    @param min_edge:
    @return:
    """
    pass

def get_long_straddles(ticker,  days=0, vol_factor = 2, time_period_adj = 30):
    '''
    ticker:     Ticker of the underlying
    days:   how many days until expiration
    vol_factor:     what is the volatility factor that you want to use?
    time_period_adj:    how many extra days do we want to go out? by default if we pass in an expiry 30days out, we will get
        volatility back (30 days + time_period_adj (10)) = 40 days out
    '''
    # this function will get the long straddle strategies for the given ticker with a g, given time in days
    _time_period = f'{days+time_period_adj}d'
    chain = get_friday_options_chain_for_ticker_date(ticker, call_or_put, days )
    #TODO: Make sure this spot value is a) mean over days arg and b) need to use forward price for theo value of straddle?
    _,vol,curr_price,_ = volatility.ticker_volatilitymatrix_with_time_period(ticker, _time_period)
    adj_vol = vol/vol_factor
    straddles = {}
    #get ATM straddles...
    straddles['ranged_atm_with_vol'] = chain[chain['Strike'] == curr_price]
    #Get straddles that are 1/vol_factor up/down from spot...see how close we can find strikes to that up/downward vol factor limit
    #TODO: Depending on vol factor, expect different theo value for the straddles. E.g. if vol @ 20%, 10% up move = 1std, vol factor of 2 would find straddles with strikes at 5% upward move - OTM, cheaper but less EV
    straddles['ranged_up_with_vol_adj'] = chain[chain['Strike'].between(curr_price, curr_price*(1+(adj_vol/2)))]
    straddles['ranged_down_with_vol_adj'] = chain[chain['Strike'].between((1 - (adj_vol / 2)) * curr_price,curr_price)]
    #Get straddles at the upper and lower vol limits, for reference (if stock follows a 1std move, expect to make money 50% of the time for straddles at the limit - pay the biggest discount rel. to those within the vol factor strike range above
    straddles['ranged_upper_limit_vol'] =  chain[chain['Strike'] ==  curr_price*(1+(vol/2))]
    straddles['ranged_lower_limit_vol'] =  chain[chain['Strike'] ==  curr_price*(1-(vol/2))]
    (f'Volatility range of {days+time_period_adj} days is: {vol}, with adjusted volatility of: {adj_vol}.')
    long_straddles = []
    for strat, straddle_list in straddles.items():
        long_straddles.append(straddle_list.reset_index(drop=True))
    return long_straddles

def high_vol(date=TODAY, volatility_less_than = .1, volume_more_than=10000000):
    df = tick_vol_runner(time_period='3mo', date=date, test=False)
    #sort by vol
    df.sort_values(['volatility'])
    print(df)
    high_vol = df.query(f"volatility > {volatility_less_than} & avgVolume > {volume_more_than}")
    return high_vol

def iterate_through_high_vol(date=TODAY):
    high_vol_df = high_vol(date)
    long_straddles = {}
    for index, row in high_vol_df.iterrows():
        long_straddles[row['ticker']] = get_long_straddles(row['ticker'], days=30, vol_factor = 2, time_period_adj = 30)
        long_straddles[row['ticker']]['volatility'] = row['volatility']
    return long_straddles

def main():
    # ticker = 'KMI'
    # print(short_strangle_vol_neutral(ticker, days=30, vol_factor = 2, time_period_adj = 30, put_chain=pd.DataFrame(), call_chain=pd.DataFrame()))
    pprint.pprint(iterate_through_high_vol())

if __name__ == '__main__':
    main()