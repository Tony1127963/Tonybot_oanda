import time
import os
import pandas as pd
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from config import OANDA_API_KEY, OANDA_ENV, SYMBOLS, TIMEFRAME, CANDLE_COUNT

# Připojení k OANDA API
client = oandapyV20.API(access_token=OANDA_API_KEY, environment=OANDA_ENV)

# Výstupní složka
os.makedirs("data", exist_ok=True)

def download_candles(symbol, count, granularity):
    params = {
        "count": count,
        "granularity": granularity,
        "price": "M"  # Midpoint
    }
    r = instruments.InstrumentsCandles(instrument=symbol, params=params)
    client.request(r)

    candles = r.response["candles"]
    data = []
    for c in candles:
        data.append({
            "time": c["time"],
            "open": float(c["mid"]["o"]),
            "high": float(c["mid"]["h"]),
            "low": float(c["mid"]["l"]),
            "close": float(c["mid"]["c"]),
            "volume": c["volume"]
        })

    df = pd.DataFrame(data)
    df.to_csv(f"data/{symbol}.csv", index=False)
    print(f"✅ Uloženo: data/{symbol}.csv ({len(df)} řádků)")
    return df

# Pro všechny symboly
for symbol in SYMBOLS:
    success = False
    for attempt in range(1, 3 + 1):  # max 3 pokusy
        print(f"⬇️ Stahuju: {symbol} (pokus {attempt}/3)")
        try:
            df = download_candles(symbol, count=CANDLE_COUNT, granularity=TIMEFRAME)
            if df is not None and not df.empty:
                success = True
                break
            else:
                print(f"❌ Prázdná data pro {symbol}, zkouším znovu...")
        except Exception as e:
            print(f"❌ Chyba při stahování {symbol}: {e}")
        time.sleep(3)

    if not success:
        print(f"🚫 Nezdařilo se stáhnout {symbol} ani po 3 pokusech.")
