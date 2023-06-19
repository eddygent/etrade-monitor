from volatility import black_scholes_ticker_symbol
from yop import get_friday_option_for_ticker_date_closest_to_price

ticker = 'T'
targetPrice = 16.37
option_chain = get_friday_option_for_ticker_date_closest_to_price(ticker=ticker, price=targetPrice, call_or_put='p',
                                                                  days=30, long=True)
print(black_scholes_ticker_symbol(ticker, option_chain, targetPrice))