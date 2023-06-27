#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 02/06/2023
# Email       : kori.s.vernon@gmail.com
# ----------------------------------------------------------------------------
import os
import sys

import pandas as pd

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path)
from volatility import *
from yop import *
from pretty_html_table import build_table
from email_summary import send_email_with_data
script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_path, ".."))
import etrade_config

EXCLUDE = pd.read_csv(os.path.join(DATA_PATH, 'exclude.csv'))['ticker'].values

import logging
level = logging.DEBUG
fmt =  "[%(levelname)s] [apps/volatility_strategies.py] %(asctime)-15s %(message)s"
logging.basicConfig(level=level, format=fmt)

from black_scholes_model import black_scholes_ticker_symbol_vol
def get_latest_vol_df(time_period='3mo', date=TODAY):
    return tick_vol_runner(time_period,date=date)

def speculate_percent_move(percent_move, volatility, prev_day_volatility):
    weight = abs(volatility-prev_day_volatility)
    if abs(percent_move) >= 1.98: return .9999 * -1
    if percent_move < 0:
        # return (1 + (percent_move * weight * -1)) * last_price
        return round((percent_move * weight * -1), 2)
    else:
        # return (1 - (percent_move * weight * -1)) * last_price
        return round((percent_move * weight * -1), 2)

def speculate_price(spec_perc_move, last_price):
    if spec_perc_move == -.9999: spec_perc_move = -.2 # conservative with -.2
    return (1 + spec_perc_move) * last_price

def filter_vol_all_symbols_find_outliers(volatility_time_period='3mo',  volume = 0,date=TODAY, to_html=False, dataframe=pd.DataFrame()):
    '''
        Look for Symbols with yesterday's move greater than or equal to perc_move avg volatility within time period.
    '''
    ret_str = f"Symbols with yesterday's move greater than or equal to the average volatility within {volatility_time_period} time period, and avg volume over given period of time greater than {'{:.2f} M'.format(float(volume)/1000000)}."
    dataframe = get_latest_vol_df(volatility_time_period, date=date)
    df = dataframe.copy()
    df = df[(abs(df['percentMove']) >= df['prevDayVolatility']) & (df['avgVolume'] > volume) ]
    df['speculativePercMove'] = df.apply(lambda row : speculate_percent_move(row['percentMove'], row['volatility'], row['prevDayVolatility']), axis = 1)
    df = df.sort_values(by='avgVolume', ascending=False)

    df['lastPrice'] = df.apply(lambda row: round(row['lastPrice'], 2), axis=1)
    df['percentMove'] = df.apply(lambda row: round(row['percentMove'], 2), axis=1)
    df['volatility'] = df.apply(lambda row: round(row['volatility'], 2), axis=1)
    df['prevDayVolatility'] = df.apply(lambda row: round(row['prevDayVolatility'], 2), axis=1)
    if to_html:
        ret_df = df.copy()
        df['yFinance Link'] = 'https://finance.yahoo.com/quote/' + df['ticker']
        df['avgVolume'] = df.apply(lambda row: "{:.2f} M".format(float(row['avgVolume'] / 1000000)), axis=1)

        df['speculativePercMove'] = df.apply(lambda row: "{:}".format(int(row['speculativePercMove'] * 100)), axis=1)
        df['percentMove'] = df.apply(lambda row: "{:}".format(int(row['percentMove'] * 100)), axis=1)

        df = df.rename(
            columns={'speculativePercMove': 'spec%Move', 'prevDayVolatility': 'prevDayVol', 'volatility': 'vol',
                     'percentMove': '%Move'})
        return build_table(df.reset_index(drop=True), 'orange_light'), ret_df, ret_str, dataframe
    else:
        df['avgVolume'] = df.apply(lambda row: "{:.2f} M".format(float(row['avgVolume'] / 1000000)), axis=1)
    return df.reset_index(drop=True), ret_str, dataframe

