import locale
locale.setlocale( locale.LC_ALL, 'en_CA.UTF-8' )
def format_currency(currency):
    return locale.currency(currency, grouping=True)