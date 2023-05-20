# E*TRADE API Python Sample Application

This sample Python application provides examples on using the ETRADE API endpoints.

## Table of Contents

* [Requirements](#requirements)
* [Setup](#setup)
* [Obtain Etrade Consumer Key and Consumer Secret](#obtain-etrade-consumer-key-and-consumer-secret)
* [Running Code](#running-code)
* [Etrade Monitor](#etrade-monitor)

## Requirements

In order to run this sample application you need the following three items:

1. Python 3 - this sample application is written in Python and requires Python 3. If you do not
already have Python 3 installed, download it from

   [`https://www.python.org/downloads/`](https://www.python.org/downloads/).

2. An [E*TRADE](https://us.etrade.com) account

3. E*TRADE consumer key and consumer secret.

## Obtain Etrade Consumer Key and Consumer Secret
In order to obtain an Etrade Consumer Key and Consumer Secret, you have to go to to Etrade Developer and request the Consumer Secret and Consumer Key
 * When you login, you can easily request your sandbox key here: https://us.etrade.com/etx/ris/apikey
 * However, in order to get your Consumer Key, you have to Complete:
   * User Intent Survey
   * API Agreement
   * Market Data Agreement
   * Market Data Atestation
 * **Complete Honestly** You can complete the following here: https://developer.etrade.com/getting-started
   * Note: You do intend to use Market Data, and you do intend to trade on your account and view your positions. 
 * Once you obtain your Etrade Consumer Key and Consumer Secret, store it somewhere safe!!!
 * Create the file `etrade_config.py` where your configurations will be placed. 
 * `etrade_config.py` follows this format. You can copy, paste, and modify to hold your account information:
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
```
*Note: This file is in the `.gitignore` double check to ensure your account information is being pushed to GitHub.*
## Setup

1. Unzip python zip file

2. Edit [`config.ini`](EtradePythonClient/etrade_python_client/config.ini)
with your consumer key and consumer secret; copy these from your application's keys' section

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
$ cd etrade_python_client
$ python3 etrade_python_client.py
```

## Running Code

Complete these steps to run the code for the sample application:

1. Activate the Python virtual environment

On Windows, run:

```
$ venv\Scripts\activate.bat
```

On Unix or Mac OS, run:

```
$ source venv/bin/activate
```

2. Run the application

```
$ cd etrade_python_client
$ python3 etrade_python_client.py
```

## Etrade Monitor

Functionalities built out in `dev_etrade_python_client.py`