def filter_vol_all_symbols_find_vol(volatility_time_period='3mo', perc_move=.15, volume = 0, avg_vol=0.5, date=TODAY, to_html=False, dataframe=pd.DataFrame()):
    '''
        Look for Symbols with yesterday's move greater than perc_move, avg volume over given period of time
        greater than volume and avg volatility less than avg_vol.
    '''
    ret_str = f"Symbols with yesterday's move greater than percentage move {perc_move}, avg volume over given period of time greater than {'{:.2f} M'.format(float(volume)/1000000)}, and avg volatility less than {avg_vol}; an outlier with relatively low volatility."
    dataframe = get_latest_vol_df(volatility_time_period, date=date)
    df = dataframe.copy()
    df = df[(abs(df['percentMove'])  >= perc_move) & (df['prevDayVolatility']<avg_vol) & (df['avgVolume'] > volume)]
    df['speculativePercMove'] = df.apply(lambda row : speculate_percent_move(row['percentMove'], row['volatility'], row['prevDayVolatility']), axis = 1)
    df = df.sort_values(by='avgVolume', ascending=False)

    df['lastPrice'] = df.apply(lambda row: round(row['lastPrice'], 2), axis=1)
    df['percentMove'] = df.apply(lambda row: round(row['percentMove'], 2), axis=1)
    df['volatility'] = df.apply(lambda row: round(row['volatility'], 2), axis=1)
    df['prevDayVolatility'] = df.apply(lambda row: round(row['prevDayVolatility'], 2), axis=1)

    if to_html:
        ret_df = df.copy()
        df['yFinance Link'] = 'https://finance.yahoo.com/quote/' + df['ticker']
        df['avgVolume'] = df.apply(lambda row: "{:.2f} M".format(float(row['avgVolume']/1000000)), axis = 1)

        df['speculativePercMove'] = df.apply(lambda row: "{:}".format(int(row['speculativePercMove'] * 100)), axis=1)
        df['percentMove'] = df.apply(lambda row: "{:}".format(int(row['percentMove'] * 100)), axis=1)

        df = df.rename(
            columns={'speculativePercMove': 'spec%Move', 'prevDayVolatility': 'prevDayVol', 'volatility': 'vol',
                     'percentMove':'%Move'})
        return build_table(df.reset_index(drop=True), 'orange_light'), ret_df, ret_str, dataframe
    else:
        df['avgVolume'] = df.apply(lambda row: "{:.2f} M".format(float(row['avgVolume']/1000000)), axis = 1)
    return df.reset_index(drop=True), ret_str, dataframe

def generate_options_positions(df, to_html = False):
    df['specPrice'] = df.apply(lambda row: speculate_price(row['speculativePercMove'], row['lastPrice']), axis=1)
    positions = pd.DataFrame()
    for index, row in df.iterrows():
        try:
            determined_position = determine_option_position(row['ticker'], row['percentMove'], row['specPrice'], row['avgVolume'])
            determined_position['speculativePercMove'] = row['speculativePercMove']
            determined_position['prevDayVolatility'] = row['prevDayVolatility']
            determined_position['volatility'] = row['volatility']
            determined_position['lastPrice'] = row['lastPrice']
            determined_position = black_scholes_ticker_symbol_vol(row['ticker'],determined_position)
            positions = pd.concat([positions, determined_position])
        except Exception as e:
            print(f'[generate_positions] Failed to get a dataframe for an option Contract. continuing')
            continue
    positions.to_csv(os.path.join(DATA_PATH, f'generated_positions_{TODAY}.csv'))
    positions = positions.reset_index()
    if to_html:
        try:
            html_positions = positions.copy()[
                ['Symbol', 'Position', 'Strike', 'Last Price', 'Volume', 'Open Interest', 'Implied Volatility','BS_sigma_vol','BS_Call_vol','BS_Put_vol']
            ]
            html_positions = html_positions.rename(columns={'Implied Volatility': 'IV', 'Last Price':'S', 'Strike':'K','BS_sigma_vol':'BSσ','BS_Call_vol':'BSC','BS_Put_vol':'BSP'})
        except Exception as e:
            return f"[generate_positions] Error Generating Positions.<br>Snippet of error: <br>{e}<br><br>",pd.DataFrame()
        html_positions = html_positions.reset_index(drop=True)
        return build_table(html_positions, 'blue_light'), positions
    return positions

