# E*TRADE API Python Application

## Table of Contents

* [Requirements](#requirements)
* [Setup](#setup)
* [Obtain Etrade Consumer Key and Consumer Secret](#obtain-etrade-consumer-key-and-consumer-secret)
* [Running Code](#running-code)
* [Etrade Monitor](#etrade-monitor)


## ToDo
- Documenting Forecasted Trades in a Journal (Medium, 3 Difficulty)
- Fair Pricer for Stocks and Options (High, x Difficulty Unknown)
- Regression Analysis on Financial Statements against Expected Growth/Subtraction due to earnings (Medium, 13 Difficulty)
- Volatility of Stock Since its purchase (Medium, 3 Difficulty)

## Requirements

In order to run this sample application you need the following three items:

1. Python 3 - this sample application is written in Python and requires Python 3. If you do not
already have Python 3 installed, download it from

   [`https://www.python.org/downloads/`](https://www.python.org/downloads/).

2. An [E*TRADE](https://us.etrade.com) account

3. E*TRADE consumer key and consumer secret.

## Obtain Etrade Consumer Key and Consumer Secret
In order to obtain an Etrade Consumer Key and Consumer Secret, you have to go to Etrade Developer and request the Consumer Secret and Consumer Key
 * When you log in, you can easily request your sandbox key here: https://us.etrade.com/etx/ris/apikey
 * However, in order to get your Consumer Key, you have to Complete:
   * User Intent Survey
   * API Agreement
   * Market Data Agreement
   * Market Data Atestation
 * **Complete Honestly** You can complete the following here: https://developer.etrade.com/getting-started
   * Note: You do intend to use Market Data, and you do intend to trade on your account and view your positions. 
 * Once you obtain your Etrade Consumer Key and Consumer Secret, store it somewhere safe!!!
   * Create the file `etrade_config.py` OR run `bash` [`setup_etrade_config.sh`](setup_etrade_config.sh) to create your etrade_config file. This is where your configurations will be placed. 
 * `etrade_config.py` follows this format. You can run `bash` [`setup_etrade_config.sh`](setup_etrade_config.sh)  to create the config file, or copy, paste, then modify to hold your account information:
```buildoutcfg
email = "your.email@website.com"
password = "your_password"
ACC_TYPE = {
    "<ACCOUNT NICKNAME IN ETRADE>": "<ACCOUNT FUNCTION>",
    "stonks": "Investing",
    "[example]errday spendin": "Checking"
}
CONSUMER_KEY = "YOUR CONSUMER KEY"
CONSUMER_SECRET = "YOUR CONSUMER SECRET"
SANDBOX_BASE_URL="https://apisb.etrade.com"
PROD_BASE_URL="https://api.etrade.com"
receiver_email = ["your.email@website.com", "another.email.if.you.want@website.com"]
```
*Note: This file is in the `.gitignore` double check to ensure your account information is being pushed to GitHub.*
## Setup

1. Unzip python zip file

2. Edit `etrade_config.py` with your consumer key and consumer secret; copy these from your application's keys' section

3. Create the virtual environment by running the Python's venv command; see the command syntax below

```
$ python3 -m venv venv
```

4. Activate the Python virtual environment

On Windows, run:

```
$ venv\Scripts\activate.bat
```

On Unix or Mac OS, run:

```
$ source venv/bin/activate
```

5. Use pip to install dependencies for the sample application

```
$ pip install -r requirements.txt
```

6. Run the sample application

```
$ python3 dev_etrade_python_client.py
```

## Etrade Monitor

Functionalities built out in `dev_etrade_python_client.py`

Running the following in Command Line will send you an email with statistics on your account. 
*Note: There is a built-in 30-day holding period. If you would not like this functionality then disable.*

[`python3 dev_etrade_python_client.py -e`](dev_etrade_python_client.py)

It will send an email that looks something like this to your target email addresses.

![etrade email top](img/top_email_ex.png?raw=true "Title")
![etrade email bottom](img/bottom_email_ex.png?raw=true "Title")



Running the following in Command Line will send you an email with statistics on volatility within the market for the current
business day and pull together the largest moves in volatility, along with potentially profitable options positions.

[`python3 dev_etrade_python_client.py -vo`](dev_etrade_python_client.py)

It will look something like this: 
![emon etrade volatility screener](/img/volatility-screener-email.png?raw=true "Title")

Feel free to customize to your own personal use case. 