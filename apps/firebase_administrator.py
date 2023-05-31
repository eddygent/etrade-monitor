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

    def set_from_document(self, doc):
        self.doc_ref = db.collection(u'GeneratedPositions')
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
            logging.DEBUG(f'record for {self.symbol} not initialized.')
        self.record = existing_record

        try: underlyingGain = data['underlyingGain']
        except Exception as e:
            logging.DEBUG(f'underlyingGain for {self.symbol} not initialized.')
            underlyingGain = 0
        self.underlyingGain = underlyingGain

        try: gain = data['gain']
        except Exception as e:
            logging.DEBUG(f'gain for {self.symbol} not initialized.')
            gain = 0
        self.gain = gain

        try: exit = data['exit']
        except Exception as e:
            logging.DEBUG(f'exit for {self.symbol} not initialized.')
            exit = False
        self.gain = exit

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
        self.doc_ref.doc(self.doc_id).update({'record': self.record})
        self.doc_ref.doc(self.doc_id).update({'gain': self.gain})
        self.doc_ref.doc(self.doc_id).update({'underlyingGain': self.underlyingGain})
        self.doc_ref.doc(self.doc_id).update({'exit': self.exit})
        print(f'Updated GeneratedPositions:\n{self.doc_ref.doc(self.doc_id).to_dict()}')

    def close_position(self, latestUnderlyingPrice):
        # if the underlying moves too much in a direction we don't want it to move
        if (self.underlyingPrice / latestUnderlyingPrice) >= self.percMove/2:
            # if the position continues to slip further in the direction we don't want, close out
            return True
        return False


    def getUpdatedData(self):
        pass


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