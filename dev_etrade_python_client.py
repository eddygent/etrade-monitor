#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
import socket
import datetime
import webbrowser
import json
import logging
import configparser
import sys
import requests
from rauth import OAuth1Service
from logging.handlers import RotatingFileHandler
from accounts.accounts import Accounts
<<<<<<< HEAD
=======
# from apps.sentiment_analysis import scrape_articles_determine_sentiment_and_send_email
>>>>>>> 8d7beb3566c506a15e759bb37f69ec75e5195585

from market.market import Market
import time
import argparse
from inputimeout import inputimeout, TimeoutOccurred
import etrade_config
import os
script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + "/apps")
import apps.volatility
<<<<<<< Updated upstream
from apps.sentiment_analysis import scrape_articles_determine_sentiment_and_send_email
<<<<<<< HEAD
=======
#from apps.sentiment_analysis import scrape_articles_determine_sentiment_and_send_email
>>>>>>> Stashed changes
from apps.email_summary import send_email_with_data, get_accounts_hold, account_summary,get_accounts_sell
=======
from apps.email_summary import send_email_with_data, get_accounts_hold, account_summary,get_accounts_sell,vol_surface_summary,send_email_with_images
>>>>>>> 8d7beb3566c506a15e759bb37f69ec75e5195585
from apps.volatility_strategies import *
#from apps.sentiment_analysis import *
#from apps.firebase_administrator import *
from apps.black_scholes_model import *

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + "/apps")

import os
base = os.getcwd()
# logger settings
level = logging.DEBUG
fmt =  "[%(levelname)s] [dev_etrade_python_client.py] %(asctime)-15s %(message)s"
logging.basicConfig(level=level, format=fmt)

def oauth():
    """Allows user authorization for the sample application with OAuth 1"""
    etrade = OAuth1Service(
        name="etrade",
        consumer_key=etrade_config.CONSUMER_KEY,
        consumer_secret=etrade_config.CONSUMER_SECRET,
        request_token_url="https://api.etrade.com/oauth/request_token",
        access_token_url="https://api.etrade.com/oauth/access_token",
        authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
        base_url="https://api.etrade.com")

    base_url = etrade_config.PROD_BASE_URL

    # Step 1: Get OAuth 1 request token and secret
    request_token, request_token_secret = etrade.get_request_token(
        params={"oauth_callback": "oob", "format": "json"})

    # Step 2: Go through the authentication flow. Login to E*TRADE.
    # After you login, the page will provide a verification code to enter.
    authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
    webbrowser.open(authorize_url)
    text_code = input("Please accept agreement and enter verification code from browser: ")

    # Step 3: Exchange the authorized request token for an authenticated OAuth 1 session
    session = etrade.get_auth_session(request_token,
                                  request_token_secret,
                                  params={"oauth_verifier": text_code})
    return session, base_url

def can_i_sell(ticker, AccountsObj):
    logging.info(f"can_i_sell(ticker={ticker}, AccountsObj={AccountsObj}) on host: {socket.gethostname()}")
    for acc in AccountsObj.accounts:
        contents = AccountsObj.accounts_holdings[acc.accountId]._can_sell()
        for tk,qty in contents:
            if ticker.upper() in tk.upper():
                logging.info(f"Can Sell: {tk} and Qty: {qty}")
    tk = input("Check Ticker For Ability to Sell (e to exit): ")
    if tk.lower() == "e":
        return
    can_i_sell(tk, AccountsObj)

def load_accounts(session, base_url):
    logging.info(f"load_accounts(session={session},base_url={base_url}) on host: {socket.gethostname()}")
    accounts = Accounts(session, base_url)
    accounts.load_accounts()
    return accounts

def different_tickers(accounts):
    logging.info(f"different_tickers(accounts={accounts}) on host: {socket.gethostname()}")
    tickers_in_acct = set()
    account_positions = accounts.accounts_positions
    for accId in account_positions.keys():
        try:
            for pos in account_positions[accId]:
                tickers_in_acct.add(pos.sym) # add to a set
        except:
            continue
    return list(tickers_in_acct)

