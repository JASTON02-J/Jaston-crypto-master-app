import ccxt
import pandas as pd
import ta
from datetime import datetime

# ================= CONFIG =================

PAIRS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"]

TIMEFRAME = "5m"
HTF = "15m"

STOP_LOSS = 0.01
TAKE_PROFIT = 0.025
RISK_PER_TRADE = 0.02

INITIAL_BALANCE = 10
COOLDOWN = 60

# ================= EXCHANGE =================

exchange = ccxt.binance({"enableRateLimit": True})

# ================= DATA =================

def get_data(pair, tf):
    try:
        bars = exchange.fetch_ohlcv(pair, tf, limit=500)

        df = pd.DataFrame(bars, columns=[
            "time","open","high","low","close","volume"
        ])

        df["time"] = pd.to_datetime(df["time"], unit="ms")

        return df

    except Exception as e:
        print("DATA ERROR:", pair, str(e))
        return None

# ================= INDICATORS =================

def apply_indicators(df):
    df["ema9"] = ta.trend.ema_indicator(df["close"], 9)
    df["ema21"] = ta.trend.ema_indicator(df["close"], 21)

    df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()

    adx = ta.trend.ADXIndicator(
        df["high"], df["low"], df["close"], 14
    )

    df["adx"] = adx.adx()
    df["vol_ma"] = df["volume"].rolling(20).mean()

    return df

# ================= BACKTEST =================

trades = []
balance = INITIAL_BALANCE
pair_counter = {}

last_trade_time = 0

for pair in PAIRS:

    df = get_data(pair, TIMEFRAME)
    htf = get_data(pair, HTF)

    if df is None or htf is None:
        continue

    df = apply_indicators(df)

    htf["ema50"] = ta.trend.ema_indicator(htf["close"], 50)
    htf["ema200"] = ta.trend.ema_indicator(htf["close"], 200)

    df = df.dropna()
    htf = htf.dropna()

    if len(df) < 50 or len(htf) < 50:
        continue

    position = None

    for i in range(50, len(df)):

        row = df.iloc[i]
        price = row["close"]

        ema9 = row["ema9"]
        ema21 = row["ema21"]

        rsi = row["rsi"]
        adx = row["adx"]

        volume = row["volume"]
        vol_ma = row["vol_ma"]

        # SAFE HTF MATCH
        htf_row = htf.iloc[min(i, len(htf)-1)]

        trend = "UP" if htf_row["ema50"] > htf_row["ema200"] else "DOWN"

        signal = None
        score = 0

        if ema9 > ema21 and trend == "UP":
            signal = "LONG"
            score += 1

        elif ema9 < ema21 and trend == "DOWN":
            signal = "SHORT"
            score += 1

        if rsi > 55 or rsi < 45:
            score += 1

        if adx > 20:
            score += 1

        if volume > vol_ma:
            score += 1

        confidence = (score / 4) * 100

        current_time = row["time"].timestamp()
        cooldown_ok = current_time - last_trade_time > COOLDOWN

        # ENTRY
        if position is None and confidence >= 75 and signal is not None and cooldown_ok:

            position = {
                "pair": pair,
                "type": signal,
                "entry": price,
                "entry_time": row["time"]
            }

            last_trade_time = current_time

        # EXIT
        if position:

            entry = position["entry"]

            if position["type"] == "LONG":

                sl = entry * (1 - STOP_LOSS)
                tp = entry * (1 + TAKE_PROFIT)

                if row["low"] <= sl:
                    pnl = -STOP_LOSS
                    reason = "SL"

                elif row["high"] >= tp:
                    pnl = TAKE_PROFIT
                    reason = "TP"

                else:
                    continue

            else:

                sl = entry * (1 + STOP_LOSS)
                tp = entry * (1 - TAKE_PROFIT)

                if row["high"] >= sl:
                    pnl = -STOP_LOSS
                    reason = "SL"

                elif row["low"] <= tp:
                    pnl = TAKE_PROFIT
                    reason = "TP"

                else:
                    continue

            # RISK MANAGEMENT (REALISTIC)
            risk_amount = balance * RISK_PER_TRADE
            profit = risk_amount * (pnl / STOP_LOSS)

            balance += profit

            trades.append([
                pair,
                position["type"],
                position["entry_time"],
                row["time"],
                round(profit, 4),
                reason
            ])

            pair_counter[pair] = pair_counter.get(pair, 0) + 1

            position = None

# ================= DASHBOARD =================

print("\n🚀 JASTON FORENSIC BACKTEST (LIVE MIRROR MODE)")
print("============================================================")

print("COIN        TYPE     ENTRY TIME          EXIT TIME           PnL     REASON")
print("--------------------------------------------------------------------------")

for t in trades[:10]:

    coin, typ, entry, exit_time, pnl, reason = t

    exit_time = exit_time if exit_time else "N/A"
    pnl = pnl if pnl is not None else 0

    print(f"{coin:<10} {typ:<7} {entry}  {exit_time}  {pnl:+.4f}   {reason}")

print("==========================================================================")

print("\n🚀 TOTAL TRADES:", len(trades))
print("💰 INITIAL: $", INITIAL_BALANCE)
print("💰 FINAL: $", round(balance, 4))
print("📈 NET PROFIT: $", round(balance - INITIAL_BALANCE, 4))

print("\n🧠 TRADE ANALYSIS MODE")

if pair_counter:
    most = max(pair_counter, key=pair_counter.get)
    print("📊 MOST ACTIVE MARKET:", most)