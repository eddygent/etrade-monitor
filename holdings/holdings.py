###################### Created Classes #######################
import sys
import etrade_config
# loading configuration file
sys.path.append(f"{etrade_config.base_dir}/positions")
from positions import Position
sys.path.append(f"{etrade_config.base_dir}/transactions")
from transactions import Transaction, BANNED_TRANSACTION_TYPE
import pandas as pd
#################### End Created Classes #####################

def red_text(text):
    return f'<mark style="color:red;">{text}</mark>'

def green_text(text):
    return f'<mark style="color:green;">{text}</mark>'
from pretty_html_table import build_table

import babel.numbers
import decimal

def format_currency(currency):
    return babel.numbers.format_currency(decimal.Decimal(currency), "USD")

class SecurityHolding:
    def __init__(self):
        self.can_sell_qty = 0
        self.px = 0
        self.last_px = 0
        self.sym = ""
        self.total_gain = 0
        self.pct_portfolio = 0
        self.market_value = 0
        self.associated_transactions = []
        self.associated_positions = []

    def percent_gain(self):
        return (self.market_value/(self.market_value-self.total_gain))-1

    def _balance_qty(self):
        self.can_sell_qty -= self.hold_qty()

    def qty(self) -> int:
        if len(self.hold_matrix()) == 0:
            return self._can_sell()
        total_hold_qty = 0
        for qty, _, _, _ in self.hold_matrix():
            total_hold_qty += qty
        return total_hold_qty + self.can_sell_qty

    def __repr__(self) -> str:
        ret_str = f'Sym: {self.sym}; Qty: {self.qty()}; Price: {format_currency(self.px)}; TotalGain: {format_currency(self.total_gain)}; MarketValue: {format_currency(self.market_value)}'
        return ret_str

    def hold_matrix(self):
        _hold_matrix = []
        if len(self.associated_transactions) != 0:
            for tx in self.associated_transactions:
                if not tx.can_sell():
                    _hold_matrix.append((tx.qty, tx.date, tx.can_sell_date(), tx.can_sell_days()))
        return _hold_matrix

    def _can_sell(self):
        self.can_sell_qty = 0
        for pos in self.associated_positions:
            self.can_sell_qty += pos.qty
        if len(self.associated_transactions) != 0:
            for hold, _, _, _ in self.hold_matrix():
                self.can_sell_qty -= hold
        return self.can_sell_qty

    def str_can_sell_matrix(self, line_break: str = "\n"):
        if self._can_sell():
            return f"Qty: {self._can_sell()}{line_break}", self.total_gain * abs(1- self.ratio())
        return None

    def str_hold_matrix(self, split: str = ";", line_break: str = "\n"):
        ret_str = ""
        for qty, purchase_date, sell_date, sell_days in self.hold_matrix():
            ret_str += f"Qty: {qty}{split} Purchase Date: {purchase_date}{split} Sell Date: {sell_date.strftime('%m-%d-%Y')}{split} Sell In: {sell_days.days} days{line_break}"
        if ret_str:
            if qty:
                return ret_str, self.total_gain * self.ratio(), self._can_sell(), self.hold_qty()
        return None

    def can_sell_info(self):
        ret_str = ""
        for qty, purchase_date, sell_date, sell_days in self.hold_matrix():
            if qty:
                return self.total_gain * self.ratio(), self._can_sell(), sell_date.strftime('%m-%d-%Y'), sell_days.days

    def hold_qty(self) -> int:
        total_qty = 0
        for tx_qty, _, _, _ in self.hold_matrix():
            total_qty += tx_qty
        return total_qty

    def ratio(self):
        hold = self.hold_qty()
        sell = self._can_sell()
        ratio = 1
        try:
            ratio = hold/(sell + hold)
        except ZeroDivisionError:
            ratio = 1
        # print(f"Symbol: {self.sym}; Ratio: {ratio}; Hold: {hold};  Sell: {sell}")
        return ratio