def email(accounts, acc_sum=True, hold_sum=True, sell_sum=True, vol=True):
    logging.info(f"email(accounts={accounts}, acc_sum={acc_sum}, hold_sum={hold_sum}, sell_sum={sell_sum}, vol={vol}) on host: {socket.gethostname()}")
    email_contents = []
    if acc_sum:
        email_contents.append(account_summary(accounts))
    if hold_sum:
        email_contents.append(get_accounts_hold(accounts))
    if sell_sum:
        email_contents.append(get_accounts_sell(accounts))
    if vol:
        vol_table,_,_ = apps.volatility.volatility_scanner(symbols=different_tickers(accounts),volatility="0", to_html=True, volume=0)
        vol_contents = "<h1>Volatility of Holdings</h1>" + vol_table
        email_contents.append(vol_contents)

    piece_together = "".join(email_contents)
    if send_email_with_data(piece_together):
        logging.info("Sent email")
        return True
    else:
        logging.debug("Unable to send email.")
        return False

def stay_awake(session, base_url):
    logging.info(f"stay_awake({session}, {base_url}) on host: {socket.gethostname()}")
    time.sleep(5)
    accounts = load_accounts(session, base_url)
    return accounts

def stay_live(session, base_url):
    logging.info(f"stay_live(session={session}, base_url={base_url}) on host: {socket.gethostname()}")
    print("Press any Key to Interrupt Stay Alive:")
    start = time.time()
    email_am = (6,30)
    email_pm = (16,0)
    while True:
        _now = datetime.now()
        accounts = stay_awake(session, base_url)
        if (_now.hour == email_am[0] and _now.minute == email_am[1]) or (_now.hour == email_pm[0] and _now.minute == email_pm[1]):
            email(accounts)
        logging.info("Time Awake:", time.time() - start, "seconds.")
        try:
            inp = inputimeout(prompt="Press any Key to Interrupt Stay Alive",timeout=5)
        except TimeoutOccurred:
            continue
        else:
            logging.info("returning account")
            return accounts

def alive_menu():
    options = {
        "1": "Stay Alive",
        "2": "Send Email",
        "3": "Check Sell",
        "E": "Exit"
    }
    while True:
        print("Select Option:")
        for op,desc in options.items():
            print(f"{op}) {desc}")
        inp = input("")
        if inp not in options.keys():
            print("That is not a valid option.")
        else: return inp

def process_input(inp, session, base_url, accounts):
    logging.info(f"process_input(inp={inp}, session={session}, base_url={base_url}, accounts={accounts}) @ {datetime.now()} on host: {socket.gethostname()}")
    if inp == "1":
        accounts = stay_live(session, base_url)
        inp = alive_menu()
    elif inp == "2":
        email(accounts)
    elif inp == "3":
        tk = input("Check Ticker For Ability to Sell (e to exit): ")
        if tk.lower() == 'e':
            exit()
        can_i_sell(tk, accounts)
    elif inp.upper() == "E":
        exit()

def vol_surface_email(vol_args):
    """
    edwgent - 2023-07-07
    @param vol_args:
    @return:
    """
    logging.info(f"vol_surface_email(vol_args={vol_args}) @ {datetime.now()} on host: {socket.gethostname()}")
    print(vol_args)
    ticker, days_out  = vol_args.split(",")
    if days_out == "":
        days_out = 30
    else:
        days_out = int(days_out)
    if ticker == '*':
        pass
    else:
        opt_chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put='*', days=days_out,tries=0,inclusive=True)
    img_path = visualize_impl_vs_strike_vs_exp(opt_chain)
    msg = vol_surface_summary([ticker])
    send_email_with_images([img_path],msg, subject=f"EMon: Volatility Surface Report - {','.join(ticker) if type(ticker) == list else ticker} - {datetime.now()}",
    receiver_email=etrade_config.receiver_email)

