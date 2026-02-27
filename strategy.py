from dataclasses import dataclass
from indicators import ema, atr

@dataclass
class Signal:
    symbol: str
    side: str          # "LONG" or "SHORT"
    entry: float
    sl: float
    tp1: float
    tp2: float
    rr: float
    score: int
    reason: str
    invalidate: str

def regime_4h(df, p):
    c = df["close"]
    ema50 = ema(c, p["ema_fast"])
    ema200 = ema(c, p["ema_slow"])
    last_close = float(c.iloc[-1])
    last_50 = float(ema50.iloc[-1])
    last_200 = float(ema200.iloc[-1])

    chop = abs(last_50 - last_200) / last_close < p["chop_pct"]
    if chop:
        return "NO_TRADE"

    if last_close > last_200 and last_50 > last_200:
        return "BULL"
    if last_close < last_200 and last_50 < last_200:
        return "BEAR"
    return "NO_TRADE"

def bias_1h(df, p):
    c = df["close"]
    ema200 = ema(c, p["ema_slow"])
    last_close = float(c.iloc[-1])
    last_200 = float(ema200.iloc[-1])
    return "LONG" if last_close > last_200 else "SHORT"

def is_bullish_engulfing(df):
    # very simple engulfing check (last candle)
    o1,c1 = df["open"].iloc[-2], df["close"].iloc[-2]
    o2,c2 = df["open"].iloc[-1], df["close"].iloc[-1]
    return (c1 < o1) and (c2 > o2) and (c2 > o1) and (o2 < c1)

def is_bearish_engulfing(df):
    o1,c1 = df["open"].iloc[-2], df["close"].iloc[-2]
    o2,c2 = df["open"].iloc[-1], df["close"].iloc[-1]
    return (c1 > o1) and (c2 < o2) and (c2 < o1) and (o2 > c1)

def detect(df15, df1h, df4h, symbol, p):
    reg = regime_4h(df4h, p)
    if reg == "NO_TRADE":
        return None

    b = bias_1h(df1h, p)
    if (reg == "BULL" and b != "LONG") or (reg == "BEAR" and b != "SHORT"):
        return None

    c15 = df15["close"]
    ema50_15 = ema(c15, p["ema_fast"])
    atr15 = atr(df15, p["atr_len"])
    last_close = float(c15.iloc[-1])
    last_ema50 = float(ema50_15.iloc[-1])
    last_atr = float(atr15.iloc[-1])

    # pullback near EMA50
    near = abs(last_close - last_ema50) / last_close <= p["pullback_pct"]
    if not near or last_atr == 0 or last_atr != last_atr:  # NaN check
        return None

    score = 0
    score += 30  # regime aligned
    score += 25  # bias aligned

    if reg == "BULL":
        if not is_bullish_engulfing(df15):
            return None
        score += 20
        entry = last_close
        sl = entry - p["atr_mult"] * last_atr
        risk = entry - sl
        tp1 = entry + p["min_rr"] * risk
        tp2 = entry + 2.5 * risk
        rr = (tp1 - entry) / risk
        invalidate = "15m close below EMA50"
        reason = "4H bull + 1H long + 15m pullback EMA50 + bullish engulfing"
        side = "LONG"
    else:
        if not is_bearish_engulfing(df15):
            return None
        score += 20
        entry = last_close
        sl = entry + p["atr_mult"] * last_atr
        risk = sl - entry
        tp1 = entry - p["min_rr"] * risk
        tp2 = entry - 2.5 * risk
        rr = (entry - tp1) / risk
        invalidate = "15m close above EMA50"
        reason = "4H bear + 1H short + 15m pullback EMA50 + bearish engulfing"
        side = "SHORT"

    if rr < p["min_rr"]:
        return None

    # RR bonus
    if rr >= 2.0:
        score += 15

    if score < 70:
        return None

    return Signal(symbol, side, entry, sl, tp1, tp2, rr, score, reason, invalidate)