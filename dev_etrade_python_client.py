#!/usr/bin/python3
"""This Python script provides examples on using the E*TRADE API endpoints"""
from __future__ import print_function

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
from etrade_apps.email_summary import send_email_with_data, get_accounts_hold, account_summary,get_accounts_sell
import etrade_apps.volatility

import os
base = os.getcwd()
# loading configuration file
sys.path.append(f"{etrade_config.base_dir}/etrade-monitor/etrade_python_client")
# logger settings
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("python_client.log", maxBytes=5*1024*1024, backupCount=3)
FORMAT = "%(asctime)-15s %(message)s"
fmt = logging.Formatter(FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(fmt)
logger.addHandler(handler)

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
    for acc in AccountsObj.accounts:
        contents = AccountsObj.accounts_holdings[acc.accountId]._can_sell()
        for tk,qty in contents:
            if ticker.upper() in tk.upper():
                print(f"Can Sell: {tk} and Qty: {qty}")
    tk = input("Check Ticker For Ability to Sell (e to exit): ")
    if tk.lower() == "e":
        return
    can_i_sell(tk, AccountsObj)

def load_accounts(session, base_url):

    accounts = Accounts(session, base_url)
    accounts.load_accounts()
    return accounts

def email(accounts, acc_sum=True, hold_sum=True, sell_sum=True):
    email_contents = []
    if acc_sum:
        email_contents.append(account_summary(accounts))
    if hold_sum:
        email_contents.append(get_accounts_hold(accounts))
    if sell_sum:
        email_contents.append(get_accounts_sell(accounts))

    piece_together = "".join(email_contents)
    if send_email_with_data(piece_together):
        print("Sent email")
        return True
    else:
        print("Unable to send email.")
        return False

def stay_awake(session, base_url):
    time.sleep(5)
    accounts = load_accounts(session, base_url)
    return accounts

def stay_live(session, base_url):
    print("Press any Key to Interrupt Stay Alive:")
    start = time.time()
    while True:
        accounts = stay_awake(session, base_url)
        print("Time Awake:", time.time() - start, "seconds.")
        try:
            inp = inputimeout(prompt="Press any Key to Interrupt Stay Alive",timeout=5)
        except TimeoutOccurred:
            continue
        else:
            print("returning account")
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
    if inp == "1":
        accounts = stay_live(session, base_url)
        inp = alive_menu()
    elif inp == "2":
        email(accounts)
    elif inp == "3":
        tk = input("Check Ticker For Ability to Sell (e to exit): ")
    elif inp.upper() == "E":
        exit()


def email_volatility(vol_args):
    vol, time_period, price = vol_args.split(",")
    subj = f"Volatility & Price Scraper"
    body = f"Parameters: Volatility: {vol}, Time Period: {time_period}, Price: {price}.<br>"
    vol_table,count,seconds = etrade_apps.volatility.volatility_scanner([],vol,time_period, price,to_csv=True,to_html=True)

    body += f"Query Took {seconds} seconds across {count} symbol(s)."
    body += vol_table

    if send_email_with_data(body, subject=subj,receiver_email=['kori.s.vernon@gmail.com','sagaboy65@mac.com']):
        print("Sent email")
        return True
    else:
        print("Unable to send email.")
        return False




if __name__ == "__main__":


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


    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--Email", help="Email Account Summary, Hold Summary, Can Sell Summary", action="store_true")
    parser.add_argument("-s", "--StayLive", help="Keep Session Alive",
                        action="store_true")
    parser.add_argument("-c", "--canSell", help="Can Sell Ticker", type=str)
    parser.add_argument("-vs","--volatilityScanner",help="Scan for market volatility", type=str,const=".3,3mo,150", nargs='?')
    
    args = parser.parse_args()
    if args.Email or args.canSell or args.StayLive:
        session, base_url = oauth()
        accounts = load_accounts(session, base_url)

    # Process User inputs
    if args.volatilityScanner:
        email_volatility(args.volatilityScanner)
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
            elif inp == "E":
                exit()


            




