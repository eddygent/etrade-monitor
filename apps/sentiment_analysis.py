#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 02/06/2023
# Email       : kori.s.vernon@gmail.com
# ----------------------------------------------------------------------------

'''
Snippet taken from article: https://medium.com/python-programming-ascendance/using-chatgpt-and-python-for-sentiment-analysis-72735072500e#:~:text=Using%20ChatGPT%20and%20Python%20for%20sentiment%20analysis%20is%20an%20easy,and%20unleash%20its%20full%20potential.
'''
import os
import sys
import pandas as pd
import openai
from tqdm import tqdm
import time
import operator
import yfinance as yf
from pretty_html_table import build_table

from volatility import TODAY

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + "/../")

from email_summary import send_email_with_data
import etrade_config

from scrape_articles import _topics_query_,discover_articles

from transformers import GPT2Tokenizer, GPT2ForSequenceClassification

def predict_sentiment(text):
    # Load the pre-trained model
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2ForSequenceClassification.from_pretrained("gpt2")
    # Encode the text
    encoded_text = tokenizer.encode(text, return_tensors="pt")
    # Predict the sentiment
    sentiment = model(encoded_text)[0]
    # Decode the sentiment
    return sentiment.argmax().item()

# SimpleSentimentAnalysis
def SimpleSentimentAnalysis(text):
    # Test the model
    sentiment = predict_sentiment(text)
    return sentiment # 1 for positive, 0 for negative

# Advanced Sentiment Analysis: https://medium.com/data-and-beyond/sentiment-analysis-with-chatgpt-openai-and-python-use-chatgpt-to-build-a-sentiment-analysis-ai-2b89158a37f6

# Enter your OpenAI API private access key here. IMPORTANT - don't share your code online if it contains your access key or anyone will be able to access your openai account
openai.api_key = etrade_config.OPENAIKEY

# Use this code block if you ONLY want to know the sentiment for each review. This code will NOT try to summarize each review.

# Create a custom function that will call the openAI API and send your reviews data to it one review at a time
# We will use the tqdm library to create a progress tracker so we can see if there are any problems with the openAI API processing our requests
def analyze_my_article(article,title, focus):
    retries = 2
    sentiment = None

    while retries > 0:
        messages = [
            {"role": "system",
             "content": f"You are an AI language model trained to analyze and detect the sentiment of financial articles towards {focus}."},
            {"role": "user",
             "content": f"Analyze the following statements about {focus} and determine if the sentiment is: positive, negative, neutral, or have nothing to do with the {focus}. Return only a single word, either POSITIVE if positive sentiment, NEGATIVE if negative sentiment, NEUTRAL if neutral sentiment, or IRRELEVANT if the article has nothing to do with the {focus}. Analyze the following articles: {article}"}
        ]

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            # We only want a single word sentiment determination so we limit the results to 3 openAI tokens, which is about 1 word.
            # If you set a higher max_tokens amount, openAI will generate a bunch of additional text for each response, which is not what we want it to do
            max_tokens=3,
            n=1,
            stop=None,
            temperature=0
        )

        response_text = completion.choices[0].message.content
        # print the sentiment for each customer review, not necessary but it's nice to see the API doing something :)
        print(response_text)

        # Sometimes, the API will be overwhelmed or just buggy so we need to check if the response from the API was an error message or one of our allowed sentiment classifications.
        # If the API returns something other than POSITIVE, NEGATIVE or NEUTRAL, we will retry that particular review that had a problem up to 3 times. This is usually enough.
        if response_text in ["POSITIVE", "NEGATIVE", "NEUTRAL","IRRELEVANT"]:
            sentiment = response_text
            break
        else:
            article = title
            retries -=1
            time.sleep(4)
    else:
        sentiment = "IRRELEVANT"
    retries = 1

    # OpenAI will limit the number of times you can access their API if you have a free account.
    # If you are using the openAI free tier, you need to add a delay of a few seconds (i.e. 4 seconds) between API requests to avoid hitting the openai free tier API call rate limit.
    # This code will still work with an openAI free tier account but you should limit the number of reviews you want to analyze (<100 at a time) to avoid running into random API problems.
    time.sleep(4)
    return sentiment

# Use this code block if you ONLY want to summarize long reviews into short, 75 word versions. This code will NOT try to classify the sentiment of each review
def summarize_my_article(article,title, focus):
    retries = 2
    summary = None

    while retries > 0:
        # This time, we are only summarizing the reviews, not determining the sentiment so we change the prompt (ie command) for chatGPT to the following
        messages = [
            {"role": "system",
             "content": f"You are an AI language model trained to analyze and summarize financial articles about {focus}."},
            {"role": "user", "content": f"Summarize the following article, highlighting pros and cons for {focus}: {article}"}
        ]

        completion2 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            # We want to limit the summarizes to about 75 words (which is around 100 openAI tokens). If you want longer review summaries, increase the max_tokens amount
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.8
        )

        response_text = completion2.choices[0].message.content
        # This is optional but it's nice to see how the reviews are being summarized to make sure something isn't wrong with the input file or API results
        print(response_text)

        # This is our quality control check. If the API has an error and doesn't generate a summary, we will retry the review 3 times.
        if response_text:
            summary = response_text
            break
        else:
            article = title
            retries -= 1
            time.sleep(4)
    else:
        summary = "Summary not available."

    # OpenAI will limit the number of times you can access their API if you have a free account.
    # If you are using the openAI free tier, you need to add a delay of a few seconds (i.e. 4 seconds) between API requests to avoid hitting the openai free tier API call rate limit.
    # This code will still work with an openAI free tier account but you should limit the number of reviews you want to analyze (<100 at a time) to avoid running into random API problems.

    time.sleep(4)
    return summary

