import os
import sys

from datetime import datetime, timedelta

script_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_path + "/../")
import etrade_config

import requests

API_KEY = etrade_config.PERIGON_API_KEY
def _topics_query_(topics = ["TSLA","Tesla", "anything that says tesla"]):
      topics_query_search = []
      for titles in topics:
            titles = titles.replace("&","%26")
            elem = "%20".join(titles.split(" "))
            topics_query_search.append(elem)
      split_by = "%20OR%20"
      search_title_query = split_by.join(topics_query_search)
      print(f"Search Title Query: {search_title_query}")
      return search_title_query
def discover_articles(title):
      two_days_ago = datetime.now() - timedelta(days=1)
      date_formatted = two_days_ago.strftime("%Y-%m-%d")
      url = f"https://api.goperigon.com/v1/all?apiKey={API_KEY}" \
            f"&title={title}" \
            f"&from={date_formatted}" \
            f"&sortBy=relevance" \
            f"&page=0" \
            f"&size=10" \
            f"&showReprints=false"
      resp = requests.get(url)
      return resp.json()