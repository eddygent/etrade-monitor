# Applications
Haphazardly put together "applications" that I use for different reasons. I have no idea what I'm doing :D!
## Table of Contents

* [Done](#done)
* [ToDo](#todo)
* [In Progress](#in-progress)

## Done
- [Sentiment Analysis using NLP](#sentiment-analysis)
- [Options Volatility Screener/Volatility Screener to find Outliers](#options-volatility-screener)
- [Generation of Neutral Strategies using Short Strangles](./volatility_strategies.py)
- [Black Scholes Pricer for Options](./black_scholes_model.py) 

## ToDo
- Fair Pricer for Stocks (High, Unknown Difficulty)
- Regression Analysis on Financial Statements against Expected Growth/Subtraction due to earnings (Medium, 13 Difficulty) - RG
- Volatility of Stock Since its purchase (Medium, 3 Difficulty) - MT
- Mispriced Option (overpriced, underpriced, how to correct) (Medium, 1 Difficulty) - MT
- Delta Calculation (High, 3 Difficulty)
- Hedge Ratio (Medium, 1 Difficulty) **_Contingent on Delta Calculation_**

## In Progress
- Documenting Forecasted Trades in a Journal [firebase] (Medium, 3 Difficulty)

## Sentiment Analysis
**Relevant File(s):** `sentiment_analysis.py`

**Relevant Function(s):** `generate_sentiment_summary_matrix(df, focus, 
analyze_sentiment=True, analyze_summary=True)`, `scrape_articles_determine_sentiment_and_send_email(ticker)`

**Description:** Done using OpenAI API. Generate a matrix of 
sentiment analysis and summary for a given stock when passed a DataFrame of Articles.
*For more information:* https://medium.com/data-and-beyond/sentiment-analysis-with-chatgpt-openai-and-python-use-chatgpt-to-build-a-sentiment-analysis-ai-2b89158a37f6

![emon sentiment analysis](../img/sentiment-analysis-snippet.png?raw=true "Title")

**Note:** I'm not made of money, and for this reason, I do not plug sentiment analysis into the options volatility screener. I only use if I want to get
the sentiment around a particular stock. 

**More on Sentiment Analysis:** I'm really trying here as you can probably tell... but I did one more thing to *hopefully* make your
life easier (if anyone at all is ever going to use this), run

[`python3 dev_etrade_python_client.py -sa`](../dev_etrade_python_client.py)

It will look something like this:
![emon sentiment analysis email](../img/sentiment-analysis-email.png?raw=true "Title")

## Options Volatility Screener
**Relevant File(s):** `volatility.py`,`volatility_strategies.py`,`yop.py`

**Relevant Function(s):** 

**Description:** The options volatility screener will scan all US Symbols (`../data/us_symbols.csv`) and genererate a matrix 
that contains the:`ticker,lastPrice,volatility,prevDayVolatility,percentMove,avgVolume`. 
This data will be saved under `../data/voldata`. 

The data will be used find large moves in volatility above a certain volume threshold (filter out penny-stocks).
From here, options positions will be generated that assume the stock will somewhat revert back
to its average price, and volatility range prior to the large move in the stock. 

*For example, if the average volatility over the last 3 months for a stock was 10%. Suddenly,
there is a +20% move in one day, this is somewhat out of the ordinary.*

**prevDayVolatility = .10**, **volatility = .25** and the **percentMove = .20**. 

*We want to open up a position under
the assumption that the stock will revert at least the difference between the volatility and prevDayVolatility*
- **( abs(.25 [volatility] - .10 [prevDayVolatility])(.20 [percentMove] )(-1 [factor])**) is the `targetPrice`
- Open up a conservative bearish position by scanning the options chain. 
- Determine whether to short on long based on volume (for higher volume short *implying it's better to hold stocks with large volume* and long *implying it's better to **not** own stocks with lower volume*).

Running the following in Command Line will send you an email with statistics on volatility within the market for the current
business day and pull together the largest moves in volatility, along with potentially profitable options positions.

[`python3 dev_etrade_python_client.py -vo`](../dev_etrade_python_client.py)

It will look something like this: 
![emon etrade volatility screener](../img/volatility-screener-email.png?raw=true "Title")