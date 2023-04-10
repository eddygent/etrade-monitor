
from datetime import datetime,timedelta

BANNED_TRANSACTION_TYPE = ['Deposit', 'Sold']
HOLDING_PERIOD = 31

class Transaction:
    def __init__(self, displaySymbol, symbol, timestamp, amount, desc, txType, qty, price, securityType, json):
        self.sym = symbol
        self.dsym = displaySymbol
        self.timestamp = datetime.utcfromtimestamp(timestamp/1000)
        self.date = self.timestamp.strftime('%m-%d-%Y')
        self.amt = amount
        self.desc = desc
        self.qty = qty
        self.px = price
        self.secType = securityType
        self.json = json
        self.txType = txType

    def __repr__(self) -> str:
        ret_str = f'Symbol: {self.dsym}; {self.date}; Amount: {self.amt}; Qty: {self.qty}; Px: {self.px}; Type: {self.secType}'
        return str(ret_str)
    
    def __str__(self) -> str:
        ret_str = f'Symbol: {self.dsym}; {self.date}; Amount: {self.amt}; Qty: {self.qty}; Px: {self.px}; Type: {self.secType}'
        return ret_str
    
    def can_sell(self):
        threshold = datetime.today() - timedelta(days = HOLDING_PERIOD)
        return threshold >= self.timestamp
    
    def can_sell_date(self):
        if self.can_sell():
            return datetime.today()
        return self.timestamp + timedelta(days = HOLDING_PERIOD)
    
    def can_sell_days(self):
        if self.can_sell():
            return 0
        return (self.timestamp + timedelta(days = HOLDING_PERIOD)) - datetime.today()

def TransactionParser(transactionListResponse):
    transactionDict = transactionListResponse['TransactionListResponse']['Transaction']
    ls = []
    for tx in transactionDict:
        if tx['transactionType'] not in BANNED_TRANSACTION_TYPE:          
            try:
                ls.append(
                    Transaction(
                        displaySymbol=tx['brokerage']['displaySymbol'],
                        symbol=tx['brokerage']['product']['symbol'],
                        timestamp=tx['transactionDate'],
                        amount=tx['amount'],
                        desc=tx['description'],
                        qty=tx['brokerage']['quantity'],
                        price=tx['brokerage']['price'],
                        securityType=tx['brokerage']['product']['securityType'],
                        txType=tx['transactionType'],
                        json=tx)
                )
            except Exception as e:
                print("==========================")
                print("Error:",e)
                print("Error Adding Transaction")
                print(tx['description'])
                print("==========================")
    return ls