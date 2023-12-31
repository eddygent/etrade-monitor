from yahoofinancials import YahooFinancials
tickers = ['AAPL', 'GOOG', 'C']
yahoo_financials = YahooFinancials(tickers, concurrent=True, max_workers=8, country="US")
balance_sheet_data_qt = yahoo_financials.get_financial_stmts('quarterly', 'balance')
print(balance_sheet_data_qt)
