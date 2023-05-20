#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from pretty_html_table import build_table
import time

from datetime import datetime
import threading

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + '/../')
import dev_etrade_python_client as e_sub

def compare_hour_minute(time1, time2):
    return time1.hour == time2.hour and time1.minute == time2.minute

def check_portfolio_time(accounts, now):
    port_time_am = datetime(1900,1,1,6,30)
    port_time_pm = datetime(1900,1,1,17,35)
    if compare_hour_minute(port_time_am, now) or compare_hour_minute(port_time_pm, now):
        e_sub.email(accounts)

def scrape_vol():
    e_sub.email_volatility("*,.3,3mo,G,0,0,me")

def check_vol_scraper():
    now = datetime.now()
    vol_time = datetime(1900,1,1,0,0) #multithread in future

    if compare_hour_minute(vol_time, now):
        t1 = threading.Thread(target=scrape_vol, name='t1')
        t1.start()

def run_scheduler():
    session, accounts, base_url = e_sub.start_session()
    while True:
        time_now = datetime.now()
        print(time_now)
        accounts = e_sub.stay_awake(session, base_url)
        check_portfolio_time(accounts, time_now)
        check_vol_scraper()

def main():
    run_scheduler()
main()