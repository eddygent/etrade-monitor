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

from datetime import datetime, timedelta
script_path = os.path.dirname(os.path.abspath(__file__))
script_path = script_path + '/../assets/emon-analytics-firebase-adminsdk-xwnpd-db7b006da2.json'
cred = credentials.Certificate(script_path)
firebase_admin.initialize_app(cred)

from volatility_strategies import *
import random, string
from yop import *


db = firestore.client()

class GeneratedPosition:
    def __init__(self):
        self.ID = None
        self.symbol = None
        self.ticker = None
        self.strike = None
        self.position = None
        self.lastOptionPrice = None
        self.position = None
        self.GenerationDate = None
        self.speculativePercMove = None
        self.percMove = None
        self.prevDayVolatility = None
        self.currDayVolatility = None
        self.underlyingPrice = None
        self.record = None
        self.exit = None
        self.gain = None
        self.underlyingGain = None

    def set_from_doc(self, doc):
        self.doc_ref = db.collection('GeneratedPositions')
        self.ID = doc.id
        data = doc.to_dict()
        self.symbol = data['symbol']
        self.ticker = data['ticker']
        self.strike = data['strike']
        self.position = data['position']
        self.lastOptionPrice  = data['lastOptionPrice']
        self.GenerationDate = data['GenerationDate']
        self.speculativePercMove = data['speculativePercMove']
        self.percMove = data['percMove']
        self.prevDayVolatility = data['prevDayVolatility']
        self.currDayVolatility = data['currDayVolatility']
        self.underlyingPrice = data['underlyingPrice']
        existing_record = {}
        try:
            existing_record = data['record']
        except Exception as e:
            print(f'record for {self.symbol} not initialized.')
            self.record = existing_record
        else:
            self.record = data['record']

        try: underlyingGain = data['underlyingGain']
        except Exception as e:
            print(f'underlyingGain for {self.symbol} not initialized.')
            self.underlyingGain = 0
        else:
            self.underlyingGain = underlyingGain

        try: gain = data['gain']
        except Exception as e:
            print(f'gain for {self.symbol} not initialized.')
            self.gain = 0
        else: self.gain = gain

        try: exit = data['exit']
        except Exception as e:
            print(f'exit for {self.symbol} not initialized.')
            self.exit = False
        else: self.gain = exit


    def update_fields(self):
        # get the updated price and underlying of the ticker and symbol
        date, underlyingPrice, optionPrice = self.getUpdatedData()
        self.gain = optionPrice - self.lastOptionPrice #notes lastOptionPrice is the first recorded option price
        self.underlyingGain = underlyingPrice - self.underlyingPrice
        self.exit = self.close_position(underlyingPrice)
        updated_data = {
                        'date': date,
                        'updatedOptionPrice': optionPrice,
                        'updatedUnderlyingPrice': underlyingPrice,
                        'gain': self.gain,
                        'underlyingGain':self.underlyingGain
                        }
        self.record[date] = updated_data
        self.doc_ref.document(self.ID).update({'record': self.record})
        self.doc_ref.document(self.ID).update({'gain': self.gain})
        self.doc_ref.document(self.ID).update({'underlyingGain': self.underlyingGain})
        self.doc_ref.document(self.ID).update({'exit': self.exit})
        print(f'Updated GeneratedPositions:\n{self.doc_ref.document(self.ID)}')

    def close_position(self, latestUnderlyingPrice):
        if self.to_date() + timedelta(days=30) >= datetime.now():
            print(f"CANNOT SELL YET - Can Sell on {self.to_date() + timedelta(days=30)}")
            return False
        # if the underlying moves too much in a direction we don't want it to move
        close_position_formula = ((self.underlyingPrice / latestUnderlyingPrice)-1) >= self.percMove/2
        print(f"[(({self.underlyingPrice} / {latestUnderlyingPrice})-1) >= {self.percMove}/2] === {close_position_formula}")
        if close_position_formula:
            # if the position continues to slip further in the direction we don't want, close out
            return True
        return False

    def getUpdatedData(self):
        return TODAY, yf.Ticker(self.ticker).info['currentPrice'], lastSymbolPrice(self.symbol)

    def __repr__(self):
        return f"""
        self.ID = {self.ID}
        self.symbol = {self.symbol}
        self.ticker = {self.ticker}
        self.strike = {self.strike}
        self.position = {self.position}
        self.lastOptionPrice = {self.lastOptionPrice}
        self.GenerationDate = {self.GenerationDate}
        self.speculativePercMove = {self.speculativePercMove}
        self.percMove = {self.percMove}
        self.prevDayVolatility = {self.prevDayVolatility}
        self.currDayVolatility = {self.currDayVolatility}
        self.underlyingPrice = {self.underlyingPrice}
        self.record = {self.record}
        self.exit = {self.exit}
        self.gain = {self.gain}
        self.underlyingGain = {self.underlyingGain}
                """

    def __str__(self):
        return f"""
        ID = {self.ID}
        symbol = {self.symbol}
        ticker = {self.ticker}
        strike = {self.strike}
        lastOptionPrice = {self.lastOptionPrice}
        position = {self.position}
        GenerationDate = {self.GenerationDate}
        speculativePercMove = {self.speculativePercMove}
        percMove = {self.percMove}
        prevDayVolatility = {self.prevDayVolatility}
        currDayVolatility = {self.currDayVolatility}
        underlyingPrice = {self.underlyingPrice}
        record = {self.record}
        exit = {self.exit}
        gain = {self.gain}
        underlyingGain = {self.underlyingGain}
                """

    def to_date(self):
        return datetime.strptime(str(self.GenerationDate)[:10],"%Y-%m-%d")

def generate_random_key():
    x = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    return x

def add_generated_positions(date=TODAY):
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
        add_pos['GenerationDate'] = datetime.strptime(date, "%Y-%m-%d")
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
            print(f"Adding Record:\n{add_pos}")

def get_all_generated_positions():
    gen_pos_ref = db.collection(u'GeneratedPositions')
    docs = gen_pos_ref.stream()
    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')

def get_generated_positions_obj():
    gen_pos_ref = db.collection(u'GeneratedPositions')
    docs = gen_pos_ref.stream()
    for doc in docs:
        p = GeneratedPosition()
        p.set_from_doc(doc)
        p.update_fields()
        print(f'{doc.id} => {p}')
def main():
    get_generated_positions_obj()
main()