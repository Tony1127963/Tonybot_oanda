import time
import pandas as pd
import joblib
import numpy as np
import os
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.pricing import PricingInfo
from config import OANDA_API_KEY, OANDA_ACCOUNT_ID
from get_features_for_symbol import get_features_for_symbol
from trailing_logic import calculate_trailing_stop
from trade_utils import close_opposite_positions
from voting_signal import get_voting_signal
from datetime import datetime
from check_trailing_tp_function import check_trailing_tp

# === Inicializace API ===
api = API(access_token=OANDA_API_KEY)
account_id = OANDA_ACCOUNT_ID

# === Načtení hotového Ensemble modelu ===
model = joblib.load("model_v180_ensemble.pkl")

# === Načtení všech symbolů ze složky /indikatory
symbol_files = os.listdir("indikatory")
symbols = [f.replace(".csv", "") for f in symbol_files if f.endswith(".csv")]

# === Uložíme si poslední signály, ať to neskáče pořád dokola
last_signals = {}
entry_price_cache = {}
peak_price_cache = {}

# === Čekání před startem
print("Čekám 5 vteřin před startem loopu...")
time.sleep(5)

# === Definované očekávané sloupce (podle nového modelu)
# === Definované očekávané sloupce (podle nového modelu)
expected_features = [
    'open', 'high', 'low', 'close', 'volume',
    'rsi', 'macd', 'macd_signal', 'macd_hist',
    'ema_20', 'ema_50', 'sma_20', 'sma_50',
    'ema', 'sma',                     # ← doplněno
    'stoch_k', 'stoch_d', 'stoch',   # ← doplněno
    'bb_bbh', 'bb_bbl', 'bb_ratio', 'bb_width',
    'cci', 'mfi', 'adx', 'atr'
]

def get_price(symbol):
    r = PricingInfo(accountID=account_id, params={"instruments": symbol})
    response = api.request(r)
    bids = float(response["prices"][0]["bids"][0]["price"])
    asks = float(response["prices"][0]["asks"][0]["price"])
    return (bids + asks) / 2

while True:
    print(f"\n===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    for symbol in symbols:
        try:
            df = pd.read_csv(f"indikatory/{symbol}.csv")
            X = get_features_for_symbol(df)
            # === Kontrola trailing take-profit pro LONG ===
            if symbol in entry_price_cache and symbol in peak_price_cache:
                current_price = float(df["close"].iloc[-1])
                tp_dist = calculate_trailing_stop(df, direction="buy")[1]
                if check_trailing_tp(symbol, current_price, entry_price_cache, peak_price_cache, threshold=tp_dist):
                    print(f"{symbol} - Otočení ceny, zavírám LONG kvůli trailing TP")
                    close_opposite_positions(api, account_id, symbol, direction="buy")
                    last_signals[symbol] = 0
                    continue

            # Kontrola, jestli obsahuje všechny očekávané featury
            if X is None or len(X) == 0 or any(col not in X.columns for col in expected_features):
                print(f"{symbol} - Chybí očekávané featury, přeskočeno.")
                continue

            ai_signal = model.predict(X)[-1]
            vote_signal = get_voting_signal(df)

            # === Kombinace AI a hlasovacího signálu ===
            if ai_signal == vote_signal:
                signal = ai_signal
            else:
                signal = 0  # HOLD, pokud se neshodují

            if last_signals.get(symbol) == signal:
                print(f"{symbol} - Stejný signál ({signal}), přeskočeno.")
                continue

            last_signals[symbol] = signal
            print(f"{symbol} - Nový signál: {signal}")

            if signal == 0:
                continue  # HOLD

            price = get_price(symbol)
            sl_dist, tp_dist, trailing_dist = calculate_trailing_stop(df, direction="buy" if signal == 1 else "sell")
            precision = 3 if "JPY" in symbol else 5

            if signal == 1:  # BUY
                current_price = float(df["close"].iloc[-1])  # ← aktuální close cena
                sl_price = round(price - sl_dist, precision)
                tp_price = round(price + tp_dist, precision)
                trailing = round(trailing_dist, precision)
                print(f"BUY @ {price:.5f} | SL: {sl_price} | TP: {tp_price} | TRAIL: {trailing}")
                close_opposite_positions(api, account_id, symbol, direction="buy")
                order_data = {
                    "order": {
                        "instrument": symbol,
                        "units": "100",
                        "type": "MARKET",
                        "positionFill": "DEFAULT",
                        "stopLossOnFill": {"price": str(sl_price)},
                        "takeProfitOnFill": {"price": str(tp_price)},
                        "trailingStopLossOnFill": {"distance": str(trailing)}
                    }
                }
                r = OrderCreate(account_id, data=order_data)
                api.request(r)
                entry_price_cache[symbol] = current_price
                peak_price_cache[symbol] = current_price

            elif signal == 2:  # SELL
                sl_price = round(price + sl_dist, precision)
                tp_price = round(price - tp_dist, precision)
                trailing = round(trailing_dist, precision)
                print(f"SELL @ {price:.5f} | SL: {sl_price} | TP: {tp_price} | TRAIL: {trailing}")
                close_opposite_positions(api, account_id, symbol, direction="sell")
                order_data = {
                    "order": {
                        "instrument": symbol,
                        "units": "-100",
                        "type": "MARKET",
                        "positionFill": "DEFAULT",
                        "stopLossOnFill": {"price": str(sl_price)},
                        "takeProfitOnFill": {"price": str(tp_price)},
                        "trailingStopLossOnFill": {"distance": str(trailing)}
                    }
                }
                r = OrderCreate(account_id, data=order_data)
                api.request(r)

        except Exception as e:
            print(f"Chyba u symbolu {symbol}: {e}")

    time.sleep(30)
