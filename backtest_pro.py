 import ccxt
import pandas as pd
import ta
import os
from datetime import datetime

# ================= CONFIG =================
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
INITIAL_CAPITAL = 10.0
LEVERAGE = 20

STOP_LOSS_AMT = 0.20
TAKE_PROFIT_AMT = 0.40

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

# ================= CANDLE PATTERN =================
def candle_pattern(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last['close'] - last['open'])
    rng = last['high'] - last['low']

    if body < rng * 0.1:
        return "DOJI ⚪"
    elif last['close'] > last['open'] and prev['close'] < prev['open']:
        return "BULL ENGULF 🟢"
    elif last['close'] < last['open'] and prev['close'] > prev['open']:
        return "BEAR ENGULF 🔴"
    elif (last['low'] < last['open'] and last['low'] < last['close']):
        return "HAMMER 🟢"
    elif (last['high'] > last['open'] and last['high'] > last['close']):
        return "SHOOT STAR 🔴"
    return "NONE"

# ================= ANALYZE MARKET =================
def analyze(symbol):

    bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=300)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])

    df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], 14).adx()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()

    price = df['close'].iloc[-1]

    ema_up = df['ema9'].iloc[-1] > df['ema21'].iloc[-1]

    score = 0
    if ema_up:
        score += 1
    if df['adx'].iloc[-1] > 20:
        score += 1
    if df['rsi'].iloc[-1] > 55 or df['rsi'].iloc[-1] < 45:
        score += 1

    candle = candle_pattern(df)

    confidence = (score / 3) * 100

    if confidence >= 70:
        signal = "OPPORTUNITY 🚀"
    else:
        signal = "NO OPPORTUNITY ❌"

    return {
        "symbol": symbol.replace("/USDT", ""),
        "price": price,
        "confidence": confidence,
        "signal": signal,
        "candle": candle
    }

# ================= BACKTEST ENGINE =================
wallet = INITIAL_CAPITAL
trade_log = []

for symbol in SYMBOLS:

    bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=300)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])

    df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], 14).adx()

    in_trade = False
    entry = 0

    for i in range(2, len(df)):

        price = df['close'].iloc[i]

        ema_up = df['ema9'].iloc[i] > df['ema21'].iloc[i]
        ema_down = df['ema9'].iloc[i] < df['ema21'].iloc[i]

        if not in_trade and df['adx'].iloc[i] > 20:

            if ema_up:
                in_trade = True
                entry = price
                side = "LONG"

            elif ema_down:
                in_trade = True
                entry = price
                side = "SHORT"

        elif in_trade:

            pnl = (price - entry)/entry if side=="LONG" else (entry - price)/entry
            pnl_usdt = wallet * 0.5 * pnl * LEVERAGE

            exit_sl = pnl_usdt <= -STOP_LOSS_AMT
            exit_tp = pnl_usdt >= TAKE_PROFIT_AMT
            exit_trend = (side=="LONG" and ema_down) or (side=="SHORT" and ema_up)

            if exit_sl or exit_tp or exit_trend:
                wallet += pnl_usdt

                trade_log.append({
                    "symbol": symbol.replace("/USDT",""),
                    "pnl": pnl_usdt,
                    "wallet": wallet,
                    "reason": "SL" if exit_sl else ("TP" if exit_tp else "TREND")
                })

                in_trade = False

# ================= MARKET SCANNER =================
results = [analyze(s) for s in SYMBOLS]
best = max(results, key=lambda x: x["confidence"])

# ================= DASHBOARD =================
os.system('cls' if os.name == 'nt' else 'clear')

print(f"🚀 JASTON AI SYNCHRONIZED BACKTEST | {datetime.now().strftime('%H:%M:%S')}")
print("------------------------------------------------------------")

print("📡 MARKET RADAR:")
for r in results:
    print(f"{r['symbol']}: {r['signal']} | {r['confidence']:.1f}% | 🕯 {r['candle']}")

print("------------------------------------------------------------")

print(f"🔥 BEST MARKET: {best['symbol']}")
print(f"📊 SIGNAL: {best['signal']}")
print(f"🎯 CONFIDENCE: {best['confidence']:.1f}%")

print("------------------------------------------------------------")

print(f"🚀 TOTAL TRADES: {len(trade_log)}")
print(f"💰 INITIAL: ${INITIAL_CAPITAL:.2f}")
print(f"💰 FINAL: ${wallet:.2f}")
print(f"📈 NET PROFIT: ${wallet - INITIAL_CAPITAL:.4f}")

print("------------------------------------------------------------")

if best['confidence'] >= 70:
    print(f"🟢 RECOMMENDATION: TRADE {best['symbol']} 🚀")
else:
    print("🔴 RECOMMENDATION: NO CLEAR SETUP ❌")