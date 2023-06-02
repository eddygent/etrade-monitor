# Applications

## Table of Contents

* [Done](#done)
* [ToDo](#todo)
* [In Progress](#in-progress)

## Done
- [Sentiment Analysis using NLP](#sentiment-analysis)
- [Options Volatility Screener/Volatility Screener for the exchange to find Outliers](#options-volatility-screener)
- Generation of Neutral Strategies using Short Strangles

## ToDo
- Fair Pricer for Stocks and Options (High, x Difficulty Unknown)
- Grab the top 10 articles on a stock and put into DataFrame (High, 3)
- Regression Analysis on Financial Statements against Expected Growth/Subtraction due to earnings (Medium, 13 Difficulty)
- Volatility of Stock Since its purchase (Medium, 3 Difficulty)

## In Progress
- Documenting Forecasted Trades in a Journal [firebase] (Medium, 3 Difficulty)

## Sentiment Analysis
**Relevant File(s):** `sentiment_analysis.py`

**Relevant Function(s):** `generate_sentiment_summary_matrix(df, focus, 
analyze_sentiment=True, analyze_summary=True)` 

**Description:** Done using OpenAI API. Generate a matrix of 
sentiment analysis and summary for a given stock when passed a DataFrame of Articles.
*For more information:* https://medium.com/data-and-beyond/sentiment-analysis-with-chatgpt-openai-and-python-use-chatgpt-to-build-a-sentiment-analysis-ai-2b89158a37f6

## Options Volatility Screener
**Relevant File(s):** `volatility.py`,`volatility_strategies.py`

**Relevant Function(s):** `generate_sentiment_summary_matrix(df, focus, 
analyze_sentiment=True, analyze_summary=True)` 

**Description:** The options volatility screener will scan all of the US Symbols (`../data/us_symbols.csv`) and genererate a matrix 
that contains the:`ticker,lastPrice,volatility,prevDayVolatility,percentMove,avgVolume`. 
This data will be saved under `../data/voldata`. 

The data will be used find large moves in volatility above a certain volume threshold (filter out penny-stocks).
From here, options positions will be generated that assume the stock will somewhat revert back
to its average price, and volatility range prior to the large move in the stock. 

*For example, if the average volatility over the last 3 months for a stock was 10%. All of the sudden
there is a +20% move in one day, this is somewhat out of the ordinary.*

**prevDayVolatility = .10**, **volatility = .25** and the **percentMove = .20**. 

*We want to open up a position under
the assumption that the stock will revert at least the difference between the volatility and prevDayVolatility*
- **( abs(.25 [volatility] - .10 [prevDayVolatility])(.20 [percentMove] )(-1 [factor])**) is the `targetPrice`
- Open up a conservative bearish position by scanning the options chain. 
- Determine whether to short on long based on volume (for higher volume short *implying it's better to hold stocks with large volume* and long *implying it's better to **not** own stocks with lower volume*).