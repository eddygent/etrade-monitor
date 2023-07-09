#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 09/07/2023
# Email       : kori.s.vernon@gmail.com
# Purpose : We want to mock the risk-free interest rate ~0.0525 on our
#               accounts cash that is designated as savings.
# ---------------------------------------------------------------------------
import yfinance as yf
from datetime import datetime, timedelta
from rauth import OAuth1Service
import webbrowser
import sys
import os
import pprint
# internal helpers
script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + '/../')
from accounts.accounts import Accounts, Account
import etrade_config

TODAY = datetime.now().strftime("%Y-%m-%d")
RATE = etrade_config.RATE

class AccountNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)

def cash_available_in_target(accounts: Accounts, target_portfolio_name='savings'):
    """
    Kori Vernon - 2023-07-09
    Description: Get the cash available in your target portfolio.

    @param accounts: Accounts object
    @param target_portfolio_name: Name of the portfolio you want to target to use to balance.
    @return: cash that you want to use to balance account
    """
    '''
    Get the available cash of the account that we are targeting.
    '''

    target_portfolio = None
    portfolio_names = []
    for account in accounts.accounts: # this is a list... we are looking for the target
        if account.accountName.lower() == target_portfolio_name.lower():
            target_portfolio = account
            break
        portfolio_names.append(account.accountName.lower())
    if not target_portfolio:
        raise AccountNotFoundException(f"Account with name {target_portfolio} could not be found. Choose from the following target portfolio names {portfolio_names}")

    return target_portfolio.buying_power
def get_performance_within_past_time_for_ticker(ticker, days=365):
    # Get the historical data for the past 5 years
    start_date = TODAY
    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    days_back_datetime = start_date_datetime - timedelta(days=days)
    end_date = days_back_datetime.strftime("%Y-%m-%d")
    data = yf.download(ticker, start=end_date, end=start_date)
    beginning_price = data["Close"].iloc[0]
    end_price = data["Close"].iloc[-1]
    # Print the annual returns
    return float((end_price/beginning_price)-1) * 365/days


def get_share_price(ticker):
    return yf.Ticker(ticker).fast_info['lastPrice']


def match_rate(available_cash:float, balance_with_names:list = ["VOO","SCHD","SCHG"], use_days_performance:int =365*10, rate:float =RATE):
    """
    Kori Vernon - 2023-07-09
    Description: Match the risk-free interest rate using the balance with names params (or given rate)

    @param available_cash: This is the available cash that you want to use to balance your account.
    @param balance_with_names: This is a list of tickers that you want to use in order to balance your portfolio.
    @param use_days_performance: days that you want to pass in to match performance for
    @param rate: This is the rate you want to use to match
    @return: dict of dict with names as keys, shares, and past annualized return.
    """
    balance_dict = {}
    balance_ratio = 1/len(balance_with_names) # this is how we want to diversify .. for three symbols it would be 33% of each to match interest rate.

    for i, ticker in enumerate(balance_with_names):


        performance_within_past_time =  get_performance_within_past_time_for_ticker(ticker, use_days_performance) # get the past performance in terms of a percentage
        if performance_within_past_time < 0 or performance_within_past_time < rate:
            balance_with_names.pop(i) # remove it if it's negative or less than the performance within past year haha
            balance_ratio = 1 / len(balance_with_names) # need to iterate through all first
        # if it's a desirable percentage, we want to see what we need in order to match the rate

    for ticker in balance_with_names:
        balance_dict[ticker] = {}  # delcare dict

        performance_within_past_time = get_performance_within_past_time_for_ticker(ticker, use_days_performance)  # get the past performance in terms of a percentage
        print("performance within past time", performance_within_past_time)
        balance_with_risk_free_interest_rate = RATE * available_cash
        balance_with_performance = performance_within_past_time * available_cash

        print("risk free interest rate performance", balance_with_risk_free_interest_rate)
        print('performance of security', balance_with_performance)
        performance_to_interest_rate_ratio = balance_with_risk_free_interest_rate / balance_with_performance

        print('performance_to_interest_rate_ratio', performance_to_interest_rate_ratio)
        amount_needed_in_cash = available_cash * (performance_within_past_time * performance_to_interest_rate_ratio )
        print('amount needeed in cash', amount_needed_in_cash)
        print(available_cash,'available_cash','*',performance_within_past_time, 'within past time', '*', performance_to_interest_rate_ratio,'perf 2 int ratio')
        amount_needed_in_cash_by_ratio  = amount_needed_in_cash * balance_ratio
        share_price = get_share_price(ticker)
        shares_needeed = int(amount_needed_in_cash_by_ratio / share_price) + 1 # always round up

        balance_dict[ticker]['match_performance_time_period'] = use_days_performance
        balance_dict[ticker]['performance_to_interest_rate_ratio'] = performance_to_interest_rate_ratio
        balance_dict[ticker]['share_price'] = share_price
        balance_dict[ticker]['shares_needed'] = shares_needeed
        balance_dict[ticker]['amount_needed_in_cash'] = amount_needed_in_cash_by_ratio
        balance_dict[ticker]['performance_within_past_time'] = performance_within_past_time
        balance_dict[ticker]['stock_portfolio_balance_ratio'] = performance_within_past_time * performance_to_interest_rate_ratio
    return balance_dict

def load_accounts(session, base_url):
    print(f"load_accounts(session={session},base_url={base_url}) on host: {socket.gethostname()}")
    accounts = Accounts(session, base_url)
    accounts.load_accounts()
    return accounts


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


def main():
    session, base_url = oauth()
    accounts = load_accounts(session, base_url)
    cash = cash_available_in_target(accounts, target_portfolio_name='savings')
    pprint.pprint(match_rate(cash))

if __name__ == '__main__':
    main()




