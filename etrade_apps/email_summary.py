import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import etrade_config

ACC_TYPE = etrade_config.ACC_TYPE

import babel.numbers
import decimal

def format_currency(currency):
    return babel.numbers.format_currency(decimal.Decimal(currency), "USD")

def get_accounts_hold(AccountsObj):
    s = "<h1>Account 30 Day Holding Monitoring Section --</h1><br>"
    for acc in AccountsObj.accounts:
        contents = AccountsObj.accounts_holdings[acc.accountId].str_must_hold_html()
        if contents:
            s += f"<b>-->{ACC_TYPE[acc.accountName]} Account:</b> {acc.accountName}<br>"
            s += contents
            s += f"<br><br>"
    return s

def get_accounts_sell(AccountsObj):
    s = "<h1>Immediate Liquidation --</h1><br>"
    for acc in AccountsObj.accounts:
        contents = AccountsObj.accounts_holdings[acc.accountId].str_can_sell(toggle_html=True)
        if contents:
            s += f"<b>-->{ACC_TYPE[acc.accountName]} Account:</b> {acc.accountName}<br>"
            s += contents
            s += f"<br><br>"
    return s

def account_summary(AccountsObj):
    s = "<h1>Account Summary Section --</h1><br>"

    acc_info = ""
    cum_total_buy = 0
    cum_total_val = 0
    for acc in AccountsObj.accounts:
        cum_total_val += acc.account_value
        cum_total_buy += acc.buying_power
        acc_info += f"<b>{ACC_TYPE[acc.accountName]} Account:</b> {acc.accountName} | <b>Account Value:</b> {format_currency(acc.account_value)}  - <b>Buying Power:</b> {format_currency(acc.buying_power)}<br>"
    s += f"<b>Total Assets:</b> {format_currency(cum_total_val)} | <b>Cumulative Immediate Buying Power:</b> {format_currency(cum_total_buy)}<br>{acc_info}<br><br>"
    return s

def send_email_with_data(contents, subject="E*TRADE ACCOUNT SUMMARY", sender_email=etrade_config.email,
                         receiver_email=["kori.s.vernon@gmail.com"]):
    receiver_email = ",".join(receiver_email)

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email  # Recommended for mass emails

    body = str(contents)

    print("SENDING EMAIL WITH THE FOLLOWING")
    print(body)

    # Add body to email
    message.attach(MIMEText(body, "html"))

    text = message.as_string()
    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, etrade_config.password)
        server.sendmail(sender_email, receiver_email, text)
    return True
