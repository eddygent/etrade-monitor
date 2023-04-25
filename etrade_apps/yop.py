import yoptions as yo

# Chain of all FORD MOTOR COMPANY call options for next expiration date
chain = yo.get_chain_greeks(stock_ticker='TSLA', dividend_yield=0, option_type='c', risk_free_rate=None)
ideal = chain[chain['Delta'].between(.2, .3)]
# print(chain.head().to_string())

print(ideal)