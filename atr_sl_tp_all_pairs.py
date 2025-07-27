import pandas as pd
import ta
import os

# === Nastavení ===
atr_period = 14
rrr = 2  # Risk/Reward ratio
data_folder = "indikatory"
output = []

# Tvůj seznam všech párů podle zpracování
pairs = [
    "AUD_CAD", "AUD_CHF", "AUD_JPY", "AUD_USD",
    "CAD_JPY", "CHF_JPY", "EUR_AUD", "EUR_CAD",
    "EUR_GBP", "EUR_JPY", "EUR_NZD", "EUR_USD",
    "GBP_AUD", "GBP_CAD", "GBP_JPY", "GBP_NZD", "GBP_USD",
    "NZD_CAD", "NZD_CHF", "NZD_JPY", "NZD_USD",
    "USD_CAD", "USD_JPY"
]

# Výpočet pro každý pár
for pair in pairs:
    file_path = os.path.join(data_folder, f"{pair}.csv")
    if not os.path.exists(file_path):
        print(f"❌ Soubor nenalezen: {file_path}")
        continue

    df = pd.read_csv(file_path)

    if not {"high", "low", "close"}.issubset(df.columns):
        print(f"⚠️ Chybí potřebné sloupce v {pair}")
        continue

    df["atr"] = ta.volatility.AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=atr_period
    ).average_true_range()

    last_atr = df["atr"].iloc[-1]
    sl = round(last_atr, 5)
    tp = round(last_atr * rrr, 5)

    output.append({
        "pair": pair,
        "ATR": round(last_atr, 5),
        "SL (1xATR)": sl,
        "TP (2xATR)": tp
    })

# Výsledná tabulka
result_df = pd.DataFrame(output)
result_df.to_csv("atr_levels.csv", index=False)

# Výpis do konzole
print("✅ Výpočet hotov. Tabulka uložena jako atr_levels.csv")
print(result_df)
