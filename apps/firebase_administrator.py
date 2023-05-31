#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 30/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
"""This Python script provides examples on using the E*TRADE API endpoints"""
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import sys

script_path = os.path.dirname(os.path.abspath(__file__))
script_path = script_path + '/../assets/emon-analytics-firebase-adminsdk-xwnpd-db7b006da2.json'
cred = credentials.Certificate(script_path)
firebase_admin.initialize_app(cred)

from volatility_strategies import *
import random, string


db = firestore.client()

def generate_random_key():
    x = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    return x

def add_generated_position(date=TODAY):
    gen_pos_ref = db.collection(u'GeneratedPositions')

    df = vol_scraper_outliers_data(date, to_html=False)
    print(df)

    positions_dict = df.to_dict(orient='index')
    for generated_position in positions_dict.values():
        add_pos = {}
        key = generate_random_key()
        add_pos['symbol'] = generated_position['Symbol']
        add_pos['ticker'] = generated_position['Ticker']
        add_pos['strike'] = generated_position['Strike']
        add_pos['position'] = generated_position['Position']
        add_pos['lastOptionPrice'] = generated_position['Last Price']
        add_pos['GenerationDate'] = datetime.strptime('2023-05-30', "%Y-%m-%d")
        add_pos['speculativePercMove'] = generated_position['speculativePercMove']
        add_pos['percMove'] = generated_position['percMove']
        add_pos['prevDayVolatility'] = generated_position['prevDayVolatility']
        add_pos['currDayVolatility'] = generated_position['volatility']
        add_pos['underlyingPrice'] = generated_position['lastPrice']
        try:
            doc_ref = gen_pos_ref.document(key)
            doc_ref.set(add_pos)
        except Exception as e:
            print(f"Error adding record. {e}")
        else:
            print(f"Adding Record:\n{doc_ref}")

def get_all_generated_positions():
    gen_pos_ref = db.collection(u'GeneratedPositions')
    docs = gen_pos_ref.stream()
    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')


def main():
    add_generated_position('2023-05-30')
main()