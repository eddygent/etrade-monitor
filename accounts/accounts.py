import json
import logging
import configparser
from logging.handlers import RotatingFileHandler
from order.order import Order
import sys
import etrade_config
sys.path.append(".")
import os
base = os.getcwd()
# loading configuration file
sys.path.append(f"{etrade_config.base_dir}/etrade-monitor/etrade_python_client")

# logger settings
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("python_client.log", maxBytes=5 * 1024 * 1024, backupCount=3)
FORMAT = "%(asctime)-15s %(message)s"
fmt = logging.Formatter(FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(fmt)
logger.addHandler(handler)

INSTITUTION_TYPE = 'BROKERAGE'


###################### Created Classes #######################
sys.path.append(f'{etrade_config.base_dir}/positions')
print(etrade_config.base_dir)
from positions import Position
sys.path.append(f'{etrade_config.base_dir}/transactions')
from transactions import Transaction, BANNED_TRANSACTION_TYPE
sys.path.append(f'{etrade_config.base_dir}/holdings')
from holdings import SecurityHolding, SecurityHoldings
#################### End Created Classes #####################

import babel.numbers
import decimal

def format_currency(currency):
    return babel.numbers.format_currency(decimal.Decimal(currency), "USD")


class Account:
    def __init__(self, accountId, accountIdKey, accountDescription, accountName):
        self.accountId = accountId
        self.accountIdKey = accountIdKey
        self.accountDescription = accountDescription
        self.accountName = accountName
        self.account_value = 0
        self.buying_power = 0

    def set_account_value(self, account_value):
        self.account_value = account_value
        return True

    def set_buying_power(self, buying_power):
        self.buying_power = buying_power
        return True

    def __repr__(self):
        return f"AccountName: {self.accountName}; Account Value: {format_currency(self.account_value)}"

class Accounts:
    def __init__(self, session, base_url):
        """
        Initialize Accounts object with session and account information

        :param session: authenticated session
        """
        self.session = session
        self.account = {}
        self.base_url = base_url
        self.accounts = [] # list of accounts
        self.accounts_transactions = {} # dictionary of transactions - key accountID, value: list of Associated Transactions
        self.accounts_positions = {} # dictionary of positions - key accountId, value: list of associated positions
        self.accounts_holdings = {}

    def update_holdings(self):
        for acc in self.accounts:
            holdings = SecurityHoldings()
            for pos in self.accounts_positions[acc.accountId]:
                holdings.add_position(pos)
            for tx in self.accounts_transactions[acc.accountId]:
                holdings.add_transaction(tx)
            self.accounts_holdings[acc.accountId] = holdings
        return True


    def total_value_of_accounts(self):
        self.update_account_balances()
        return sum([acc.account_value for acc in self.accounts]) # sum all of the account values

    def AccountParser(self, AccountListResponse):
        if AccountListResponse is not None and "AccountListResponse" in AccountListResponse and "Accounts" in AccountListResponse["AccountListResponse"] \
                and "Account" in AccountListResponse["AccountListResponse"]["Accounts"]:
            accounts = AccountListResponse['AccountListResponse']["Accounts"]["Account"]
            for acc in accounts:
                self.accounts.append(Account(acc['accountId'], acc['accountIdKey'], acc['accountDesc'], acc['accountName']))
            'accountId', 'accountIdKey', 'accountDesc', 'accountName'
            self.update_account_balances()
            return True
        return False

    def update_account_balances(self):
        """
        Calls account balance API to retrieve the current balance and related details for a specified account

        :param self: Pass in parameters authenticated session and information on selected account
        """

        # URL for the API endpoint
        for acc in self.accounts:
            try:
                url = self.base_url + "/v1/accounts/" + acc.accountIdKey + "/balance.json"

                # Add parameters and header information
                params = {"instType": INSTITUTION_TYPE, "realTimeNAV": "true"}
                headers = {"consumerkey": etrade_config.CONSUMER_KEY}

                # Make API call for GET request
                response = self.session.get(url, header_auth=True, params=params, headers=headers)
                logger.debug("Request url: %s", url)
                logger.debug("Request Header: %s", response.request.headers)

                # Handle and parse response
                if response is not None and response.status_code == 200:
                    parsed = json.loads(response.text)
                    logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
                    data = response.json()
                    if data is not None and "BalanceResponse" in data:
                        balance_data = data["BalanceResponse"]
                        if balance_data is not None and "Computed" in balance_data \
                                and "RealTimeValues" in balance_data["Computed"] \
                                and "totalAccountValue" in balance_data["Computed"]["RealTimeValues"]:
                            total_account_value = balance_data["Computed"]["RealTimeValues"]["totalAccountValue"]
                            if balance_data["Computed"]["RealTimeValues"]["totalAccountValue"] != 0: acc.set_account_value(balance_data["Computed"]["RealTimeValues"]["totalAccountValue"])
                        if balance_data is not None and "Computed" in balance_data \
                                and "cashBuyingPower" in balance_data["Computed"]:
                            buying_power = balance_data["Computed"]["cashBuyingPower"]
                            if buying_power != 0: acc.set_buying_power(buying_power)
                    else:
                        # Handle errors
                        logger.debug("Response Body: %s", response.text)
                        if response is not None and response.headers['Content-Type'] == 'application/json' \
                                and "Error" in response.json() and "message" in response.json()["Error"] \
                                and response.json()["Error"]["message"] is not None:
                            print("Error: " + response.json()["Error"]["message"])
                        else:
                            print("Error: Balance API service error")
                else:
                    # Handle errors
                    logger.debug("Response Body: %s", response.text)
                    if response is not None and response.headers['Content-Type'] == 'application/json' \
                            and "Error" in response.json() and "message" in response.json()["Error"] \
                            and response.json()["Error"]["message"] is not None:
                        print("Error: " + response.json()["Error"]["message"])
                    else:
                        print("Error: Balance API service error")
            except Exception as e:
                print(e)

    def load_accounts(self):
        """
        Calls account list API to retrieve a list of the user's E*TRADE accounts

        :param self:Passes in parameter authenticated session
        """

        # URL for the API endpoint
        url = self.base_url + "/v1/accounts/list.json"

        # Make API call for GET request
        response = self.session.get(url, header_auth=True)
        logger.debug("Request Header: %s", response.request.headers)

        # Handle and parse response
        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))

            data = response.json()

            # parse account list data using parser
            try:
                # Add Accounts
                self.AccountParser(data)
            except Exception as e:
                logger.info("Error adding Accounts",e)
                print("Error adding Accounts",e)
            else:
                # Add Transactions
                try:
                    self.TransactionParser()
                except Exception as e:
                    logger.info("Error adding Transactions",e)
                # Add Positions
                try:
                    self.PositionsParser()
                except Exception as e:
                    logger.info("Error adding Postions", e)
                # Create Holdings
                try:
                    self.update_holdings()
                except Exception as e:
                    logger.info("Error updating Holdings", e)
                    return False
            return True

        return False

    def account_list(self):
        """
        Calls account list API to retrieve a list of the user's E*TRADE accounts

        :param self:Passes in parameter authenticated session
        """

        # URL for the API endpoint
        url = self.base_url + "/v1/accounts/list.json"

        # Make API call for GET request
        response = self.session.get(url, header_auth=True)
        logger.debug("Request Header: %s", response.request.headers)

        # Handle and parse response
        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))

            data = response.json()

            if data is not None and "AccountListResponse" in data and "Accounts" in data["AccountListResponse"] \
                    and "Account" in data["AccountListResponse"]["Accounts"]:
                accounts = data["AccountListResponse"]["Accounts"]["Account"]
                while True:
                    # Display account list
                    count = 1
                    print("\nBrokerage Account List:")
                    accounts[:] = [d for d in accounts if d.get('accountStatus') != 'CLOSED']
                    for account in accounts:
                        print_str = str(count) + ")\t"
                        if account is not None and "accountId" in account:
                            print_str = print_str + (account["accountId"])
                        if account is not None and "accountDesc" in account \
                                and account["accountDesc"].strip() is not None:
                            print_str = print_str + ", " + account["accountDesc"].strip()
                        if account is not None and "institutionType" in account:
                            print_str = print_str + ", " + account["institutionType"]
                        print(print_str)
                        count = count + 1
                    print(str(count) + ")\t" "Go Back")

                    # Select account option
                    account_index = input("Please select an account: ")
                    if account_index.isdigit() and 0 < int(account_index) < count:
                        if self.base_url == "":
                            self.account = accounts[int(account_index) - 1]
                        else:
                            self.account = accounts[int(account_index) - 1]
                        self.account_menu()
                    elif account_index == str(count):
                        break
                    else:
                        print("Unknown Account Selected!")
            else:
                # Handle errors
                logger.debug("Response Body: %s", response.text)
                if response is not None and response.headers['Content-Type'] == 'application/json' \
                        and "Error" in response.json() and "message" in response.json()["Error"] \
                        and response.json()["Error"]["message"] is not None:
                    print("Error: " + data["Error"]["message"])
                else:
                    print("Error: AccountList API service error")
        else:
            # Handle errors
            logger.debug("Response Body: %s", response.text)
            if response is not None and response.headers['Content-Type'] == 'application/json' \
                    and "Error" in response.json() and "message" in response.json()["Error"] \
                    and response.json()["Error"]["message"] is not None:
                print("Error: " + response.json()["Error"]["message"])
            else:
                print("Please select an option:")
                print("Error: AccountList API service error")

    def TransactionParser(self):
        for acc in self.accounts:
            url = self.base_url + "/v1/accounts/" + acc.accountIdKey + "/transactions.json"
            response = self.session.get(url, header_auth=True)
            logger.debug("Request Header: %s", response.request.headers)
            transactionList = []
            if response is not None and response.status_code == 200:
                parsed = json.loads(response.text)
                logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
                try:
                    transactionDict = response.json()['TransactionListResponse']['Transaction']
                except Exception as e:
                    print(e, "\nTransactionParser No Transactions Error")
                    self.accounts_transactions[acc.accountId] = []
                    continue

                # print(response.json())

                for tx in transactionDict:
                    if tx['transactionType'] not in BANNED_TRANSACTION_TYPE:
                        try:
                            transactionList.append(
                                Transaction(
                                    displaySymbol = tx['brokerage']['displaySymbol'],
                                    symbol = tx['brokerage']['product']['symbol'],
                                    timestamp = tx['transactionDate'],
                                    amount = tx['amount'],
                                    desc = tx['description'],
                                    qty = tx['brokerage']['quantity'],
                                    price = tx['brokerage']['price'],
                                    securityType = tx['brokerage']['product']['securityType'],
                                    txType = tx['transactionType'],
                                    json = tx)
                            )
                        except Exception as e:
                            pass
                            # logger.info("\nTransactionParser: Error Adding Transaction", tx['description'])
            self.accounts_transactions[acc.accountId] = transactionList
        return True

    def PositionsParser(self):
        for acc in self.accounts:
            # URL for the API endpoint
            url = self.base_url + "/v1/accounts/" + acc.accountIdKey + "/portfolio.json"

            # Make API call for GET request
            response = self.session.get(url, header_auth=True)
            logger.debug("Request Header: %s", response.request.headers)
            pos = []
            # Handle and parse response
            if response is not None and response.status_code == 200:
                parsed = json.loads(response.text)
                logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
                data = response.json()
                try:
                    positions = data["PortfolioResponse"]["AccountPortfolio"]
                except Exception as e:
                    print(e,"\nPositionsParser: Error no Positions in Portfolio")
                    self.accounts_positions[acc.accountId] = pos
                    continue
                for acctPortfolio in positions:
                    if acctPortfolio is not None and "Position" in acctPortfolio:
                        for position in acctPortfolio["Position"]:
                            p = Position(symbolDescription=position["symbolDescription"], quantity=position["quantity"],
                                         lastTrade=position["Quick"]["lastTrade"], pricePaid=position["pricePaid"],
                                         totalGain=position["totalGain"], marketValue=position["marketValue"],
                                         pctOfPortfolio=position["pctOfPortfolio"], json=position)
                            pos.append(p)
                self.accounts_positions[acc.accountId] = pos
                #logger.info("PositionsParser: Successfully added Positions for", acc.accountId,"-", acc.accountName)
            else:
                #logger.info("PositionsParser: Error with adding Positions for", acc.accountId,"-", acc.accountName)
                self.accounts_positions[acc.accountId] = pos
        return True

    def transactions(self):
        # url = self.base_url + "/v1/accounts/" + self.account["accountIdKey"] + "/transactions.json"
        url = self.base_url + "/v1/accounts/" + "TkvcooSqcC-IFbCRwRxIAQ" + "/transactions.json"

        response = self.session.get(url, header_auth=True)

        logger.debug("Request Header: %s", response.request.headers)

        print("\nTransaction:")

        print("Transaction URL",url)

        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
            data = response.json()
            print(data)
            print(data['TransactionListResponse']['moreTransactions'])

    def get_transaction(self, idKey):
        url = self.base_url + "/v1/accounts/" + idKey + "/transactions.json"
        response = self.session.get(url, header_auth=True)

        logger.debug("Request Header: %s", response.request.headers)

        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
            data = response.json()
            return data

    def portfolio(self):
        """
        Call portfolio API to retrieve a list of positions held in the specified account

        :param self: Passes in parameter authenticated session and information on selected account
        """

        # URL for the API endpoint
        url =self.base_url + "/v1/accounts/" + self.account["accountIdKey"] + "/portfolio.json"

        # Make API call for GET request
        response = self.session.get(url, header_auth=True)
        logger.debug("Request Header: %s", response.request.headers)

        print("\nPortfolio:")

        # Handle and parse response
        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
            data = response.json()

            print(data)

            if data is not None and "PortfolioResponse" in data and "AccountPortfolio" in data["PortfolioResponse"]:
                # Display balance information
                for acctPortfolio in data["PortfolioResponse"]["AccountPortfolio"]:
                    if acctPortfolio is not None and "Position" in acctPortfolio:
                        for position in acctPortfolio["Position"]:

                            print_str = ""
                            if position is not None and "symbolDescription" in position:
                                print_str = print_str + "Symbol: " + str(position["symbolDescription"])
                            if position is not None and "quantity" in position:
                                print_str = print_str + " | " + "Quantity #: " + str(position["quantity"])
                            if position is not None and "Quick" in position and "lastTrade" in position["Quick"]:
                                print_str = print_str + " | " + "Last Price: " \
                                            + str('${:,.2f}'.format(position["Quick"]["lastTrade"]))
                            if position is not None and "pricePaid" in position:
                                print_str = print_str + " | " + "Price Paid $: " \
                                            + str('${:,.2f}'.format(position["pricePaid"]))
                            if position is not None and "totalGain" in position:
                                print_str = print_str + " | " + "Total Gain $: " \
                                            + str('${:,.2f}'.format(position["totalGain"]))
                            if position is not None and "marketValue" in position:
                                print_str = print_str + " | " + "Value $: " \
                                            + str('${:,.2f}'.format(position["marketValue"]))
                            print(print_str)
                    else:
                        print("None")
            else:
                # Handle errors
                logger.debug("Response Body: %s", response.text)
                if response is not None and "headers" in response and "Content-Type" in response.headers \
                        and response.headers['Content-Type'] == 'application/json' \
                        and "Error" in response.json() and "message" in response.json()["Error"] \
                        and response.json()["Error"]["message"] is not None:
                    print("Error: " + response.json()["Error"]["message"])
                else:
                    print("Error: Portfolio API service error")
        elif response is not None and response.status_code == 204:
            print("None")
        else:
            # Handle errors
            logger.debug("Response Body: %s", response.text)
            if response is not None and "headers" in response and "Content-Type" in response.headers \
                    and response.headers['Content-Type'] == 'application/json' \
                    and "Error" in response.json() and "message" in response.json()["Error"] \
                    and response.json()["Error"]["message"] is not None:
                print("Error: " + response.json()["Error"]["message"])
            else:
                print("Error: Portfolio API service error")

    def balance(self):
        """
        Calls account balance API to retrieve the current balance and related details for a specified account

        :param self: Pass in parameters authenticated session and information on selected account
        """

        # URL for the API endpoint
        url = self.base_url + "/v1/accounts/" + self.account["accountIdKey"] + "/balance.json"

        # Add parameters and header information
        params = {"instType": self.account["institutionType"], "realTimeNAV": "true"}
        headers = {"consumerkey": etrade_config.CONSUMER_KEY}

        # Make API call for GET request
        response = self.session.get(url, header_auth=True, params=params, headers=headers)
        logger.debug("Request url: %s", url)
        logger.debug("Request Header: %s", response.request.headers)

        # Handle and parse response
        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
            data = response.json()
            if data is not None and "BalanceResponse" in data:
                balance_data = data["BalanceResponse"]
                if balance_data is not None and "accountId" in balance_data:
                    print("\n\nBalance for " + balance_data["accountId"] + ":")
                else:
                    print("\n\nBalance:")
                # Display balance information
                if balance_data is not None and "accountDescription" in balance_data:
                    print("Account Nickname: " + balance_data["accountDescription"])
                if balance_data is not None and "Computed" in balance_data \
                        and "RealTimeValues" in balance_data["Computed"] \
                        and "totalAccountValue" in balance_data["Computed"]["RealTimeValues"]:
                    print("Net Account Value: "
                          + str('${:,.2f}'.format(balance_data["Computed"]["RealTimeValues"]["totalAccountValue"])))
                if balance_data is not None and "Computed" in balance_data \
                        and "marginBuyingPower" in balance_data["Computed"]:
                    print("Margin Buying Power: " + str('${:,.2f}'.format(balance_data["Computed"]["marginBuyingPower"])))
                if balance_data is not None and "Computed" in balance_data \
                        and "cashBuyingPower" in balance_data["Computed"]:
                    print("Cash Buying Power: " + str('${:,.2f}'.format(balance_data["Computed"]["cashBuyingPower"])))
            else:
                # Handle errors
                logger.debug("Response Body: %s", response.text)
                if response is not None and response.headers['Content-Type'] == 'application/json' \
                        and "Error" in response.json() and "message" in response.json()["Error"] \
                        and response.json()["Error"]["message"] is not None:
                    print("Error: " + response.json()["Error"]["message"])
                else:
                    print("Error: Balance API service error")
        else:
            # Handle errors
            logger.debug("Response Body: %s", response.text)
            if response is not None and response.headers['Content-Type'] == 'application/json' \
                    and "Error" in response.json() and "message" in response.json()["Error"] \
                    and response.json()["Error"]["message"] is not None:
                print("Error: " + response.json()["Error"]["message"])
            else:
                print("Error: Balance API service error")

    def account_menu(self):
        """
        Provides the different options for the sample application: balance, portfolio, view orders

        :param self: Pass in authenticated session and information on selected account
        """

        if self.account["institutionType"] == "BROKERAGE":
            menu_items = {"1": "Balance",
                          "2": "Portfolio",
                          "3": "Orders",
                          "4": "Transactions",
                          "5": "Go Back"}

            while True:
                print("")
                options = menu_items.keys()
                for entry in options:
                    print(entry + ")\t" + menu_items[entry])

                selection = input("Please select an option: ")

                if selection == "1":
                    self.balance()
                elif selection == "2":
                    self.portfolio()
                elif selection == "3":
                    order = Order(self.session, self.account, self.base_url)
                    order.view_orders()
                elif selection == "4":
                    self.transactions()
                elif selection == "5":
                    break
                else:
                    print("Unknown Option Selected!")
        elif self.account["institutionType"] == "BANK":
            menu_items = {"1": "Balance",
                          "2": "Go Back"}

            while True:
                print("\n")
                options = menu_items.keys()
                for entry in options:
                    print(entry + ")\t" + menu_items[entry])

                selection = input("Please select an option: ")
                if selection == "1":
                    self.balance()
                elif selection == "2":
                    break
                else:
                    print("Unknown Option Selected!")
        else:
            menu_items = {"1": "Go Back"}

            while True:
                print("")
                options = menu_items.keys()
                for entry in options:
                    print(entry + ")\t" + menu_items[entry])

                selection = input("Please select an option: ")
                if selection == "1":
                    break
                else:
                    print("Unknown Option Selected!")
