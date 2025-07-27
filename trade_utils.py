
from oandapyV20.endpoints.positions import OpenPositions
from oandapyV20.endpoints.trades import TradesList, TradeClose

def close_opposite_positions(api, account_id, symbol, direction):
    r = OpenPositions(account_id)
    data = api.request(r)

    for pos in data["positions"]:
        if pos["instrument"] == symbol:
            net = float(pos["long"]["units"]) - float(pos["short"]["units"])

            if (net > 0 and direction == "sell") or (net < 0 and direction == "buy"):
                # Nutné zavolat otevřené trady pro daný instrument
                trades = api.request(TradesList(account_id))  # ← tady byla chyba
                for trade in trades["trades"]:
                    if trade["instrument"] == symbol:
                        close = TradeClose(account_id, tradeID=trade["id"])
                        api.request(close)
