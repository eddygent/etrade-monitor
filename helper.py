#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
import locale
locale.setlocale( locale.LC_ALL, 'en_CA.UTF-8' )
def format_currency(currency):
    return locale.currency(currency, grouping=True)