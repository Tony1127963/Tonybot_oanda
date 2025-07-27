
def calculate_trailing_stop(df, symbol, direction="buy"):
    atr = df["atr"].iloc[-1]

    # Minimální trailing stop vzdálenost podle typu páru
    if "JPY" in symbol:
        trailing_min = 0.05  # např. pro USD_JPY, GBP_JPY
    else:
        trailing_min = 0.001  # např. pro EUR_USD, AUD_CAD

    sl = max(atr * 1.5, trailing_min)
    tp = max(atr * 3.0, trailing_min * 2)
    trailing = max(atr * 2.0, trailing_min)

    return sl, tp, trailing