#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Created By  : Kori Vernon
# Created Date: 20/05/2023
# Email       : kori.s.vernon@gmail.com
# ---------------------------------------------------------------------------
class Position:
    def __init__(self, symbolDescription, quantity, lastTrade, pricePaid, totalGain, marketValue, pctOfPortfolio, json):
        self.sym = symbolDescription
        self.qty = quantity
        self.last_trade = lastTrade
        self.px_paid = pricePaid
        self.total_gain = totalGain
        self.market_value = marketValue
        self.pct_portfolio = pctOfPortfolio
        self.json = json

    def __str__(self):
        ret_str = f"Position: {self.sym}; Qty: {self.qty}; Last Trade: {self.px_paid}; Total Gain: {self.total_gain}; Market Value: {self.market_value}; Percentage of Portfolio; {self.pct_portfolio}"
        return ret_str
    
    def __repr__(self):
        return str(self.json)
    
def PositionsParser(portfolioPositionResponse):
    positions = portfolioPositionResponse["PortfolioResponse"]["AccountPortfolio"]

    pos = []
    for acctPortfolio in positions:
        if acctPortfolio is not None and "Position" in acctPortfolio:
            for position in acctPortfolio["Position"]:
                p = Position(symbolDescription= position["symbolDescription"], quantity=position["quantity"], lastTrade=position["Quick"]["lastTrade"], pricePaid=position["pricePaid"], totalGain=position["totalGain"], marketValue=position["marketValue"], pctOfPortfolio=position["pctOfPortfolio"],json = position)
                pos.append(p)
    return pos