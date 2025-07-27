import os
import pandas as pd
import ta

INPUT_FOLDER = "data"  # složka se surovými OHLC daty
OUTPUT_FOLDER = "indikatory"  # složka pro výstup

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def add_indicators(df):
    df = df.copy()
    df = df.dropna().reset_index(drop=True)

    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()

    # MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()  # navíc

    # EMA a SMA
    df['ema_20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
    df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()

    # Alias pro očekávané názvy:
    df['ema'] = df['ema_20']
    df['sma'] = df['sma_20']

    # Stochastic
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    df['stoch'] = df['stoch_k']  # alias pro očekávaný název

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_bbh'] = bb.bollinger_hband()
    df['bb_bbl'] = bb.bollinger_lband()
    df['bb_ratio'] = df['close'] / bb.bollinger_hband()
    df['bb_width'] = bb.bollinger_wband()

    # Ostatní indikátory navíc (připravují se na budoucí modely)
    df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close']).cci()
    df['mfi'] = ta.volume.MFIIndicator(df['high'], df['low'], df['close'], df['volume']).money_flow_index()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()

    return df.dropna()

for filename in os.listdir(INPUT_FOLDER):
    if filename.endswith(".csv"):
        print(f"📥 Zpracovávám: {filename}")
        df = pd.read_csv(os.path.join(INPUT_FOLDER, filename))
        if set(['open', 'high', 'low', 'close', 'volume']).issubset(df.columns):
            df_ind = add_indicators(df)
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            df_ind.to_csv(output_path, index=False)
            print(f"✅ Uloženo: {output_path} ({df_ind.shape[0]} řádků)")
        else:
            print(f"❌ Přeskakuji {filename} – chybí potřebné sloupce")