def generate_stock_positions(df, to_html = False):
    df['specPrice'] = df.apply(lambda row: speculate_price(row['speculativePercMove'], row['lastPrice']), axis=1)
    positions = pd.DataFrame()
    for index, row in df.iterrows():
        try:
            determined_position = determine_stock_position(row['ticker'], row['percentMove'], row['specPrice'], row['avgVolume'])
            determined_position['speculativePercMove'] = row['speculativePercMove']
            determined_position['prevDayVolatility'] = row['prevDayVolatility']
            determined_position['volatility'] = row['volatility']
            determined_position['lastPrice'] = row['lastPrice']
            positions = pd.concat([positions, determined_position])
        except Exception as e:
            print(f'[generate_positions] Failed to get a dataframe for an option Contract. continuing')
            continue
    positions.to_csv(os.path.join(DATA_PATH, f'generated_positions_{TODAY}.csv'))
    positions = positions.reset_index()
    if to_html:
        try:
            html_positions = positions.copy()[
                ['Ticker', 'Position', 'lastPrice','volatility','prevDayVolatility','percMove', 'spec_price']
            ]
        except Exception as e:
            return f"[generate_positions] Error Generating Stock Positions.<br>Snippet of error: <br>{e}<br><br>",pd.DataFrame()
        html_positions = html_positions.rename(columns={'prevDayVolatility':'prevVol'})
        html_positions = html_positions.reset_index(drop=True)
        return build_table(html_positions, 'blue_light'), positions
    return positions

def vol_scraper_outliers_data(date=TODAY, to_html = True):
    try:
        convert_date = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError as e:
        logging.info(f"[vol_scraper_outliers_data] {e}\nError. Trying to use different date format")
        convert_date = date
        logging.info(f'Converting date to: {convert_date}')
    filename = f'voldata/volatility_scanner_result_{convert_date}_3mo.csv'
    filepath = os.path.join(DATA_PATH, filename)
    logging.info(f"Searching for: {filepath}... {os.path.exists(filepath)}")
    if os.path.exists(filepath):
        logging.info("Path Exists... Opening file")
        df = pd.read_csv(filepath)
        df = df[~df['ticker'].isin(EXCLUDE)]
        find_vol, vol_res, str_vol, df = filter_vol_all_symbols_find_vol(volume=1000000, to_html=True, dataframe=df, date=date)
        logging.info(f'Result of filter_vol_all_symbols_find_vol:\n{df}')
        find_out, vol_out, str_out, df = filter_vol_all_symbols_find_outliers(volume=1000000, to_html=True, dataframe=df,date=date)
        logging.info(f'Result of filter_vol_all_symbols_find_outliers:\n{df}')
    else:
        find_vol, vol_res, str_vol, df = filter_vol_all_symbols_find_vol(volume=1000000, to_html=True)
        logging.info(f'Result of filter_vol_all_symbols_find_vol:\n{df}')
        find_out, vol_out, str_out, df = filter_vol_all_symbols_find_outliers(volume=1000000, to_html=True, dataframe=df)
        logging.info(f'Result of filter_vol_all_symbols_find_outliers:\n{df}')
    # concat and find unique
    df = pd.concat([vol_res, vol_out])
    df = df.drop_duplicates(ignore_index=True)
    # send an email with the volatility outliers before generating positions in the event generate positions fails
    volatility_outliers_email = \
        f"""
            <h1>Volatility Outliers: {date}</h1>
                {str_vol}<br>
                {find_vol}<br>
                {str_out}<br>
                {find_out}<br>
                <em>Note: If the percent move is greater than 198% the speculative percentage move is defaulted to -0.99 and further investigation is suggested.</em>
            """
    try:
        options_positions_html, positions = generate_options_positions(df, to_html = True)
    except Exception as e:
        logging.info(f'WE HIT AN EXCEPTION WHILE GENERATING OPTIONS POSITIONS: \n{e}')
        options_positions_html,positions = "Exception hit while generating positions.", pd.DataFrame()
    volatility_outliers_email_with_options_positions = volatility_outliers_email + \
        f""" 
        <h2>Options Positions</h2>
        {options_positions_html}
        <em>Note: These positions are not screened and were generated programatically using a Volatility Based Mean Reversion Quantitative Method</em>
        """
    stock_positions_html, stock_positions = generate_stock_positions(df, to_html=True)
    volatility_outliers_email_with_stock_positions = volatility_outliers_email_with_options_positions + \
        f"""
        <h2>Stock Positions</h2>
        {stock_positions_html}
        <em>Note: These positions are not screened and were generated programatically using a Volatility Based Mean Reversion Quantitative Method</em>
        """

    vol_out_email = volatility_outliers_email_with_stock_positions
    if to_html:
        return vol_out_email, positions
    else:
        return positions