def vol_outliers_email(date):
    logging.info(f"vol_outliers_email({date}) @ {datetime.now()} on host: {socket.gethostname()}")
    try:
        logging.info('attempting to get data')
        msg,pos = vol_scraper_outliers_data(date)
    except Exception as e:
        logging.debug(f"Whoops, hit {e}. Trying to re run in 90 seconds.")
        time.sleep(90)
        msg,pos = vol_scraper_outliers_data(date)
        send_email_with_data(msg, subject=f"EMon: Volatility Outliers & Positions Job {date} - Check Logs Encountered Exception",
                             receiver_email=etrade_config.receiver_email)
        # add_generated_positions(df=pos)
        # get_generated_positions_obj()
    else:
        send_email_with_data(msg, subject=f"EMon: Volatility Outliers & Positions Job {date}",
                             receiver_email=etrade_config.receiver_email)
        # add_generated_positions(df=pos)
        # get_generated_positions_obj()


def start_session():
    logging.info(f"start_session() @ {datetime.now()} on host: {socket.gethostname()}")
    session, base_url = oauth()
    accounts = load_accounts(session, base_url)
    return session, accounts, base_url


def snap_and_email_risk(AccountsObj):
    """
    edwgent - 2023-07-07
    @param AccountsObj:
    @return:
    """
    for acc in AccountsObj.accounts:
        holdings = AccountsObj.accounts_holdings[acc.accountId]
        print(holdings)


def email_volatility(vol_args):
    logging.info(f"email_volatility(vol_args={vol_args}) @ {datetime.now()} on host: {socket.gethostname()}")
    symbols, vol, time_period, gt, price, volume, emailwho = vol_args.split(",")
    volume = int(volume)
    price = float(price)
    gt = True if gt.lower() == "g" else False
    symbols = [] if symbols == "*" else [symbols]
    subj = f"EMon: Volatility & Price Scraper"
    body = f"Parameters: Volatility: {vol}, Time Period: {time_period}, Price: {price}.<br>"
    vol_table,count,seconds = apps.volatility.volatility_scanner(symbols,vol,time_period, price=price,to_csv=True,to_html=True,volume=volume, gt =gt)
    body += f"Query Took {seconds} seconds across {count} symbol(s)."
    body += vol_table
    emails = []
    if emailwho == 'me': emails = ['kori.s.vernon@gmail.com']
    elif emailwho == 'all': emails = ['kori.s.vernon@gmail.com','sagaboy65@mac.com','rohan.gopinath9@gmail.com']

    if send_email_with_data(body, subject=subj,receiver_email=emails):
        logging.info("Sent email")
        return True
    else:
        logging.debug("Unable to send email.")
        return False

def email_long_straddles(straddle_args):
    """
    edwgent - 2023-07-10
    @param straddle_args:
    @return:
    """
    logging.info(f"email_long_straddles(straddle_args={straddle_args}) @ {datetime.now()} on host: {socket.gethostname()}")
    symbols,  days,time_period, min_edge, slippage,min_volume  = straddle_args.split(",")
    if symbols == '*':
        ticker_list = apps.volatility.get_top_vol_names(time_period)
    else:
        ticker_list = [symbols]
    for ticker in ticker_list:
        long_straddles = apps.long_straddle.get_long_staddles(ticker,days,min_volume,time_period)
        opportunistic_straddles = apps.long_straddles.get_opportunistic_long_straddles(long_straddles,min_edge)