def generate_sentiment_summary_matrix(df, focus, analyze_sentiment=True, analyze_summary=True):
    # Analyze each review using ChatGPT and save the results in a list called sentiments so we can access the results later
    sentiments = []
    summaries = []

    # Here we loop through all of the reviews in our dataset and send them to the openAI API using our custom function from above
    if analyze_sentiment:
        for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing article sentiment"):
            article = row["Article"]
            title = row['title']
            sentiment = analyze_my_article(article=article,title=title, focus=focus)
            sentiments.append(sentiment)
        # Now let's save the openAI API results as an additional column in our original dataset
        df["sentiment"] = sentiments

    if analyze_summary:
        for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing article summary"):
            article = row["Article"]
            title = row['title']
            summary = summarize_my_article(article=article, title=title, focus=focus)
            summaries.append(summary)
        df['summary'] = summaries
    return df

def sentiment_bias(sentiment_dict):
    '''
    Helper function to get the sentiment from the perigon sentiment analysis dict.
    '''
    return max(sentiment_dict.items(), key=operator.itemgetter(1))[0]


def json_article_iterator(json):
    df = pd.DataFrame(columns=['title', 'pubDate', 'url', 'perigon_sentiment', 'Article'])
    for i, meta in enumerate(json['articles']):
        article_df = {}
        article_df['title'] = meta["title"]
        article_df['pubDate'] = meta['pubDate'][:10]
        article_df['url'] = meta['url']
        # article_df['perigon_sentiment'] = sentiment_bias(meta["sentiment"])
        article_df['Article'] = meta['content']
        # sentiment_dict = meta["sentiment"]
        new_row = pd.DataFrame(article_df, index=[i])

        df = pd.concat([df, new_row], ignore_index=True)
    return df

def _overall_sentiment(df, normalize=True):
    overall_sentiments = df['sentiment'].value_counts(normalize=normalize)
    pos = overall_sentiments.get(key='POSITIVE') if overall_sentiments.get(key='POSITIVE') else 0
    neg = overall_sentiments.get(key='NEGATIVE') if overall_sentiments.get(key='NEGATIVE') else 0
    neu = overall_sentiments.get(key='NEUTRAL') if overall_sentiments.get(key='NEUTRAL') else 0
    return {"POSITIVE":pos,"NEGATIVE":neg,"NEUTRAL":neu}

def give_direction(overall_sentiment_dict):
    pos = overall_sentiment_dict['POSITIVE']
    neg = overall_sentiment_dict['NEGATIVE']
    neu = overall_sentiment_dict['NEUTRAL']
    if pos == neg: return 0
    if pos > neg and neu > neg: return 1
    if neg > pos and neu > pos: return -1
    if neu > pos and neu > neg: return 0
    if pos > neg: return 1
    if neg > pos: return -1
def scrape_articles_and_perform_analysis(ticker):
    y = yf.Ticker(ticker)
    yinfo = y.info
    shortname = yinfo['shortName']
    longname = yinfo['longName']
    search_for = [ticker, shortname, longname]
    query = _topics_query_(search_for)
    json = discover_articles(query)
    df = json_article_iterator(json)
    result = generate_sentiment_summary_matrix(df,focus=ticker, analyze_summary=False)
    overall_sentiment = _overall_sentiment(result, normalize=True)
    direction = give_direction(overall_sentiment)
    result = result[['title', 'sentiment', 'pubDate', 'url']]
    return result, overall_sentiment, direction

def scrape_articles_determine_sentiment_and_send_email(ticker):
    df, overall_sentiment, direction = scrape_articles_and_perform_analysis(ticker)
    if direction == 1:
        color = 'green_light'
        sentiment = "POSITIVE"
    if direction == 0:
        color = 'grey_light'
        sentiment = "NEUTRAL"
    if direction == -1:
        color = 'red_light'
        sentiment = "NEGATIVE"
    html_df = build_table(df, color)

    matrix_df = pd.DataFrame(overall_sentiment, index=[0])
    matrix_df = matrix_df.reset_index(drop=True)
    matrix = build_table(matrix_df, color)

    s = f"<h1>EMon: Sentiment Analysis Results for {ticker} - {TODAY} - {sentiment}</h1>"
    s+= f"YahooFinance Link: https://finance.yahoo.com/quote/{ticker}"
    s += "<br>Overall Sentiment Matrix:" + matrix
    s += html_df

    send_email_with_data(s,subject=f"EMon: Sentiment Analysis results for {ticker} - {TODAY} - {sentiment}" )

# def main():
#     input_file = "reviews.csv"
#     # Read the input file into a dataframe
#     df = pd.read_csv(input_file)
#     focus = "AAPL"
#     result = generate_sentiment_summary_matrix(df, focus)
#     print(result)
# main()