def determine_option_position(ticker, perc_move, spec_price, volume):
    perc_move = perc_move *-1
    if perc_move > 0:
        if volume < 20000000: # if volume less than 20M
            # long call - bull
            call_or_put = 'c'
            long = True
            position = 'Long Call'
        else: # short put - bull
            call_or_put = 'p'
            long = False
            position = 'Short Put'
    else: #long put - bear
        if volume < 15000000:
            call_or_put = 'p'
            long = True
            position = 'Long Put'
        else: # short call -bear
            call_or_put = 'c'
            long = False
            position = 'Short Call'
    # try:
    chain = get_friday_option_for_ticker_date_closest_to_price(ticker=ticker, price=spec_price, call_or_put=call_or_put, days=30, long=long)
    # except Exception as e:
    #     logging.info(f'HIT EXCEPTION WHILE GETTING FRIDAY OPTIONS FOR DATE CLOSEST TO PRICE!!!\n{e}')
    #     chain = pd.DataFrame()
    if chain.empty:
        logging.info(f'Unable to get Options Chain for {ticker}.')
        return chain
    print("Adding",position,ticker,"Options Strat")
    chain['Position'] = position
    chain['Ticker'] = ticker
    chain['percMove'] = perc_move
    return chain

def determine_stock_position(ticker, perc_move, spec_price, volume):
    stock_pos = {}
    perc_move = perc_move
    if perc_move > 0:
        position = 'Short'
    else:
        position = 'Long'
    print("Adding",position,ticker,"Stock Strat as Perc Move is:", perc_move)
    stock_pos['Ticker'] = ticker
    stock_pos['Position'] = position
    stock_pos['percMove'] = perc_move
    stock_pos['spec_price'] = spec_price
    stock_pos['volume'] = volume
    stock_pos = pd.DataFrame(stock_pos, index=[0])
    print(stock_pos)
    return stock_pos

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
    (f'Volatility range of {days+time_period_adj} days is: {vol}, with adjusted volatility of: {adj_vol}.')
    ranged_with_vol = ranged_with_vol.reset_index(drop=True)
    return ranged_with_vol

# def main():
#     # ticker = 'TSLA'
#     # put_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='p', days=30)
#     # call_chain = get_options_chain_within_vol_of_strike_given_time(ticker, call_or_put='c', days=30)
#     # # df = get_options_chain_within_vol_of_strike_given_time(ticker='TSLA', call_or_put='p', days=30, vol_factor=4)
#     # print('short strangle skewed down')
#     # sssd = short_strangle_vol_skewed_down(ticker='TSLA', put_chain=put_chain, call_chain=call_chain)
#     # print(sssd)
#     #
#     # print('short strangle neutral')
#     # ssn = short_strangle_vol_neutral(ticker='TSLA', put_chain=put_chain, call_chain=call_chain)
#     # print(ssn)
#     #
#     # print('short strangle skewed up')
#     # sssu = short_strangle_vol_skewed_up(ticker='TSLA', put_chain=put_chain, call_chain=call_chain)
#     # print(sssu)
#     print(vol_scraper_email_str('2023-05-29'))
# main()