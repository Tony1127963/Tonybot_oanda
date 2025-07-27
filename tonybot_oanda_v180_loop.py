import joblib
import numpy as np
import pandas as pd
import os
import time
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.pricing import PricingInfo
from config import OANDA_API_KEY, OANDA_ACCOUNT_ID
from get_features_for_symbol import get_features_for_symbol
from trailing_logic import calculate_trailing_stop
from trade_utils import close_opposite_positions
from voting_signal import get_voting_signal
from check_trailing_tp_function import check_trailing_tp
from datetime import datetime

# === Inicializace API ===
api = API(access_token=OANDA_API_KEY)
account_id = OANDA_ACCOUNT_ID

# === Nastavení minimální confidence
CONFIDENCE_THRESHOLD = 0.85

# === Načtení modelu
model = joblib.load("model_v180_ensemble.pkl")

# === Symboly
symbol_files = os.listdir("indikatory")
symbols = [f.replace(".csv", "") for f in symbol_files if f.endswith(".csv")]
last_signals = {}
entry_price_cache = {}
peak_price_cache = {}

print("⏳ Čekám 5 vteřin před startem loopu...")
time.sleep(5)

expected_features = [
    'open', 'high', 'low', 'close', 'volume',
    'rsi', 'macd', 'macd_signal', 'macd_hist',
    'ema_20', 'ema_50', 'sma_20', 'sma_50',
    'ema', 'sma', 'stoch',
    'stoch_k', 'stoch_d',
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

            if symbol in entry_price_cache and symbol in peak_price_cache:
                current_price = float(df["close"].iloc[-1])
                # LONG
                tp_dist_long = calculate_trailing_stop(df, symbol, direction="buy")[1]
                exit_long, _ = check_trailing_tp(symbol, current_price, "buy", tp_dist_long, peak_price_cache)
                if exit_long:
                    print(f"{symbol} - 💰 Trailing TP aktivován, zavírám LONG")
                    close_opposite_positions(api, account_id, symbol, direction="buy")
                    last_signals[symbol] = 0
                    del entry_price_cache[symbol]
                    del peak_price_cache[symbol]
                    continue
                # SHORT
                tp_dist_short = calculate_trailing_stop(df, symbol, direction="sell")[1]
                exit_short, _ = check_trailing_tp(symbol, current_price, "sell", tp_dist_short, peak_price_cache)
                if exit_short:
                    print(f"{symbol} - 💰 Trailing TP aktivován, zavírám SHORT")
                    close_opposite_positions(api, account_id, symbol, direction="sell")
                    last_signals[symbol] = 0
                    del entry_price_cache[symbol]
                    del peak_price_cache[symbol]
                    continue

            if X is None or len(X) == 0 or any(col not in X.columns for col in expected_features):
                print(f"{symbol} - ⚠️ Chybí featury, přeskočeno.")
                continue

            proba = model.predict_proba(X)[-1]
            ai_signal = int(np.argmax(proba))
            confidence = float(np.max(proba))

            if confidence < CONFIDENCE_THRESHOLD:
                print(f"{symbol} - ❌ Confidence {confidence:.2f} pod prahem, přeskočeno.")
                continue

            vote_signal = get_voting_signal(df.iloc[-1])
            signal = ai_signal if ai_signal == vote_signal else 0

            if last_signals.get(symbol) == signal:
                print(f"{symbol} - Stejný signál ({signal}), přeskočeno.")
                continue

            last_signals[symbol] = signal
            print(f"{symbol} - 🔔 Nový signál: {signal} (AI confidence: {confidence:.2f})")

            if signal == 0:
                continue

            price = get_price(symbol)
            sl_dist, tp_dist, trailing_dist = calculate_trailing_stop(df, symbol, direction="buy" if signal == 1 else "sell")
            precision = 3 if "JPY" in symbol else 5

            if signal == 1:  # BUY
                entry_price_cache[symbol] = price
                peak_price_cache[symbol] = price
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

            elif signal == 2:  # SELL
                entry_price_cache[symbol] = price
                peak_price_cache[symbol] = price
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
            print(f"❌ Chyba u symbolu {symbol}: {e}")

    time.sleep(30)