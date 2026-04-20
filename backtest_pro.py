import ccxt
import pandas as pd
import ta
import numpy as np
import matplotlib.pyplot as plt

# ================= CONFIG =================

PAIRS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"]

TIMEFRAME = "5m"
HTF = "15m"

STOP_LOSS = 0.01
TAKE_PROFIT = 0.025
RISK_PER_TRADE = 0.02

INITIAL_BALANCE = 10
COOLDOWN = 300

FEE = 0.0004
SLIPPAGE = 0.0005

exchange = ccxt.binance({"enableRateLimit": True})

# ================= DATA =================

def get_data(pair, tf):
    bars = exchange.fetch_ohlcv(pair, tf, limit=1000)  # FIXED
    df = pd.DataFrame(bars, columns=["time","open","high","low","close","volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df

# ================= VOLATILITY =================

def calculate_volatility(df):
    df = df.copy()
    df["return"] = df["close"].pct_change()
    vol = df["return"].rolling(14).std().iloc[-1]
    return abs(vol*100) if not pd.isna(vol) else 0

def classify_volatility(vol):
    if vol < 0.2:
        return "LOW"
    elif vol < 0.5:
        return "NORMAL"
    elif vol < 1.0:
        return "MEDIUM"
    elif vol < 2.0:
        return "HIGH"
    else:
        return "EXTREME"

# ================= LEVERAGE =================

def get_leverage(conf, vol):
    if conf >= 90:
        return 12 if vol < 0.3 else 7
    elif conf >= 80:
        return 10 if vol < 0.3 else 5
    else:
        return 5

# ================= INDICATORS =================

def apply_indicators(df):
    df["ema9"] = ta.trend.ema_indicator(df["close"], 9)
    df["ema21"] = ta.trend.ema_indicator(df["close"], 21)
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()
    adx = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], 14)
    df["adx"] = adx.adx()
    df["vol_ma"] = df["volume"].rolling(20).mean()
    return df

# ================= BACKTEST =================

trades = []
balance = INITIAL_BALANCE
equity_curve = []

pair_counter = {}
last_trade_time = 0
skip_counter = 0

for pair in PAIRS:

    df = get_data(pair, TIMEFRAME)
    htf = get_data(pair, HTF)

    df = apply_indicators(df)

    htf["ema50"] = ta.trend.ema_indicator(htf["close"], 50)
    htf["ema200"] = ta.trend.ema_indicator(htf["close"], 200)

    df = pd.merge_asof(
        df.sort_values("time"),
        htf[["time","ema50","ema200"]].sort_values("time"),
        on="time",
        direction="backward"
    )

    # FIX: usifute data zote
    df = df.dropna(subset=["ema9","ema21","rsi","adx","ema50","ema200"])

    # SAFETY: kama data haitoshi
    if len(df) < 100:
        continue

    position = None

    for i in range(50, len(df)):

        slice_df = df.iloc[:i]
        row = df.iloc[i]
        price = row["close"]

        ema9 = row["ema9"]
        ema21 = row["ema21"]
        rsi = row["rsi"]
        adx = row["adx"]
        volume = row["volume"]
        vol_ma = row["vol_ma"]

        trend = "UP" if row["ema50"] > row["ema200"] else "DOWN"

        signal = None
        score = 0

        if ema9 > ema21 and trend == "UP":
            signal = "LONG"
            score += 2
        elif ema9 < ema21 and trend == "DOWN":
            signal = "SHORT"
            score += 2

        if 50 < rsi < 70:
            score += 1

        if adx > 20:
            score += 2

        if volume > vol_ma:
            score += 1

        confidence = min((score / 6) * 100, 100)

        # ================= FILTERS =================

        volatility = calculate_volatility(slice_df)
        vol_label = classify_volatility(volatility)

        if vol_label in ["HIGH", "EXTREME"]:
            equity_curve.append(balance)
            skip_counter += 1
            continue

        if adx < 25:
            equity_curve.append(balance)
            skip_counter += 1
            continue

        leverage = get_leverage(confidence, volatility)

        current_time = row["time"].timestamp()
        cooldown_ok = current_time - last_trade_time > COOLDOWN

        # ================= ENTRY =================

        if position is None and confidence >= 80 and signal and cooldown_ok:

            entry = price * (1 + SLIPPAGE) if signal == "LONG" else price * (1 - SLIPPAGE)

            position = {
                "pair": pair,
                "type": signal,
                "entry": entry,
                "entry_time": row["time"],
                "leverage": leverage
            }

            last_trade_time = current_time

        # ================= EXIT =================

        if position:

            entry = position["entry"]

            if position["type"] == "LONG":
                sl = entry * (1 - STOP_LOSS)
                tp = entry * (1 + TAKE_PROFIT)

                hit_sl = row["low"] <= sl
                hit_tp = row["high"] >= tp

                if hit_sl:
                    pnl = -STOP_LOSS
                    reason = "SL"
                elif hit_tp:
                    pnl = TAKE_PROFIT
                    reason = "TP"
                else:
                    equity_curve.append(balance)
                    continue

            else:
                sl = entry * (1 + STOP_LOSS)
                tp = entry * (1 - TAKE_PROFIT)

                hit_sl = row["high"] >= sl
                hit_tp = row["low"] <= tp

                if hit_sl:
                    pnl = -STOP_LOSS
                    reason = "SL"
                elif hit_tp:
                    pnl = TAKE_PROFIT
                    reason = "TP"
                else:
                    equity_curve.append(balance)
                    continue

            # ================= PROFIT =================

            risk_amount = balance * RISK_PER_TRADE
            gross_profit = risk_amount * (pnl / STOP_LOSS)  # FIXED

            fee_cost = risk_amount * FEE * 2
            profit = gross_profit - fee_cost

            balance += profit

            trades.append([
                pair,
                position["type"],
                position["entry_time"],
                row["time"],
                round(profit,4),
                reason
            ])

            pair_counter[pair] = pair_counter.get(pair, 0) + 1
            position = None

        equity_curve.append(balance)

# ================= DASHBOARD (USIGUSE) =================

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
print("💰 FINAL: $", round(balance,4))
print("📈 NET PROFIT: $", round(balance - INITIAL_BALANCE,4))

print("\n🧠 TRADE ANALYSIS MODE")

if pair_counter:
    most = max(pair_counter, key=pair_counter.get)
    print("📊 MOST ACTIVE MARKET:", most)

wins = len([t for t in trades if t[4] > 0])
losses = len([t for t in trades if t[4] <= 0])
winrate = (wins/len(trades))*100 if trades else 0

print("\n📊 ADVANCED METRICS")
print("Wins:", wins)
print("Losses:", losses)
print("Winrate:", round(winrate,2), "%")

plt.plot(equity_curve)
plt.title("Equity Curve")
plt.xlabel("Trades")
plt.ylabel("Balance")
plt.show()