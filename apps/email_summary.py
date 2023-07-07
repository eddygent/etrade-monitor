#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
import email, smtplib, ssl
import locale

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import os
import sys
script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + '/../')
import etrade_config

ACC_TYPE = etrade_config.ACC_TYPE

from helper import format_currency

from pretty_html_table import build_table
import pandas as pd
from redmail import gmail

gmail.username = etrade_config.sender_email
gmail.password = etrade_config.password

def get_accounts_hold(AccountsObj):
    s = "<h1>Account 30 Day Holding Monitor --</h1>"
    for acc in AccountsObj.accounts:
        s += AccountsObj.accounts_holdings[acc.accountId].hold_dataframe(html=True)
        # contents = AccountsObj.accounts_holdings[acc.accountId].str_must_hold_html()
        # if contents:
        #     s += f"<b>-->{ACC_TYPE[acc.accountName]} Account:</b> {acc.accountName}<br>"
        #     s += contents
        #     s += f"<br><br>"
    return s

def get_accounts_sell(AccountsObj):
    s = "<h1>Immediate Liquidation --</h1>"
    for acc in AccountsObj.accounts:
        df_win = AccountsObj.accounts_holdings[acc.accountId].can_sell_winners_dataframe()
        gain = df_win['GAIN RANKING'].sum()
        df_lose = AccountsObj.accounts_holdings[acc.accountId].can_sell_losers_dataframe()
        loss = df_lose['GAIN RANKING'].sum()

        if gain == loss == 0:
            continue
        s += f"Total Gain: {format_currency(gain)}"
        s += AccountsObj.accounts_holdings[acc.accountId].can_sell_winners_dataframe(html=True)
        s += f"Total Loss: {format_currency(loss)}"
        s += AccountsObj.accounts_holdings[acc.accountId].can_sell_losers_dataframe(html=True)
        # contents = AccountsObj.accounts_holdings[acc.accountId].str_can_sell(toggle_html=True)
        # if contents:
        #     s += f"<b>-->{ACC_TYPE[acc.accountName]} Account:</b> {acc.accountName}<br>"
        #     s += contents
        #     s += f"<br><br>"
    return s

def account_summary(AccountsObj):
    s = "<h1>Account Summary Section --</h1>"
    cum_total_buy = 0
    cum_total_val = 0
    acc_type = []
    acc_name = []
    acc_value = []
    acc_buying_power = []
    for acc in AccountsObj.accounts:
        cum_total_val += acc.account_value
        cum_total_buy += acc.buying_power
        # acc_info += f"<b>{ACC_TYPE[acc.accountName]} Account:</b> {acc.accountName} | <b>Account Value:</b> {format_currency(acc.account_value)}  - <b>Buying Power:</b> {format_currency(acc.buying_power)}<br>"
        # s += f"<b>Total Assets:</b> {format_currency(cum_total_val)} | <b>Cumulative Immediate Buying Power:</b> {format_currency(cum_total_buy)}<br>{acc_info}<br><br>"
        try:
            acc_type.append(ACC_TYPE[acc.accountName])
            acc_name.append(acc.accountName)
        except KeyError:
            acc_type.append(ACC_TYPE[acc.accountDescription])
            acc_name.append(acc.accountDescription)
        acc_value.append(format_currency(acc.account_value))
        acc_buying_power.append(format_currency(acc.buying_power))
    acc_type.append("Cumulative")
    acc_name.append("Total Assets")
    acc_value.append(format_currency(cum_total_val))
    acc_buying_power.append(format_currency(cum_total_buy))
    to_df = {"Account Type":acc_type, "Account Name": acc_name, "Buying Power": acc_buying_power, "Account Value":acc_value,}
    df = pd.DataFrame(to_df)
    df = df.reset_index(drop=True)
    return s + build_table(df,'blue_light')

def send_email_with_data(contents, subject="EMon: E*TRADE ACCOUNT SUMMARY", sender_email=etrade_config.sender_email,
                         receiver_email=etrade_config.receiver_email):


    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(receiver_email)
    message["Subject"] = subject
    message["Bcc"] = ", ".join(receiver_email)  # Recommended for mass emails
    body = str(contents)
    print("SENDING EMAIL WITH THE FOLLOWING")
    print(body)
    # Add body to email
    message.attach(MIMEText(body, "html"))
    text = message.as_string()
    # Log in to server using secure context and send email - TODO: make ssl optional
    context = ssl._create_unverified_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, etrade_config.password)
        server.sendmail(sender_email, receiver_email, text)
    return True

def _send_email_with_data(contents, subject="EMon: E*TRADE ACCOUNT SUMMARY", sender_email=etrade_config.sender_email,
                         receiver_email=etrade_config.receiver_email):
    '''
    Not working for some reason. to be fixed at a later time
    '''
    body = str(contents)
    print(body)
    gmail.send(
        subject=f"{subject}",
        sender=f"{sender_email}",
        receivers=[f"{receiver_email}"],
        html=f"""{body}"""
    )
    return True

def main():
    gmail.send(
        subject="hi",
        sender=etrade_config.sender_email,
        receivers=[etrade_config.receiver_email],
        html="hi"
    )

if __name__ == '__main__':
    main()