class SecurityHoldings:
    def __init__(self):
        self.holdings = {}

    def add_position(self, position: Position) -> bool:
        try:
            self.holdings[position.sym]
        except Exception as e:
            # print("Position Does Not Exist. Creating...", e)
            self.holdings[position.sym] = SecurityHolding()
            self.holdings[position.sym].sym = position.sym

        finally:
            holdingsItem = self.holdings[position.sym]
            holdingsItem.associated_positions.append(position)
            holdingsItem.can_sell_qty = position.qty
            holdingsItem.px = position.px_paid
            holdingsItem.last_px = position.last_trade
            holdingsItem.total_gain = position.total_gain
            holdingsItem.market_value = position.market_value
            holdingsItem.pct_portfolio = position.pct_portfolio
        return True

    def add_transaction(self, transaction: Transaction) -> bool:
        try:
            self.holdings[transaction.dsym]
        except Exception as e:
            # print("Holding Does Not Exist. Not adding Transaction", e)
            # print("Skipping Transaction:", transaction)
            return False
        else:
            holdingsItem = self.holdings[transaction.dsym]
            self.holdings[transaction.dsym]._balance_qty()
            holdingsItem.associated_transactions.append(transaction)
        return True

    def str_must_hold(self, toggle_html = False):
        s = ""
        line_break = ""
        for holding in self.holdings.values():
            # Toggle HTML Formatting
            if toggle_html:
                line_break = "<br>"
                response = holding.str_hold_matrix(line_break=line_break)
            else:
                line_break = "\n"
                response = holding.str_hold_matrix()

            if response:
                hold_str, gain, can_sell, hold = response
                add_holding_response = f"{holding.sym} - Total Gain: {format_currency(gain)} | Can Sell: {can_sell} | Must Hold: {hold}{line_break}{hold_str}"
                if toggle_html:
                    if gain < 0: add_holding_response = red_text(add_holding_response)
                    else: add_holding_response = green_text(add_holding_response)
                s += add_holding_response + line_break
        return s

    def str_must_hold_html(self):
        s = ""
        line_break = ""
        toggle_html = True
        for holding in self.holdings.values():
            # Toggle HTML Formatting
            if toggle_html:
                line_break = "<br>"
                response = holding.str_hold_matrix(line_break=line_break)
            else:
                line_break = "\n"
                response = holding.str_hold_matrix()

            if response:
                hold_str, gain, can_sell, hold = response
                add_holding_response = f"{holding.sym} - Total Gain: {format_currency(gain)} | Can Sell: {can_sell} | Must Hold: {hold}{line_break}{hold_str}"
                if toggle_html:
                    if gain < 0: add_holding_response = red_text(add_holding_response)
                    else: add_holding_response = green_text(add_holding_response)
                s += add_holding_response + line_break
        return s

    def str_can_sell(self, toggle_html=False):
        s = ""
        line_break = ""
        for holding in self.holdings.values():
            if toggle_html:
                line_break = "<br>"
                response = holding.str_can_sell_matrix(line_break = line_break)
            else:
                holding.str_can_sell_matrix()
            if response:
                sell_str, gain = response
                if gain > 0:
                    s += green_text(f"{holding.sym} - Total Gain: {format_currency(gain)} | {sell_str}{line_break}")
                else:
                    s += red_text(f"{holding.sym} - Total Gain: {format_currency(gain)} | {sell_str}{line_break}")

        return s

    def _can_sell(self):
        can_sell = []
        for holding in self.holdings.values():
            if holding._can_sell():
                can_sell.append((holding.sym, holding._can_sell()))
        return can_sell

    def __repr__(self):
        return str(self.holdings)

    def to_json(self):
        pass

    def to_dataframe(self):
        sym = []
        price = []
        total_gain = []
        total_gain_secret = []
        must_hold = []
        perc_portfolio = []
        perc_gain = []
        can_sell = []
        can_sell_date = []
        for holding in self.holdings.values():
            sym.append(holding.sym)
            price.append(format_currency(holding.last_px))
            total_gain.append(format_currency(holding.total_gain))
            must_hold.append(holding.hold_qty())
            perc_portfolio.append(holding.pct_portfolio)
            perc_gain.append(holding.percent_gain()*100)
            can_sell.append(holding._can_sell())
            total_gain_secret.append(holding.total_gain)
            try:
                _,_,date,days = holding.can_sell_info()
            except Exception as e:
                can_sell_date.append("N/A")
            else:
                can_sell_date.append(date)
        to_df = {"SYMBOL": sym, "PRICE": price, "TOTAL GAIN": total_gain, "% GAIN": perc_gain, "MUST HOLD": must_hold,
                  "CAN SELL": can_sell, "CAN SELL DATE": can_sell_date, "GAIN RANKING": total_gain_secret, "% PORTFOLIO": perc_portfolio}
        df = pd.DataFrame(to_df)
        df = df.sort_values(by=['GAIN RANKING'])
        df = df.reset_index(drop=True)
        return df

    def hold_dataframe(self, html=False):
        df = self.to_dataframe()
        df = df.loc[df['CAN SELL DATE'] != 'N/A']
        if not html:
            return df
        df = df.drop(columns=["GAIN RANKING"])
        df = df.reset_index(drop=True)
        return build_table(df, 'grey_light')

    def can_sell_winners_dataframe(self, html=False):
        df = self.to_dataframe()
        df = df.loc[df['CAN SELL DATE'] == 'N/A']
        df = df.loc[df['GAIN RANKING'] >= 0]
        if not html:
            return df
        df = df.drop(columns=["GAIN RANKING"])
        df = df.reset_index(drop=True)
        return build_table(df, 'green_light')

    def can_sell_losers_dataframe(self, html=False):
        df = self.to_dataframe()
        df = df.loc[df['CAN SELL DATE'] == 'N/A']
        df = df.loc[df['GAIN RANKING'] <= 0]
        if not html:
            return df
        df = df.drop(columns=["GAIN RANKING"])
        df = df.reset_index(drop=True)
        return build_table(df, 'red_light')
