import pandas as pd

# === Funkce pro extrakci posledních feature hodnot ===
def get_features_for_symbol(df, lookback=1):
    required_columns = [
        'open', 'high', 'low', 'close', 'volume',
        'rsi', 'macd', 'macd_signal', 'macd_hist',
        'ema_20', 'ema_50', 'sma_20', 'sma_50',
        'ema', 'sma',
        'stoch_k', 'stoch_d', 'stoch',
        'bb_bbh', 'bb_bbl', 'bb_ratio', 'bb_width',
        'cci', 'mfi', 'adx', 'atr'
    ]

    # Zkontroluj, jestli všechny potřebné sloupce existují
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(f"⚠️ Chybí některé featury! Očekáváno: {required_columns}")
        print(f"Chybí: {missing}")
        return None

    # Vezmeme poslední hodnoty
    df = df[required_columns].dropna()
    if len(df) < lookback:
        return None

    return df[-lookback:]