def black_scholes_input(blackScholesPricer):
    if blackScholesPricer == 'take input':
        ticker = input('Ticker: ')
        print("Note: If you would like to use the volatility time until expiry days back (volatility [Time until Expiry - Today] days back), leave empty.")
        target_price = input('Target Price: ')
        print("Note: If you would like to generate a strike closest to your target price, leave empty.")
        strike = input('Strike: ')
        call_or_put = input('Call or Put (c or p): ')
        print("Note: If you would like to default to 30 days, leave empty.")
        days_out = input("Days out: ")
        print("Note: If you would like to default to long, leave empty.")

        long = input("Long 'l' or 's': ")
        if long == 'l' or long == '': long = True
        else: long = False
    else:
        ticker, strike, target_price, call_or_put, days_out,long = blackScholesPricer.split(',')
        if long == 'l' or long == '': long = True
        else: long = False

    # clean up strike
    if strike == "":
        strike = None
    else:
        strike = float(strike)

    # clean up target price
    if target_price == "":
        target_price = None
    else:
        target_price = float(target_price)

    # clean up days out
    if days_out == "":
        days_out = 30
    else:
        days_out = int(days_out)
    print(f"inputs:\nticker:{ticker}\nstrike:{strike}\ncall_or_put:{call_or_put}\ntarget_price:{target_price}\ndays_out:{days_out}\nlong:{long}")
    bsp_res = black_scholes_option_pricer(ticker=ticker, call_or_put=call_or_put, target_price=target_price, strike=strike,
                                      days=days_out, long=long)
    print(bsp_res)

    visualize = input("Visualize? (y or n): ")

    use_call_or_put = 'BS_Call' if call_or_put == 'c' else 'BS_Put'
    vol_fig = ticker_volatility_matrix_with_time_period_plt_vol(ticker,days_out)
    perf_fig = ticker_volatility_matrix_with_time_period_plt_stock(ticker,days_out)
    if visualize == 'y':
        opt_chain = get_friday_options_chain_for_ticker_date(ticker=ticker, call_or_put=call_or_put, days=days_out)
        fig = visualize_impl_vs_real_combined(opt_chain)

        gmail.send(
            subject=f"{ticker} Ideal vs. Implied vs. Real Volatility",
            sender=f"{etrade_config.sender_email}",
            receivers=[f"{etrade_config.sender_email}"],

            # A plot in body
            html=f"""
                    <h1>Black Scholes Pricer Result for: {ticker}</h1> 
                    {build_table(bsp_res[['Underlying','Strike','Last Price', use_call_or_put, 'Implied Volatility', 'BS_sigma']], color='grey_light')}
                    Price of Option vs. Strike:
                    {{{{ visualize_impl }}}}
                    <br>
                    Stock Performance:
                    {{{{ visualize_perf }}}}
                    <br>
                    Stock Volatility:
                    {{{{ visualize_vol }}}}
                """,
            body_images={
                "visualize_impl": fig,
                "visualize_vol": vol_fig,
                "visualize_perf": perf_fig
            },
            # Or plot as an attachment
            attachments={
                f"Black_Scholes_{ticker}.png": fig
            }
        )
    else:
        gmail.send(
            subject=f"{ticker} Ideal vs. Implied vs. Real Volatility",
            sender=f"{etrade_config.sender_email}",
            receivers=[f"{etrade_config.sender_email}"],

            # A plot in body
            html=f"""
                                <h1>Black Scholes Pricer Result for: {ticker}</h1> 
                                {build_table(bsp_res[['Underlying', 'Strike', 'Last Price', use_call_or_put, 'Implied Volatility', 'BS_sigma']], color='grey_light')}
                                <br>
                                Stock Performance:
                                {{{{ visualize_perf }}}}
                                <br>
                                Stock Volatility:
                                {{{{ visualize_vol }}}}
                            """,
            body_images={
                "visualize_vol": vol_fig,
                "visualize_perf": perf_fig
            }
        )
    print("Sent to email.")



