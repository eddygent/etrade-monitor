#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import random
import re
import sys
import xmltodict
from typing import Union
from jxmlease import emit_xml
import os

import etrade_config
# loading configuration file
from rauth import OAuth1Session

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + '/positions')
from positions.positions import Position
sys.path.insert(0, script_path + '/transactions')
from transactions.transactions import Transaction, BANNED_TRANSACTION_TYPE
sys.path.insert(0, script_path + '/holdings')
from holdings.holdings import SecurityHolding, SecurityHoldings

CALL = "Call"
PUT = "Put"
LOGGER = logging.getLogger(__name__)

# logger settings
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("python_client.log", maxBytes=5 * 1024 * 1024, backupCount=3)
FORMAT = "%(asctime)-15s %(message)s"
fmt = logging.Formatter(FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p')
handler.setFormatter(fmt)
logger.addHandler(handler)


class SecurityOrder:

    def __init__(self, session, account, base_url, security_holdings):
        self.session = session
        self.account = account
        self.base_url = base_url
        self.security_holdings = security_holdings

    @staticmethod
    def parse_options_order(security_holding: SecurityHolding):
        sym, m, d, y, p, t = security_holding.sym.split(" ")
        combined = "-".join([m, d, y.strip("'")])
        dto = datetime.strptime(combined, "%b-%d-%y")
        price = p.strip("$")

        order = {"symbol": sym,
                 "security_type": "OPTN",
                 "price_type": "MARKET",
                 "order_term": "GOOD_FOR_DAY",
                 "order_action": "SELL_CLOSE",
                 "expiryDay": dto.day,
                 "expiryMonth": dto.month,
                 "expiryYear": dto.year,
                 "callPut": t,
                 "strikePrice": price,
                 "limit_price": None,
                 # "quantity": security_holding._can_sell(),
                 "quantity": 1,
                 }
        return order


    def payload_parser(self, order, action="Preview"):
        # Add payload for POST Request
        if order["security_type"] == "EQ":
            payload = f"""<{action}OrderRequest>
                                   <orderType>{order["security_type"]}</orderType>
                                   <clientOrderId>{order["client_order_id"]}</clientOrderId>
                                   <Order>
                                       <allOrNone>false</allOrNone>
                                       <priceType>{order["price_type"]}</priceType>
                                       <orderTerm>{order["order_term"]}</orderTerm>
                                       <marketSession>REGULAR</marketSession>
                                       <stopPrice></stopPrice>
                                       <limitPrice>{order["limit_price"]}</limitPrice>
                                       <Instrument>
                                           <Product>
                                               <securityType>{order["security_type"]}</securityType>
                                               <symbol>{order["symbol"]}</symbol>
                                           </Product>
                                           <orderAction>{order["order_action"]}</orderAction>
                                           <quantityType>QUANTITY</quantityType>
                                           <quantity>{order["quantity"]}</quantity>
                                       </Instrument>
                                   </Order>
                               </{action}OrderRequest>"""
        else:
            payload = f"""<{action}OrderRequest>
                            <Order>
                                <Instrument>
                                    <Product>
                                        <callPut>{order["callPut"].upper()}</callPut>
                                        <expiryDay>{order["expiryDay"]}</expiryDay>
                                        <expiryMonth>{order["expiryMonth"]}</expiryMonth>
                                        <expiryYear>{order["expiryYear"]}</expiryYear>
                                        <securityType>OPTN</securityType>
                                        <strikePrice>{order["strikePrice"]}</strikePrice>
                                        <symbol>{order["symbol"]}</symbol>
                                    </Product>
                                    <orderAction>{order["order_action"]}</orderAction>
                                    <orderedQuantity>{order['quantity']}</orderedQuantity>
                                    <quantity>{order['quantity']}</quantity>
                                </Instrument>
                                <allOrNone>false</allOrNone>
                                <limitPrice>{order['limit_price']}</limitPrice>
                                <marketSession>REGULAR</marketSession>
                                <orderTerm>{order["order_term"]}</orderTerm>
                                <priceType>MARKET</priceType>
                                <stopPrice></stopPrice>
                            </Order>
                            <clientOrderId>{order['client_order_id']}</clientOrderId>
                            <orderType>OPTN</orderType>
                        </{action}OrderRequest>"""
        return payload

    def sell_security_market_order(self, security_holding: SecurityHolding, action = "preview"):
        """
        Call preview order API based on selecting from different given options

        :param self: Pass in authenticated session and information on selected account
        """
        # URL for the API endpoint
        action_dict = {"preview":"Preview", "place":"Place"}
        url = self.base_url + "/v1/accounts/" + self.account.accountIdKey + f"/orders/{action}.json"

        order = {}
        if CALL in security_holding.sym or PUT in security_holding.sym:
            order = self.parse_options_order(security_holding)
            order["client_order_id"] = random.randint(1000000000, 9999999999)
        else:
            order = {"price_type": "MARKET",
                     "order_term": "GOOD_FOR_DAY",
                     "symbol": security_holding.sym,
                     "order_action": "SELL",
                     "limit_price": None,
                     "quantity": security_holding._can_sell(),
                     "security_type": "EQ"
                     }
            order["client_order_id"] = random.randint(1000000000, 9999999999)

        # Add parameters and header information
        headers = {"Content-Type": "application/xml", "consumerKey": etrade_config.CONSUMER_KEY}

        payload = self.payload_parser(order, action_dict[action])

        # Make API call for POST request
        response = self.session.post(url, header_auth=True, headers=headers, data=payload)
        logger.debug("Request Header: %s", response.request.headers)
        logger.debug("Request payload: %s", payload)

        # Handle and parse response
        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
            data = response.json()
            print("\nPreview Order:")

            if data is not None and f"{action_dict[action]}OrderResponse" in data and f"{action_dict[action]}Ids" in data[f"{action_dict[action]}OrderResponse"]:
                for previewids in data[f"{action_dict[action]}OrderResponse"][f"{action_dict[action]}Ids"]:
                    print(f"{action_dict[action]} ID: " + str(previewids[f"{action}Id"]))
            else:
                # Handle errors
                data = response.json()
                if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                    print("Error: " + data["Error"]["message"])
                else:
                    print(f"Error: {action_dict[action]} Order API service error")

            if data is not None and f"{action_dict[action]}OrderResponse" in data and "Order" in data[f"{action_dict[action]}OrderResponse"]:
                for orders in data[f"{action_dict[action]}OrderResponse"]["Order"]:
                    order["limitPrice"] = orders["limitPrice"]

                    if orders is not None and "Instrument" in orders:
                        for instrument in orders["Instrument"]:
                            if instrument is not None and "orderAction" in instrument:
                                print("Action: " + instrument["orderAction"])
                            if instrument is not None and "quantity" in instrument:
                                print("Quantity: " + str(instrument["quantity"]))
                            if instrument is not None and "Product" in instrument \
                                    and "symbol" in instrument["Product"]:
                                print("Symbol: " + instrument["Product"]["symbol"])
                            if instrument is not None and "symbolDescription" in instrument:
                                print("Description: " + str(instrument["symbolDescription"]))

                if orders is not None and "priceType" in orders and "limitPrice" in orders:
                    print("Price Type: " + orders["priceType"])
                    if orders["priceType"] == "MARKET":
                        print("Price: MKT")
                    else:
                        print("Price: " + str(orders["limitPrice"]))
                if orders is not None and "orderTerm" in orders:
                    print("Duration: " + orders["orderTerm"])
                if orders is not None and "estimatedCommission" in orders:
                    print("Estimated Commission: " + str(orders["estimatedCommission"]))
                if orders is not None and "estimatedTotalAmount" in orders:
                    print("Estimated Total Cost: " + str(orders["estimatedTotalAmount"]))
            else:
                # Handle errors
                data = response.json()
                if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                    print("Error: " + data["Error"]["message"])
                else:
                    print(f"Error: {action_dict[action]} Order API service error")
        else:
            # Handle errors
            data = response.json()
            if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                print("Error: " + data["Error"]["message"])
            else:
                print(f"Error: {action_dict[action]} Order API service error")

    def preview_order(self):
        """
        Call preview order API based on selecting from different given options

        :param self: Pass in authenticated session and information on selected account
        """

        # User's order selection

        order = self.user_select_order()

        # URL for the API endpoint
        url = self.base_url + "/v1/accounts/" + self.account.accountIdKey + "/orders/preview.json"

        # Add parameters and header information
        headers = {"Content-Type": "application/xml", "consumerKey": etrade_config.CONSUMER_KEY}

        # Add payload for POST Request
        payload = """<PreviewOrderRequest>
                       <orderType>EQ</orderType>
                       <clientOrderId>{0}</clientOrderId>
                       <Order>
                           <allOrNone>false</allOrNone>
                           <priceType>{1}</priceType>
                           <orderTerm>{2}</orderTerm>
                           <marketSession>REGULAR</marketSession>
                           <stopPrice></stopPrice>
                           <limitPrice>{3}</limitPrice>
                           <Instrument>
                               <Product>
                                   <securityType>EQ</securityType>
                                   <symbol>{4}</symbol>
                               </Product>
                               <orderAction>{5}</orderAction>
                               <quantityType>QUANTITY</quantityType>
                               <quantity>{6}</quantity>
                           </Instrument>
                       </Order>
                   </PreviewOrderRequest>"""
        payload = payload.format(order["client_order_id"], order["price_type"], order["order_term"],
                                 order["limit_price"], order["symbol"], order["order_action"], order["quantity"])

        # Make API call for POST request
        response = self.session.post(url, header_auth=True, headers=headers, data=payload)
        logger.debug("Request Header: %s", response.request.headers)
        logger.debug("Request payload: %s", payload)

        # Handle and parse response
        if response is not None and response.status_code == 200:
            parsed = json.loads(response.text)
            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
            data = response.json()
            print("\nPreview Order:")

            if data is not None and "PreviewOrderResponse" in data and "PreviewIds" in data["PreviewOrderResponse"]:
                for previewids in data["PreviewOrderResponse"]["PreviewIds"]:
                    print("Preview ID: " + str(previewids["previewId"]))
            else:
                # Handle errors
                data = response.json()
                if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                    print("Error: " + data["Error"]["message"])
                else:
                    print("Error: Preview Order API service error")

            if data is not None and "PreviewOrderResponse" in data and "Order" in data["PreviewOrderResponse"]:
                for orders in data["PreviewOrderResponse"]["Order"]:
                    order["limitPrice"] = orders["limitPrice"]

                    if orders is not None and "Instrument" in orders:
                        for instrument in orders["Instrument"]:
                            if instrument is not None and "orderAction" in instrument:
                                print("Action: " + instrument["orderAction"])
                            if instrument is not None and "quantity" in instrument:
                                print("Quantity: " + str(instrument["quantity"]))
                            if instrument is not None and "Product" in instrument \
                                    and "symbol" in instrument["Product"]:
                                print("Symbol: " + instrument["Product"]["symbol"])
                            if instrument is not None and "symbolDescription" in instrument:
                                print("Description: " + str(instrument["symbolDescription"]))

                if orders is not None and "priceType" in orders and "limitPrice" in orders:
                    print("Price Type: " + orders["priceType"])
                    if orders["priceType"] == "MARKET":
                        print("Price: MKT")
                    else:
                        print("Price: " + str(orders["limitPrice"]))
                if orders is not None and "orderTerm" in orders:
                    print("Duration: " + orders["orderTerm"])
                if orders is not None and "estimatedCommission" in orders:
                    print("Estimated Commission: " + str(orders["estimatedCommission"]))
                if orders is not None and "estimatedTotalAmount" in orders:
                    print("Estimated Total Cost: " + str(orders["estimatedTotalAmount"]))
            else:
                # Handle errors
                data = response.json()
                if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                    print("Error: " + data["Error"]["message"])
                else:
                    print("Error: Preview Order API service error")
        else:
            # Handle errors
            data = response.json()
            if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                print("Error: " + data["Error"]["message"])
            else:
                print("Error: Preview Order API service error")

    def previous_order(self, session, account, prev_orders):
        """
        Calls preview order API based on a list of previous orders

        :param session: authenticated session
        :param account: information on selected account
        :param prev_orders: list of instruments from previous orders
        """

        if prev_orders is not None:
            while True:
                # Display previous instruments for user selection
                print("")
                count = 1
                for order in prev_orders:
                    print(str(count) + ")\tOrder Action: " + order["order_action"] + " | "
                          + "Security Type: " + str(order["security_type"]) + " | "
                          + "Term: " + str(order["order_term"]) + " | "
                          + "Quantity: " + str(order["quantity"]) + " | "
                          + "Symbol: " + order["symbol"] + " | "
                          + "Price Type: " + order["price_type"])
                    count = count + 1
                print(str(count) + ")\t" "Go Back")
                options_select = input("Please select an option: ")

                if options_select.isdigit() and 0 < int(options_select) < len(prev_orders) + 1:

                    # URL for the API endpoint
                    url = self.base_url + "/v1/accounts/" + account["accountIdKey"] + "/orders/preview.json"

                    # Add parameters and header information
                    headers = {"Content-Type": "application/xml", "consumerKey": etrade_config.CONSUMER_KEY}

                    # Add payload for POST Request
                    payload = """<PreviewOrderRequest>
                                   <orderType>{0}</orderType>
                                   <clientOrderId>{1}</clientOrderId>
                                   <Order>
                                       <allOrNone>false</allOrNone>
                                       <priceType>{2}</priceType>  
                                       <orderTerm>{3}</orderTerm>   
                                       <marketSession>REGULAR</marketSession>
                                       <stopPrice></stopPrice>
                                       <limitPrice>{4}</limitPrice>
                                       <Instrument>
                                           <Product>
                                               <securityType>{5}</securityType>
                                               <symbol>{6}</symbol>
                                           </Product>
                                           <orderAction>{7}</orderAction> 
                                           <quantityType>QUANTITY</quantityType>
                                           <quantity>{8}</quantity>
                                       </Instrument>
                                   </Order>
                               </PreviewOrderRequest>"""

                    options_select = int(options_select)
                    prev_orders[options_select - 1]["client_order_id"] = str(random.randint(1000000000, 9999999999))
                    payload = payload.format(prev_orders[options_select - 1]["order_type"],
                                             prev_orders[options_select - 1]["client_order_id"],
                                             prev_orders[options_select - 1]["price_type"],
                                             prev_orders[options_select - 1]["order_term"],
                                             prev_orders[options_select - 1]["limitPrice"],
                                             prev_orders[options_select - 1]["security_type"],
                                             prev_orders[options_select - 1]["symbol"],
                                             prev_orders[options_select - 1]["order_action"],
                                             prev_orders[options_select - 1]["quantity"])

                    # Make API call for POST request
                    response = session.post(url, header_auth=True, headers=headers, data=payload)
                    logger.debug("Request Header: %s", response.request.headers)
                    logger.debug("Request payload: %s", payload)

                    # Handle and parse response
                    if response is not None and response.status_code == 200:
                        parsed = json.loads(response.text)
                        logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
                        data = response.json()
                        print("\nPreview Order: ")
                        if data is not None and "PreviewOrderResponse" in data and "PreviewIds" in data["PreviewOrderResponse"]:
                            for previewids in data["PreviewOrderResponse"]["PreviewIds"]:
                                print("Preview ID: " + str(previewids["previewId"]))
                        else:
                            # Handle errors
                            data = response.json()
                            if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                                print("Error: " + data["Error"]["message"])
                            else:
                                print("Error: Preview Order API service error")

                        if data is not None and "PreviewOrderResponse" in data and "Order" in data[
                            "PreviewOrderResponse"]:
                            for orders in data["PreviewOrderResponse"]["Order"]:
                                prev_orders[options_select - 1]["limitPrice"] = orders["limitPrice"]

                                if orders is not None and "Instrument" in orders:
                                    for instruments in orders["Instrument"]:
                                        if instruments is not None and "orderAction" in instruments:
                                            print("Action: " + instruments["orderAction"])
                                        if instruments is not None and "quantity" in instruments:
                                            print("Quantity: " + str(instruments["quantity"]))
                                        if instruments is not None and "Product" in instruments \
                                                and "symbol" in instruments["Product"]:
                                            print("Symbol: " + instruments["Product"]["symbol"])
                                        if instruments is not None and "symbolDescription" in instruments:
                                            print("Description: " + str(instruments["symbolDescription"]))

                            if orders is not None and "priceType" in orders and "limitPrice" in orders:
                                print("Price Type: " + orders["priceType"])
                                if orders["priceType"] == "MARKET":
                                    print("Price: MKT")
                                else:
                                    print("Price: " + str(orders["limitPrice"]))
                            if orders is not None and "orderTerm" in orders:
                                print("Duration: " + orders["orderTerm"])
                            if orders is not None and "estimatedCommission" in orders:
                                print("Estimated Commission: " + str(orders["estimatedCommission"]))
                            if orders is not None and "estimatedTotalAmount" in orders:
                                print("Estimated Total Cost: " + str(orders["estimatedTotalAmount"]))
                        else:
                            # Handle errors
                            data = response.json()
                            if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                                print("Error: " + data["Error"]["message"])
                            else:
                                print("Error: Preview Order API service error")
                    else:
                        # Handle errors
                        data = response.json()
                        if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                            print("Error: " + data["Error"]["message"])
                        else:
                            print("Error: Preview Order API service error")
                    break
                elif options_select.isdigit() and int(options_select) == len(prev_orders) + 1:
                    break
                else:
                    print("Unknown Option Selected!")

    @staticmethod
    def print_orders(response, status):
        """
        Formats and displays a list of orders

        :param response: response object of a list of orders
        :param status: order status related to the response object
        :return a list of previous orders
        """
        prev_orders = []
        if response is not None and "OrdersResponse" in response and "Order" in response["OrdersResponse"]:
            for order in response["OrdersResponse"]["Order"]:
                if order is not None and "OrderDetail" in order:
                    for details in order["OrderDetail"]:
                        if details is not None and "Instrument" in details:
                            for instrument in details["Instrument"]:
                                order_str = ""
                                order_obj = {"price_type": None,
                                             "order_term": None,
                                             "order_indicator": None,
                                             "order_type": None,
                                             "security_type": None,
                                             "symbol": None,
                                             "order_action": None,
                                             "quantity": None}
                                if order is not None and 'orderType' in order:
                                    order_obj["order_type"] = order["orderType"]

                                if order is not None and 'orderId' in order:
                                    order_str += "Order #" + str(order["orderId"]) + " : "

                                if instrument is not None and 'Product' in instrument \
                                        and 'securityType' in instrument["Product"]:
                                    order_str += "Type: " + instrument["Product"]["securityType"] + " | "
                                    order_obj["security_type"] = instrument["Product"]["securityType"]

                                if instrument is not None and 'orderAction' in instrument:
                                    order_str += "Order Type: " + instrument["orderAction"] + " | "
                                    order_obj["order_action"] = instrument["orderAction"]

                                if instrument is not None and 'orderedQuantity' in instrument:
                                    order_str += "Quantity(Exec/Entered): " + str("{:,}".format(instrument["orderedQuantity"])) + " | "
                                    order_obj["quantity"] = instrument["orderedQuantity"]

                                if instrument is not None and 'Product' in instrument and 'symbol' in instrument["Product"]:
                                    order_str += "Symbol: " + instrument["Product"]["symbol"] + " | "
                                    order_obj["symbol"] = instrument["Product"]["symbol"]

                                if details is not None and 'priceType' in details:
                                    order_str += "Price Type: " + details["priceType"] + " | "
                                    order_obj["price_type"] = details["priceType"]

                                if details is not None and 'orderTerm' in details:
                                    order_str += "Term: " + details["orderTerm"] + " | "
                                    order_obj["order_term"] = details["orderTerm"]

                                if details is not None and 'limitPrice' in details:
                                    order_str += "Price: " + str('${:,.2f}'.format(details["limitPrice"])) + " | "
                                    order_obj["limitPrice"] = details["limitPrice"]

                                if status == "Open" and details is not None and 'netBid' in details:
                                    order_str += "Bid: " + details["netBid"] + " | "
                                    order_obj["bid"] = details["netBid"]

                                if status == "Open" and details is not None and 'netAsk' in details:
                                    order_str += "Ask: " + details["netAsk"] + " | "
                                    order_obj["ask"] = details["netAsk"]

                                if status == "Open" and details is not None and 'netPrice' in details:
                                    order_str += "Last Price: " + details["netPrice"] + " | "
                                    order_obj["netPrice"] = details["netPrice"]

                                if status == "indiv_fills" and instrument is not None and 'filledQuantity' in instrument:
                                    order_str += "Quantity Executed: " + str("{:,}".format(instrument["filledQuantity"])) + " | "
                                    order_obj["quantity"] = instrument["filledQuantity"]

                                if status != "open" and status != "expired" and status != "rejected" and instrument is not None \
                                        and "averageExecutionPrice" in instrument:
                                    order_str += "Price Executed: " + str('${:,.2f}'.format(instrument["averageExecutionPrice"])) + " | "

                                if status != "expired" and status != "rejected" and details is not None and 'status' in details:
                                    order_str += "Status: " + details["status"]

                                print(order_str)
                                prev_orders.append(order_obj)
        return prev_orders

    @staticmethod
    def options_selection(options):
        """
        Formats and displays different options in a menu

        :param options: List of options to display
        :return the number user selected
        """
        while True:
            print("")
            for num, price_type in enumerate(options, start=1):
                print("{})\t{}".format(num, price_type))
            options_select = input("Please select an option: ")
            if options_select.isdigit() and 0 < int(options_select) < len(options) + 1:
                return options_select
            else:
                print("Unknown Option Selected!")

    def user_select_order(self):
        """
            Provides users options to select to preview orders
            :param self test
            :return user's order selections
            """
        order = {"price_type": "",
                 "order_term": "",
                 "symbol": "",
                 "order_action": "",
                 "limit_price":"",
                 "quantity": ""}

        price_type_options = ["MARKET", "LIMIT"]
        order_term_options = ["GOOD_FOR_DAY", "IMMEDIATE_OR_CANCEL", "FILL_OR_KILL"]
        order_action_options = ["BUY", "SELL", "BUY_TO_COVER", "SELL_SHORT"]

        print("\nPrice Type:")
        order["price_type"] = price_type_options[int(self.options_selection(price_type_options)) - 1]

        if order["price_type"] == "MARKET":
            order["order_term"] = "GOOD_FOR_DAY"
        else:
            print("\nOrder Term:")
            order["order_term"] = order_term_options[int(self.options_selection(order_term_options)) - 1]

        order["limit_price"] = None
        if order["price_type"] == "LIMIT":
            while order["limit_price"] is None or not order["limit_price"].isdigit() \
                    and not re.match(r'\d+(?:[.]\d{2})?$', order["limit_price"]):
                order["limit_price"] = input("\nPlease input limit price: ")

        order["client_order_id"] = random.randint(1000000000, 9999999999)

        while order["symbol"] == "":
            order["symbol"] = input("\nPlease enter a stock symbol :")

        print("\nOrder Action Type:")
        order["order_action"] = order_action_options[int(self.options_selection(order_action_options)) - 1]

        while not order["quantity"].isdigit():
            order["quantity"] = input("\nPlease type quantity:")

        return order

    def preview_order_menu(self, session, account, prev_orders):
        """
        Provides the different options for preview orders: select new order or select from previous order

        :param session: authenticated session
        :param account: information on selected account
        :param prev_orders: list of instruments from previous orders
        """
        menu_list = {"1": "Select New Order",
                     "2": "Select From Previous Orders",
                     "3": "Select From Holdings",
                     "4": "Go Back"}

        while True:
            print("")
            options = menu_list.keys()
            for entry in options:
                print(entry + ")\t" + menu_list[entry])

            selection = input("Please select an option: ")
            if selection == "1":
                print("\nPreview Order: ")
                self.preview_order()
                break
            elif selection == "2":
                self.previous_order(session, account, prev_orders)
                break
            elif selection == "4":
                break
            elif selection  == "3":
                print("Select Sell From Holdings")
                self.sell_from_holdings()
            else:
                print("Unknown Option Selected!")

    def sell_from_holdings(self):
        holdings_matrix = {}
        ignore = [] # ignore these symbols
        while True:
            display = []
            security_holdings_keys = [i for i in self.security_holdings.holdings.keys() if i not in ignore ]
            for i,sym in enumerate(security_holdings_keys):
                display.append(f'\t{i+1}) { self.security_holdings.holdings[sym]}')
                holdings_matrix[str(i+1)] = sym

            while True:
                print("Holdings:")
                print("\n".join(display))
                input_choice = input("Enter the number you would like to sell from holdings (e to exit): ")
                try:
                    choice = self.security_holdings.holdings[holdings_matrix[input_choice]]
                except KeyError:
                    if input_choice.lower() == "e": break
                    print("That is not a valid answer. Please Try again.")
                    continue
                print(f"You want to sell: {choice}")

                pv_or_pl = input("Preview or Place order (any key to preview, or 'place' to place): ")
                action = "preview"
                if pv_or_pl.lower() == 'place':
                    action = pv_or_pl
                    # ignore.append(holdings_matrix[input_choice])  # ignore this key when displaying table again
                self.sell_security_market_order(choice, action)
                break
            inp = input("Do you want to place another order (y or any key to exit): ")
            if inp.lower() == 'y': continue
            else: break



    def cancel_order(self):
        """
        Calls cancel order API to cancel an existing order
        :param self: Pass parameter with authenticated session and information on selected account
        """
        while True:
            # Display a list of Open Orders
            # URL for the API endpoint
            url = self.base_url + "/v1/accounts/" + self.account.accountIdKey + "/orders.json"

            # Add parameters and header information
            params_open = {"status": "OPEN"}
            headers = {"consumerkey": etrade_config.CONSUMER_KEY}

            # Make API call for GET request
            response_open = self.session.get(url, header_auth=True, params=params_open, headers=headers)

            logger.debug("Request Header: %s", response_open.request.headers)
            logger.debug("Response Body: %s", response_open.text)

            print("\nOpen Orders: ")
            # Handle and parse response
            if response_open.status_code == 204:
                logger.debug(response_open)
                print("None")
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
                break
            elif response_open.status_code == 200:
                parsed = json.loads(response_open.text)
                logger.debug(json.dumps(parsed, indent=4, sort_keys=True))
                data = response_open.json()

                order_list = []
                count = 1
                if data is not None and "OrdersResponse" in data and "Order" in data["OrdersResponse"]:
                    for order in data["OrdersResponse"]["Order"]:
                        if order is not None and "OrderDetail" in order:
                            for details in order["OrderDetail"]:
                                if details is not None and "Instrument" in details:
                                    for instrument in details["Instrument"]:
                                        order_str = ""
                                        order_obj = {"price_type": None,
                                                     "order_term": None,
                                                     "order_indicator": None,
                                                     "order_type": None,
                                                     "security_type": None,
                                                     "symbol": None,
                                                     "order_action": None,
                                                     "quantity": None}
                                        if order is not None and 'orderType' in order:
                                            order_obj["order_type"] = order["orderType"]

                                        if order is not None and 'orderId' in order:
                                            order_str += "Order #" + str(order["orderId"]) + " : "
                                        if instrument is not None and 'Product' in instrument and 'securityType' \
                                                in instrument["Product"]:
                                            order_str += "Type: " + instrument["Product"]["securityType"] + " | "
                                            order_obj["security_type"] = instrument["Product"]["securityType"]

                                        if instrument is not None and 'orderAction' in instrument:
                                            order_str += "Order Type: " + instrument["orderAction"] + " | "
                                            order_obj["order_action"] = instrument["orderAction"]

                                        if instrument is not None and 'orderedQuantity' in instrument:
                                            order_str += "Quantity(Exec/Entered): " + str(
                                                "{:,}".format(instrument["orderedQuantity"])) + " | "
                                            order_obj["quantity"] = instrument["orderedQuantity"]

                                        if instrument is not None and 'Product' in instrument and 'symbol' \
                                                in instrument["Product"]:
                                            order_str += "Symbol: " + instrument["Product"]["symbol"] + " | "
                                            order_obj["symbol"] = instrument["Product"]["symbol"]

                                        if details is not None and 'priceType' in details:
                                            order_str += "Price Type: " + details["priceType"] + " | "
                                            order_obj["price_type"] = details["priceType"]

                                        if details is not None and 'orderTerm' in details:
                                            order_str += "Term: " + details["orderTerm"] + " | "
                                            order_obj["order_term"] = details["orderTerm"]

                                        if details is not None and 'limitPrice' in details:
                                            order_str += "Price: " + str(
                                                '${:,.2f}'.format(details["limitPrice"])) + " | "
                                            order_obj["limitPrice"] = details["limitPrice"]

                                        if instrument is not None and 'filledQuantity' in instrument:
                                            order_str += "Quantity Executed: " \
                                                         + str("{:,}".format(instrument["filledQuantity"])) + " | "
                                            order_obj["quantity"] = instrument["filledQuantity"]

                                        if instrument is not None and "averageExecutionPrice" in instrument:
                                            order_str += "Price Executed: " + str(
                                                '${:,.2f}'.format(instrument["averageExecutionPrice"])) + " | "

                                        if details is not None and 'status' in details:
                                            order_str += "Status: " + details["status"]

                                        print(str(count) + ")\t" + order_str)
                                        count = 1 + count
                                        order_list.append(order["orderId"])

                    print(str(count) + ")\tGo Back")
                    selection = input("Please select an option: ")
                    if selection.isdigit() and 0 < int(selection) < len(order_list) + 1:
                        # URL for the API endpoint
                        url = self.base_url + "/v1/accounts/" + self.account.accountIdKey + "/orders/cancel.json"

                        # Add parameters and header information
                        headers = {"Content-Type": "application/xml", "consumerKey": etrade_config.CONSUMER_KEY}

                        # Add payload for POST Request
                        payload = """<CancelOrderRequest>
                                        <orderId>{0}</orderId>
                                    </CancelOrderRequest>
                                   """
                        payload = payload.format(order_list[int(selection) - 1])

                        # Add payload for PUT Request
                        response = self.session.put(url, header_auth=True, headers=headers, data=payload)
                        logger.debug("Request Header: %s", response.request.headers)
                        logger.debug("Request payload: %s", payload)

                        # Handle and parse response
                        if response is not None and response.status_code == 200:
                            parsed = json.loads(response.text)
                            logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
                            data = response.json()
                            if data is not None and "CancelOrderResponse" in data \
                                    and "orderId" in data["CancelOrderResponse"]:
                                print("\nOrder number #" + str(
                                    data["CancelOrderResponse"]["orderId"]) + " successfully Cancelled.")
                            else:
                                # Handle errors
                                logger.debug("Response Headers: %s", response.headers)
                                logger.debug("Response Body: %s", response.text)
                                data = response.json()
                                if 'Error' in data and 'message' in data["Error"] \
                                        and data["Error"]["message"] is not None:
                                    print("Error: " + data["Error"]["message"])
                                else:
                                    print("Error: Cancel Order API service error")
                        else:
                            # Handle errors
                            logger.debug("Response Headers: %s", response.headers)
                            logger.debug("Response Body: %s", response.text)
                            data = response.json()
                            if 'Error' in data and 'message' in data["Error"] and data["Error"]["message"] is not None:
                                print("Error: " + data["Error"]["message"])
                            else:
                                print("Error: Cancel Order API service error")
                        break

                    elif selection.isdigit() and int(selection) == len(order_list) + 1:
                        break
                    else:
                        print("Unknown Option Selected!")
                else:
                    # Handle errors
                    logger.debug("Response Body: %s", response_open.text)
                    if response_open is not None and response_open.headers['Content-Type'] == 'application/json' \
                            and "Error" in response_open.json() and "message" in response_open.json()["Error"] \
                            and response_open.json()["Error"]["message"] is not None:
                        print("Error: " + response_open.json()["Error"]["message"])
                    else:
                        print("Error: Balance API service error")
                    break
            else:
                # Handle errors
                logger.debug("Response Body: %s", response_open.text)
                if response_open is not None and response_open.headers['Content-Type'] == 'application/json' \
                        and "Error" in response_open.json() and "message" in response_open.json()["Error"] \
                        and response_open.json()["Error"]["message"] is not None:
                    print("Error: " + response_open.json()["Error"]["message"])
                else:
                    print("Error: Balance API service error")
                break

    def view_orders(self):
        """
        Calls orders API to provide the details for the orders

        :param self: Pass in authenticated session and information on selected account
        """
        while True:
            # URL for the API endpoint
            url = self.base_url + "/v1/accounts/" + self.account.accountIdKey + "/orders.json"

            # Add parameters and header information
            headers = {"consumerkey": etrade_config.CONSUMER_KEY}
            params_open = {"status": "OPEN"}
            params_executed = {"status": "EXECUTED"}
            params_indiv_fills = {"status": "INDIVIDUAL_FILLS"}
            params_cancelled = {"status": "CANCELLED"}
            params_rejected = {"status": "REJECTED"}
            params_expired = {"status": "EXPIRED"}

            # Make API call for GET request
            response_open = self.session.get(url, header_auth=True, params=params_open, headers=headers)
            response_executed = self.session.get(url, header_auth=True, params=params_executed, headers=headers)
            response_indiv_fills = self.session.get(url, header_auth=True, params=params_indiv_fills, headers=headers)
            response_cancelled = self.session.get(url, header_auth=True, params=params_cancelled, headers=headers)
            response_rejected = self.session.get(url, header_auth=True, params=params_rejected, headers=headers)
            response_expired = self.session.get(url, header_auth=True, params=params_expired, headers=headers)

            prev_orders = []

            # Open orders
            logger.debug("Request Header: %s", response_open.request.headers)
            logger.debug("Response Body: %s", response_open.text)

            print("\nOpen Orders:")
            # Handle and parse response
            if response_open.status_code == 204:
                logger.debug(response_open)
                print("None")
            elif response_open.status_code == 200:
                parsed = json.loads(response_open.text)
                logger.debug(json.dumps(parsed, indent=4, sort_keys=True))
                data = response_open.json()

                # Display list of open orders
                prev_orders.extend(self.print_orders(data, "open"))

            # Executed orders
            logger.debug("Request Header: %s", response_executed.request.headers)
            logger.debug("Response Body: %s", response_executed.text)
            logger.debug(response_executed.text)

            print("\nExecuted Orders:")
            # Handle and parse response
            if response_executed.status_code == 204:
                logger.debug(response_executed)
                print("None")
            elif response_executed.status_code == 200:
                parsed = json.loads(response_executed.text)
                logger.debug(json.dumps(parsed, indent=4, sort_keys=True))
                data = response_executed.json()

                # Display list of executed orders
                prev_orders.extend(self.print_orders(data, "executed"))

            # Individual fills orders
            logger.debug("Request Header: %s", response_indiv_fills.request.headers)
            logger.debug("Response Body: %s", response_indiv_fills.text)

            print("\nIndividual Fills Orders:")
            # Handle and parse response
            if response_indiv_fills.status_code == 204:
                logger.debug("Response Body: %s", response_indiv_fills)
                print("None")
            elif response_indiv_fills.status_code == 200:
                parsed = json.loads(response_indiv_fills.text)
                logger.debug("Response Body: %s", json.dumps(parsed, indent=4, sort_keys=True))
                data = response_indiv_fills.json()

                # Display list of individual fills orders
                prev_orders.extend(self.print_orders(data, "indiv_fills"))

            # Cancelled orders
            logger.debug("Request Header: %s", response_cancelled.request.headers)
            logger.debug("Response Body: %s", response_cancelled.text)

            print("\nCancelled Orders:")
            # Handle and parse response
            if response_cancelled.status_code == 204:
                logger.debug(response_cancelled)
                print("None")
            elif response_cancelled.status_code == 200:
                parsed = json.loads(response_cancelled.text)
                logger.debug(json.dumps(parsed, indent=4, sort_keys=True))
                data = response_cancelled.json()

                # Display list of open orders
                prev_orders.extend(self.print_orders(data, "cancelled"))

            # Rejected orders
            logger.debug("Request Header: %s", response_rejected.request.headers)
            logger.debug("Response Body: %s", response_rejected.text)

            print("\nRejected Orders:")
            # Handle and parse response
            if response_rejected.status_code == 204:
                logger.debug(response_rejected)
                print("None")
            elif response_rejected.status_code == 200:
                parsed = json.loads(response_rejected.text)
                logger.debug(json.dumps(parsed, indent=4, sort_keys=True))
                data = response_rejected.json()

                # Display list of open orders
                prev_orders.extend(self.print_orders(data, "rejected"))

            # Expired orders
            print("\nExpired Orders:")
            # Handle and parse response
            if response_expired.status_code == 204:
                logger.debug(response_executed)
                print("None")
            elif response_expired.status_code == 200:
                parsed = json.loads(response_expired.text)
                logger.debug(json.dumps(parsed, indent=4, sort_keys=True))
                data = response_expired.json()

                # Display list of open orders
                prev_orders.extend(self.print_orders(data, "expired"))

            menu_list = {"1": "Preview Order",
                         "2": "Cancel Order",
                         "3": "Go Back"}

            print("")
            options = menu_list.keys()
            for entry in options:
                print(entry + ")\t" + menu_list[entry])

            selection = input("Please select an option: ")
            if selection == "1":
                self.preview_order_menu(self.session, self.account, prev_orders)
            elif selection == "2":
                self.cancel_order()
            elif selection == "3":
                break
            else:
                print("Unknown Option Selected!")

#### ETRADEORDER GIT
# price: number
# round_down: bool
# return string
def to_decimal_str(price: float, round_down: bool) -> str:
    spstr = "%.2f" % price  # round to 2-place decimal
    spstrf = float(spstr)  # convert back to float again
    diff = price - spstrf

    if diff != 0:  # have to work hard to round to decimal
        HALF_CENT = 0.005  # e.g. BUY  stop: round   up to decimal

        if round_down:
            HALF_CENT *= -1  # e.g. SELL stop: round down to decimal
        price += HALF_CENT

        if price > 0:
            spstr = "%.2f" % price  # now round to 2-place decimal

    return spstr


# resp_format: xml (default)
# empty_json: either [] or {}, depends on the caller's semantics
def get_request_result(req: OAuth1Session.request, empty_json: dict, resp_format: str = "xml") -> dict:
    LOGGER.debug(req.text)

    if resp_format == "json":
        if req.text.strip() == "":
            # otherwise, when ETrade server return empty string, we got this error:
            # simplejson.errors.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
            req_output = empty_json  # empty json object
        else:
            req_output = req.json()
    else:
        xmlstr = req.text
        # import xml.etree.ElementTree as ET
        # xml_data = ET.parse(req.text).getroot()
        # xmlstr = ET.tostring(xml_data, encoding='utf-8', method='xml')

        req_output = xmltodict.parse(xmlstr)

    if 'Error' in req_output.keys():
        raise Exception(f'Etrade API Error - Code: {req_output["Error"]["code"]}, Msg: {req_output["Error"]["message"]}')
    else:
        return req_output


# return Etrade internal option symbol: e.g. "PLTR--220218P00023000" ref:_test_option_symbol()
def option_symbol(symbol: str, call_put: str, expiry_date: datetime, strike_price: float) -> str:
    sym = symbol.strip().upper()
    symstr = sym + ("-" * (6 - len(sym)))

    edstr = expiry_date.strftime("%y%m%d")
    assert (len(edstr) == 6)

    sp = "%08d" % (float(strike_price) * 1000)
    assert (len(sp) == 8)

    opt_sym = symstr + edstr + call_put.strip().upper()[0] + sp
    assert (len(opt_sym) == 21)

    return opt_sym


class OrderException(Exception):
    """:description: Exception raised when giving bad args to a method not from Etrade calls
    """

    def __init__(self, explanation=None, params=None) -> None:
        super().__init__()
        self.required = params
        self.args = (explanation, params)

    def __str__(self) -> str:
        return "Missing required parameters"


class ETradeOrder:
    """:description: Object to perform Orders
       :param client_key: Client key provided by Etrade
       :type client_key: str, required
       :param client_secret: Client secret provided by Etrade
       :type client_secret: str, required
       :param resource_owner_key: Resource key from :class:`pyetrade.authorization.ETradeOAuth`
       :type resource_owner_key: str, required
       :param resource_owner_secret: Resource secret from
            :class:`pyetrade.authorization.ETradeOAuth`
       :type resource_owner_secret: str, required
       :param dev: Defines Sandbox (True) or Live (False) ETrade, defaults to True
       :type dev: bool, optional
       :param timeout: Timeout value for OAuth, defaults to 30
       :type timeout: int, optional
       :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
    """

    def __init__(
        self,
        session,
        base_url,
        account_id_key,
        security_holding_obj,
        timeout=30,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.session = session
        self.account_id_key = account_id_key
        self.security_holdings_obj = security_holding_obj

    def sell_from_holdings(self):
        holdings_matrix = {}
        ignore = [] # ignore these symbols
        while True:
            display = []
            security_holdings_keys = [i for i in self.security_holdings_obj.holdings.keys() if i not in ignore ]
            for i,sym in enumerate(security_holdings_keys):
                display.append(f'\t{i+1}) { self.security_holdings_obj.holdings[sym]}')
                holdings_matrix[str(i+1)] = sym

            while True:
                print("Holdings:")
                print("\n".join(display))
                input_choice = input("Enter the number you would like to sell from holdings (e to exit): ")
                try:
                    choice = self.security_holdings_obj.holdings[holdings_matrix[input_choice]]
                except KeyError:
                    if input_choice.lower() == "e": break
                    print("That is not a valid answer. Please Try again.")
                    continue
                print(f"You want to sell: {choice}")

                pv_or_pl = input("Preview or Place order (any key to preview, or 'place' to place): ")
                action = "preview"
                if pv_or_pl.lower() == 'place':
                    action = pv_or_pl
                    # ignore.append(holdings_matrix[input_choice])  # ignore this key when displaying table again
                self.preview_equity_order(security_holding = self.security_holdings_obj.holdings[holdings_matrix[input_choice]] )
                break
            inp = input("Do you want to place another order (y or any key to exit): ")
            if inp.lower() == 'y': continue
            else: break

    def list_orders(self, resp_format: str = "json", **kwargs) -> dict:
        """:description: Lists orders for a specific account ID Key
            :param account_id_key: AccountIDKey from :class:`pyetrade.accounts.ETradeAccounts.list_accounts`
            :type  account_id_key: str, required
            :param resp_format: Desired Response format, defaults to xml
            :type  resp_format: str, optional
            :param kwargs: Parameters for api. Refer to EtradeRef for options
            :type  kwargs: ``**kwargs``, optional
            :return: List of orders for an account
            :rtype: ``xml`` or ``json`` based on ``resp_format``
            :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
            :return: List of orders in an account
        """

        api_url = f'{self.base_url}/{self.account_id_key}/orders'

        if resp_format == "json":
            api_url += ".json"

        # Build Params
        params = kwargs
        LOGGER.debug("query string params: %s", params)

        LOGGER.debug(api_url)
        req = self.session.get(api_url, params=params, timeout=self.timeout)

        return get_request_result(req, {}, resp_format)

    def find_option_orders(self, symbol: str, call_put: str,
                           expiry_date: datetime, strike_price: float) -> list:
        """:description: Lists option orders for a specific account ID Key
            :param account_id_key: AccountIDKey from :class:`pyetrade.accounts.ETradeAccounts.list_accounts`
            :type  account_id_key: str, required
            :param symbol: ticker symbol for options chain
            :type  symbol: str, required
            :param call_put: whether the option is a call or put
            :type  call_put: str, required
            :param expiry_date: desired expiry of option (ex: 12-05-2021)
            :type  expiry_date: str, required
            :param strike_price: strike price of desired option
            :type  strike_price: str, required
            :return: List of matching option orders in an account
        """

        opt_sym = option_symbol(symbol, call_put, expiry_date, strike_price)
        orders = self.list_orders(self.account_id_key, resp_format="json", status="OPEN")  # this call may return empty

        results = []

        if len(orders) > 0:
            for o in orders["OrdersResponse"]["Order"]:
                product = o["OrderDetail"][0]["Instrument"][0]["Product"]

                if product["securityType"] == "OPTN":
                    symbol = product["productId"]["symbol"]  # e.g. "PLTR--220218P00023000"

                    if symbol == opt_sym:
                        results.append(o)
        return results

    @staticmethod
    def check_order(**kwargs):
        """:description: Check that required params for preview or place order are there and correct
                         (Used internally)
        """
        mandatory = [
            "accountIdKey",
            "symbol",
            "orderAction",
            "clientOrderId",
            "priceType",
            "quantity",
            "orderTerm",
            "marketSession",
        ]

        if "security_holding" in kwargs:
            return

        if not all(param in kwargs for param in mandatory):
            raise OrderException

        if kwargs["priceType"] == "STOP" and "stopPrice" not in kwargs:
            raise OrderException
        if kwargs["priceType"] == "LIMIT" and "limitPrice" not in kwargs:
            raise OrderException
        if (
                kwargs["priceType"] == "STOP_LIMIT"
                and "limitPrice" not in kwargs
                and "stopPrice" not in kwargs
        ):
            raise OrderException

    def parse_options_order(self, security_holding: SecurityHolding):
        sym, m, d, y, p, t = security_holding.sym.split(" ")
        combined = "-".join([m, d, y.strip("'")])
        dto = datetime.strptime(combined, "%b-%d-%y")
        price = p.strip("$")

        order = {"symbol": sym,
                 "security_type": "OPTN",
                 "price_type": "MARKET",
                 "order_term": "GOOD_FOR_DAY",
                 "order_action": "SELL_CLOSE",
                 "expiryDay": dto.day,
                 "expiryMonth": dto.month,
                 "expiryYear": dto.year,
                 "callPut": t,
                 "strikePrice": price,
                 "limit_price": None,
                 "datetime_object": dto,
                 "quantity": security_holding._can_sell(),
                 }
        return order

    def parse_equity_order(self, security_holding: SecurityHolding):
        order = {"symbol": security_holding.sym,
                 "security_type": "EQ",
                 "price_type": "MARKET",
                 "order_term": "GOOD_FOR_DAY",
                 "order_action": "SELL",
                 "limit_price": None,
                 "quantity": security_holding._can_sell(),
                 }
        return order

    def parse_order(self, security_holding: SecurityHolding):
        if CALL in security_holding.sym or PUT in security_holding.sym:
            return self.parse_options_order(security_holding)
        return self.parse_equity_order(security_holding)

    def build_order_payload(self, order_type: str, **kwargs) -> dict:
        """:description: Builds the POST payload of a preview or place order
                         (Used internally)
           :param order_type: PreviewOrderRequest or PlaceOrderRequest
           :type  order_type: str, required
           :securityType: EQ or OPTN
           :orderAction: for OPTN: BUY_OPEN, SELL_CLOSE
           :callPut: CALL or PUT
           :expiryDate: string, e.g. "2022-02-18"
           :return: Builds Order Payload
           :rtype: ``xml`` or ``json`` based on ``resp_format``
           :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
        """
        securityType = kwargs.get("securityType", "EQ")  # EQ by default
        product = {"securityType": securityType, "symbol": kwargs["symbol"]}

        if securityType == "OPTN":
            expiryDate = kwargs.pop("expiryDate")  # dateutil can handle most date formats
            product.update({
                "expiryDay": expiryDate.day,
                "expiryMonth": expiryDate.month,
                "expiryYear": expiryDate.year,
                "callPut": kwargs["callPut"],
                "strikePrice": kwargs["strikePrice"]
            })

        instrument = {
            "Product": product,
            "orderAction": kwargs["orderAction"],
            "quantityType": "QUANTITY",
            "quantity": kwargs["quantity"],
        }

        order = kwargs
        order["Instrument"] = instrument

        def remove_invalid_price_from_kwargs(key: str) -> None:
            if float(kwargs.get(key, 0)) <= 0:
                kwargs.pop(key, 0)

        remove_invalid_price_from_kwargs("stopPrice")
        remove_invalid_price_from_kwargs("limitPrice")

        if "stopPrice" in kwargs:
            stopPrice = float(kwargs["stopPrice"])
            round_down = ("SELL" == kwargs["orderAction"][:4])
            spstr = to_decimal_str(stopPrice, round_down)

            order["stopPrice"] = spstr

        payload = {
            order_type: {
                "orderType": securityType,
                "clientOrderId": kwargs["clientOrderId"],
                "Order": order,
            }
        }

        if "previewId" in kwargs:
            payload[order_type]["PreviewIds"] = {"previewId": kwargs["previewId"]}

        return payload

    # def build_order_payload(self, order_type: str, **kwargs) -> dict:
    #     """:description: Builds the POST payload of a preview or place order
    #                      (Used internally)
    #        :param order_type: PreviewOrderRequest or PlaceOrderRequest
    #        :type  order_type: str, required
    #        :securityType: EQ or OPTN
    #        :orderAction: for OPTN: BUY_OPEN, SELL_CLOSE
    #        :callPut: CALL or PUT
    #        :expiryDate: datetime, e.g. "2022-02-18"
    #        :return: Builds Order Payload
    #        :rtype: ``xml`` or ``json`` based on ``resp_format``
    #        :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
    #     """
    #     security_holding_order = None
    #     product = {}
    #     securityType = ""
    #     try:
    #         holding = kwargs.pop("security_holding")
    #     except:
    #         print("no security holding object present")
    #         holding = False
    #         securityType = kwargs.get("securityType")  # EQ by default
    #         product = {"securityType": securityType, "symbol": kwargs["symbol"]}
    #     else:
    #         security_holding_order = self.parse_order(holding)
    #         product = {"securityType": security_holding_order["security_type"], "symbol": security_holding_order["symbol"]}
    #
    #     if product["securityType"] == "OPTN":
    #         callPut = ""
    #         strikePrice = ""
    #         if not holding:
    #             expiryDate = kwargs.pop("expiryDate")
    #             callPut = kwargs["callPut"]
    #             strikePrice = kwargs["strikePrice"]
    #         else:
    #             expiryDate = security_holding_order["datetime_object"]
    #             strikePrice = security_holding_order["strikePrice"]
    #             callPut = security_holding_order["callPut"]
    #         product.update({
    #             "expiryDay": expiryDate.day,
    #             "expiryMonth": expiryDate.month,
    #             "expiryYear": expiryDate.year,
    #             "callPut": kwargs.get("callPut") if kwargs.get("callPut") else security_holding_order["callPut"],
    #             "strikePrice": kwargs.get("strikePrice") if  kwargs.get("strikePrice") else security_holding_order["strikePrice"]
    #         })
    #     order_action = kwargs.get("orderAction") if kwargs.get("orderAction") else security_holding_order["order_action"]
    #     order_qty = kwargs.get("quantity") if kwargs.get("quantity") else security_holding_order[
    #         "quantity"]
    #
    #     instrument = {
    #         "Product": product,
    #         "orderAction": order_action,
    #         "quantityType": "QUANTITY",
    #         "quantity": order_qty,
    #     }
    #     order = {}
    #     if security_holding_order:
    #         order = {
    #             "accountIdKey": self.account_id_key,
    #             "symbol": security_holding_order["symbol"],
    #             "priceType": security_holding_order["price_type"],
    #             "orderTerm": security_holding_order["order_term"],
    #             "marketSession": "REGULAR"
    #         }
    #     else:
    #         order = kwargs
    #     order["Instrument"] = instrument
    #
    #     def remove_invalid_price_from_kwargs(key: str) -> None:
    #         if float(kwargs.get(key, 0)) <= 0:
    #             kwargs.pop(key, 0)
    #
    #     remove_invalid_price_from_kwargs("stopPrice")
    #     remove_invalid_price_from_kwargs("limitPrice")
    #
    #     if "stopPrice" in kwargs:
    #         stopPrice = float(kwargs["stopPrice"])
    #         round_down = ("SELL" == kwargs["orderAction"][:4])
    #         spstr = to_decimal_str(stopPrice, round_down)
    #
    #         order["stopPrice"] = spstr
    #
    #     payload = {
    #         order_type: {
    #             "orderType": securityType,
    #             "clientOrderId": random.randint(1000000000, 9999999999),
    #             "Order": order,
    #         }
    #     }
    #
    #     if "previewId" in kwargs:
    #         payload[order_type]["PreviewIds"] = {"previewId": kwargs["previewId"]}
    #
    #     f = open("payload_holding.txt", "w")
    #     print(f"Payload\n{payload}", file=f)
    #
    #     return payload

    def perform_request(self, method, api_url: str, payload: Union[dict, str], resp_format: str = "xml") -> dict:
        """:description: POST or PUT request with json or xml used by preview, place and cancel
           :param method: PUT or POST method
           :type method: session, required
           :param resp_format: Desired Response format, defaults to xml
           :type  resp_format: str, required
           :param api_url: API URL
           :type  api_url: str, required
           :param payload: Payload
           :type  payload: json/dict or str xml, required
           :return: Return request
           :rtype: xml or json based on ``resp_format``
           :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
        """

        LOGGER.debug(api_url)
        LOGGER.debug("payload: %s", payload)

        if resp_format == "json":
            req = method(api_url, json=payload, timeout=self.timeout)
        else:
            headers = {"Content-Type": "application/xml"}
            payload = emit_xml(payload)
            LOGGER.debug("xml payload: %s", payload)
            # print("api url:", api_url)
            req = method(api_url, data=payload, headers=headers, timeout=self.timeout)

        return get_request_result(req, {}, resp_format)

    def preview_equity_order(self, **kwargs) -> dict:
        """API is used to submit an order request for preview before placing it
           :param accountIdKey: AccountIDkey retrived from :class:`list_accounts` :type  accountIdKey: str, required
           :param symbol: Market symbol for the security being bought or sold :type  symbol: str, required
           :param orderAction: Action that the broker is requested to perform :type  orderAction: str, required
           :orderAction values:
               * BUY
               * SELL
               * BUY_TO_COVER
               * SELL_SHORT
           :param previewId: Required only if order was previewed.
                             Numeric preview ID from preview.
                             **Note** - Other parameters much match that of preview
           :type  previewId: long, conditional
           :param clientOrderId: Reference number generated by developer.
                                 Used to ensure duplicate order is not submitted.
                                 Value can be of 20 alphanmeric characters or less
                                 Must be uniquewithin this account.
                                 Does not appear in any API responses.
           :type  clientOrderId: str, required
           :param priceType: Type of pricing specified in equity order
           :type  priceType: str, required
           :priceType values:
               * MARKET
               * LIMIT - Requires `limitPrice`
               * STOP - Requires `stopPrice`
               * STOP_LIMIT - Requires `limitPrice`
               * MARKET_ON_CLOSE
           :param limitPrice: Highest to buy or lowest to sell.
                              Required if `priceType` is `STOP` or `STOP_LIMIT`
           :type  limitPrice: double, conditional
           :param stopPrice: Price to buy or sell if specified in a stop order.
                             Required if `priceType` is  `STOP` or `STOP_LIMIT`
           :type  stopPrice: double, conditional
           :param allOrNone: Specifies if order must be executed all at once.
                             TRUE triggers `allOrNone`, defaults to FALSE
           :type  allOrNone: bool, optional
           :param quantity: Number of shares to buy or sell
           :type  quantity: int, required
           :param reserveOrder: If set to TRUE, publicly displays only a limited
                                number of shares (the reserve quantity), instead
                                of the entire order, to avoid influencing other
                                traders. If TRUE, must also specify the
                                `reserveQuantity`, defaults to FALSE
           :type  reserveOrder: bool, optional
           :param reserveQuantity: Number of shares to be publicly displayed if
                                   this is a reserve order. Required if
                                   `reserveOrder` is TRUE.
           :type reserveQuantity: int, conditional
           :param marketSession: Session to place the equity order
           :type  marketSession: str, required
           :marketSession values:
               * REGULAR
               * EXTENDED
           :param orderTerm: Term for which the order is in effect.
           :type  orderTerm: str, required
           :orderTerm values:
               * GOOD_UNTIL_CANCEL
               * GOOD_FOR_DAY
               * IMMEDIATE_OR_CANCEL (only for `LIMIT` orders)
               * FILL_OR_KILL (only for `LIMIT` orders)
           :param routingDestination: Exchange where the order should be executed.
           :type  routingDestination: str, optional
           :routingDestination values:
               * AUTO (default)
               * ARCA
               * NSDQ
               * NYSE
           :param estimatedCommission: Cost billed to the user to preform requested action
           :type  estimatedCommission: double
           :param estimatedTotalAmount: Cost including commission
           :type  estimatedTotalAmount: double
           :param messageList: Container for messages describing the result of the action
           :type  messageList: dict
           :param msgDesc: Text of the result message, indicating order status, success
                           or failure, additional requirements that must be met before
                           placing the order, etc. Applications typically display this
                           message to the user, which may result in further user action
           :type  msgDesc: str
           :param msgCode: Standard numeric code of the result message. Refer to
                           the Error Messages documentation for examples. May optionally
                           be displayed to the user, but is primarily intended for
                           internal use.
           :type  msgCode: int
           :param orderNum: Numeric ID for this order in the E*TRADE system
           :type  orderNum: int
           :param orderTime: The epoch time the order was submitted.
           :type  orderTime: long
           :param symbolDesc: Text description of the security
           :type  symbolDesc: str
           :param symbol: The market symbol for the underlier
           :type  symbol: str
           :return: Confirmation of the Preview Equity Order
           :rtype: ``xml`` or ``json`` based on ``resp_format``
           :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
        """
        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        api_url = f'{self.base_url}/{self.account_id_key}/orders/preview'

        # payload creation
        print("kwargs", kwargs)
        payload = self.build_order_payload("PreviewOrderRequest", **kwargs)

        return self.perform_request(self.session.post, api_url, payload, "xml")

    def change_preview_equity_order(self, account_id_key: str, order_id: str, **kwargs):
        """:description: Same as :class:`preview_equity_order` with orderId
           :param order_id: order_id to modify, refer :class:`list_orders`
           :type  order_id: str, required
           :param account_id_key: account_id_key retrieved from :class:`list_accounts`
           :type  account_id_key: str, required
           :return: Previews Changed order with orderId for account with account_id_key
           :rtype: dict/json
           :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
        """

        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        api_url = f'{self.base_url}/{self.account_id_key}/orders/{order_id}/change/preview'

        # payload creation
        payload = self.build_order_payload("PreviewOrderRequest", **kwargs)

        return self.perform_request(self.session.put, api_url, payload, "xml")

    def place_option_order(self, **kwargs) -> dict:
        """:description: Places Option Order, only single leg CALL or PUT is supported for now
           :return: Returns confirmation of the equity order
        """
        kwargs["securityType"] = "OPTN"

        return self.place_equity_order(**kwargs)

    def place_equity_order(self, **kwargs) -> dict:
        """:description: Places Equity Order
           :param kwargs: Parameters for api, refer :class:`preview_equity_order`
           :type  kwargs: ``**kwargs``, required
           :return: Returns confirmation of the equity order
           :rtype: xml or json based on ``resp_format``
           :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
        """

        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        if "previewId" not in kwargs:
            LOGGER.debug(
                "No previewId given, previewing before placing order "
                "because of an Etrade bug as of 1/1/2019"
            )
            preview = self.preview_equity_order(**kwargs)
            print("this is preview:", preview
                  )
            kwargs["previewId"] = preview["PreviewOrderResponse"]["PreviewIds"]["previewId"]

            LOGGER.debug("Got a successful preview with previewId: %s", kwargs["previewId"])
            print("Got a successful preview with previewId: %s", kwargs["previewId"])

        api_url = f'{self.base_url}/{self.account_id_key}/orders/place'

        # payload creation
        payload = self.build_order_payload("PlaceOrderRequest", **kwargs)

        return self.perform_request(self.session.post, api_url, payload, "xml")

    def place_changed_option_order(self, **kwargs) -> dict:
        """:description: Places Option Order, only single leg CALL or PUT is supported for now
           :return: Returns confirmation of the equity order
        """
        kwargs["securityType"] = "OPTN"

        return self.place_changed_equity_order(**kwargs)

    def place_changed_equity_order(self, **kwargs) -> dict:
        """:description: Places changes to equity orders
            NOTE: the ETrade server will actually cancel the old orderId, and create a new orderId
           :param kwargs: Parameters for api, refer :class:`change_preview_equity_order`
           :type  kwargs: ``**kwargs``, required
           :return: Returns confirmation similar to :class:`preview_equity_order`
           :rtype: xml or json based on ``resp_format``
           :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
        """

        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        if "previewId" not in kwargs:
            LOGGER.debug(
                "No previewId given, previewing before placing order "
                "because of an Etrade bug as of 1/1/2019"
            )
            preview = self.preview_equity_order(**kwargs)

            if "Error" in preview:
                LOGGER.error(preview)
                raise Exception("Please check your order!")

            kwargs["previewId"] = preview["PreviewOrderResponse"]["PreviewIds"]["previewId"]
            LOGGER.debug("Got a successful preview with previewId: %s", kwargs["previewId"])

        api_url = f'{self.base_url}/{self.account_id_key}/orders/{kwargs["orderId"]}/change/place'

        # payload creation
        payload = self.build_order_payload("PlaceOrderRequest", **kwargs)

        return self.perform_request(self.session.put, api_url, payload, "xml")

    def cancel_order(self, order_num: int, resp_format: str = "xml") -> dict:
        """:description: Cancels a specific order for a given account
           :param account_id_key: AccountIDkey retrived from
                              :class:`pyetrade.accounts.ETradeAccounts.list_accounts`
           :type  account_id_key: str, required
           :param order_num: Numeric id for this order listed in :class:`list_orders`
           :type  order_num: int, required
           :param resp_format: Desired Response format, defaults to xml
           :type  resp_format: str, required
           :return: Confirmation of cancellation
           :rtype: ``dict/json``
           :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
        """

        api_url = f'{self.base_url}/{self.account_id_key}/orders/cancel'
        payload = {"CancelOrderRequest": {"orderId": order_num}}

        return self.perform_request(self.session.put, api_url, payload, resp_format)