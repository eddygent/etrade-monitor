#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
"""This Python script provides examples on using the E*TRADE API endpoints"""
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
from market.market import Market
import time
import argparse
from inputimeout import inputimeout, TimeoutOccurred
import etrade_config
import apps.volatility
from apps.email_summary import send_email_with_data, get_accounts_hold, account_summary,get_accounts_sell
from apps.volatility import *
from apps.volatility_strategies import *

import os
base = os.getcwd()
# logger settings
level = logging.DEBUG
fmt =  "[%(levelname)s] [dev_etrade_python_client.py] %(asctime)-15s %(message)s"
logging.basicConfig(level=level, format=fmt)
# logger = logging.getLogger('my_logger')
# logger.setLevel(logging.INFO)
# handler = RotatingFileHandler("python_client.log", maxBytes=5*1024*1024, backupCount=3)
# FORMAT = "[%(levelname)s] %(asctime)-15s %(message)s"
# fmt = logging.Formatter(FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p')
# handler.setFormatter(fmt)
# logger.addHandler(handler)

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

def vol_outliers_email(date):
    logging.info(f"vol_outliers_email({date}) @ {datetime.now()} on host: {socket.gethostname()}")
    try:
        msg,pos = vol_scraper_outliers_data(date)
    except Exception as e:
        logging.debug("Whoops, hit",e,'Trying to re run in 90 seconds.')
        time.sleep(90)
        msg,pos = vol_scraper_outliers_data(date)
        send_email_with_data(msg, subject=f"EMon: Volatility Outliers Job {date}", receiver_email=etrade_config.receiver_email)
    else:
        send_email_with_data(msg, subject=f"EMon: Volatility Outliers Job {date}", receiver_email=etrade_config.receiver_email)

def start_session():
    logging.info(f"start_session() @ {datetime.now()} on host: {socket.gethostname()}")
    session, base_url = oauth()
    accounts = load_accounts(session, base_url)
    return session, accounts, base_url

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


if __name__ == "__main__":
    logging.info("Runtime:",datetime.now())

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
    parser.add_argument("-vo", "--volatilityOutliers", help=f"Send Volatility Outliers with current date: {TODAY} or what ever date you would like.", type=str, const=TODAY, nargs='?')

    parser.add_argument("-vs","--volatilityScanner",help="Scan for market volatility", type=str,const="*,.3,3mo,G,0,0,me", nargs='?')

    args = parser.parse_args()
    if args.Email or args.canSell or args.StayLive:
        session, base_url = oauth()
        accounts = load_accounts(session, base_url)

    # Process User inputs
    if args.volatilityScanner:
        email_volatility(args.volatilityScanner)
    if args.volatilityOutliers:
        date = args.volatilityOutliers
        logging.info("Volatility Outliers for Date:",date)
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


            