if __name__ == "__main__":
    logging.info(f"Runtime: {datetime.now()}")

    # session, base_url = oauth()
    # accounts = load_accounts(session, base_url)


    # sys.path.append(f"{etrade_config.base_dir}/order_security")
    # from order_security import SecurityOrder, ETradeOrder

    # test = accounts.accounts[2]
    # print(accounts.accounts_holdings[test.accountId].to_dataframe())
    # order = SecurityOrder(session,test, base_url, accounts.accounts_holdings[test.accountId])
    # order.sell_from_holdings()
    # etrade_order = ETradeOrder(session, base_url, test.accountIdKey, accounts.accounts_holdings[test.accountId] )
    # etrade_order.sell_from_holdings()
    # etrade_order.preview_equity_order(
    #     securityType="OPTN",
    #     orderType="OPTN",
    #     accountIdKey="zBRmF6b_gzE-mkO74Vbaag",
    #     symbol="BAC",
    #     orderAction="BUY_OPEN",
    #     clientOrderId="6591041807",
    #     priceType="MARKET",
    #     quantity=1,
    #     callPut="CALL",
    #     expiryDate=datetime.datetime(2023,4,21),
    #     marketSession="REGULAR",
    #     orderTerm= "GOOD_FOR_DAY",
    #     strikePrice=30,
    #     allOrNone=False,
    #     stopPrice=0,
    #     routingDestination='AUTO'
    # )
    # etrade_order.preview_equity_order(
    #     securityType="EQ",
    #     orderType="EQ",
    #     accountIdKey="zBRmF6b_gzE-mkO74Vbaag",
    #     symbol="AAPL",
    #     orderAction="SELL",
    #     clientOrderId="6591041907",
    #     priceType="MARKET",
    #     quantity=1,
    #     marketSession="REGULAR",
    #     orderTerm="GOOD_FOR_DAY",
    # )
    # order.sell_security_market_order(accounts.accounts_holdings[test.accountId].holdings['AAPL'])
    # order.cancel_order()

    logging.info(f'EMON Tool Initialized')
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--Email", help="Email Account Summary, Hold Summary, Can Sell Summary", action="store_true")
    parser.add_argument("-s", "--StayLive", help="Keep Session Alive",
                        action="store_true")
    parser.add_argument("-c", "--canSell", help="Can Sell Ticker", type=str)

    parser.add_argument("-sa", "--sentimentAnalysis", help="Pass in Ticker to scrape 10 relevant and up-to-date articles and perform sentiment analysis - send email to target email.", type=str)
    parser.add_argument("-vo", "--volatilityOutliers", help=f"Send Volatility Outliers with current date: {datetime.strptime(TODAY,'%Y-%m-%d').strftime('%Y%m%d')} or what ever date you would like.", type=str, const=datetime.strptime(TODAY,'%Y-%m-%d').strftime('%Y%m%d'), nargs='?')

    parser.add_argument("-vs","--volatilityScanner",help="Scan for market volatility", type=str,const="*,.3,3mo,G,0,0,me", nargs='?')

    parser.add_argument("-r","--Risk",help="Snap risk and email out for all accounts", action='store_true')

    parser.add_argument("-bsp", "--blackScholesPricer", help="BlackScholesPricer - input is 'TICKER,TARGET PRICE, 'c' for call, and 'p' for put',days out,'l' for long and 's' for short", type=str, const='take input', nargs='?')

    parser.add_argument("-ss", "--stockStats", help="Get stock stats - incl vol surface, income statement, events for stocks given - input is 'TICKER,days out - leave TICKER as * to only fetch highest vol tickers", type=str, const='take input', nargs='?')

    args = parser.parse_args()
    if args.Email or args.canSell or args.StayLive or args.Risk:
        session, base_url = oauth()
        accounts = load_accounts(session, base_url)

    # Process User inputs
    if args.blackScholesPricer:
        # add strike
        black_scholes_input(args.blackScholesPricer)
    if args.stockStats:
        vol_surface_email(args.stockStats)
    if args.Risk:
        snap_and_email_risk(accounts)
    if args.volatilityScanner:
        email_volatility(args.volatilityScanner)
    if args.sentimentAnalysis:
        scrape_articles_determine_sentiment_and_send_email(args.sentimentAnalysis)
    if args.volatilityOutliers:
        date = args.volatilityOutliers
        logging.info(f"Volatility Outliers for Date: {date}")
        vol_outliers_email(date)
    if args.Email:
        email(accounts)
    if args.canSell:
        can_i_sell(args.canSell, accounts)
        inp = alive_menu()
        process_input(inp, session, base_url, accounts)
    if args.StayLive:
        while True:
            accounts = stay_live(session, base_url)
            inp = alive_menu()
            if inp == "1": continue
            elif inp == "2":
                email(accounts)
                break
            elif inp == "3":
                tk = input("Check Ticker For Ability to Sell: ")
                can_i_sell(tk, accounts)
            elif inp.lower() == "E":
                exit()


            




