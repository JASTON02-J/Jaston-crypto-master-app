 import ccxt
import pandas as pd
import ta
import os
import time
import json
from datetime import datetime

# ================= CONFIG =================
API_KEY = "dUTfsZjIuDVwHcaIAYwVEJ4n7Te8jHsEeRc2wJencEPxHC0XKygve29qOYpY1Co9"
SECRET = "m2h1SRu4tU9wdMdDkqHVII8lpU6qtnCXvajiYOp9uUTxH6iaY37K3fujcOO6IXYh"

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# ================= MEMORY =================
MEMORY_FILE = "market_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        return json.load(open(MEMORY_FILE))
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f)

memory = load_memory()

# ================= SCAN FUNCTION =================
def analyze_market(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
        df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

        df['ema9'] = ta.trend.ema_indicator(df['c'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['c'], 21)
        df['rsi'] = ta.momentum.RSIIndicator(df['c'], 14).rsi()
        df['adx'] = ta.trend.ADXIndicator(df['h'], df['l'], df['c'], 14).adx()

        ema_up = df['ema9'].iloc[-1] > df['ema21'].iloc[-1]
        ema_down = df['ema9'].iloc[-1] < df['ema21'].iloc[-1]

        rsi = df['rsi'].iloc[-1]
        adx = df['adx'].iloc[-1]

        # ================= SCORE ENGINE =================
        score = 0
        if adx > 20:
            score += 1
        if rsi > 55 or rsi < 45:
            score += 1
        if ema_up or ema_down:
            score += 1

        confidence = (score / 3) * 100

        if confidence >= 70:
            signal = "OPPORTUNITY 🚀"
        else:
            signal = "NO OPPORTUNITY ❌"

        return {
            "symbol": symbol.replace("/USDT", ""),
            "price": df['c'].iloc[-1],
            "confidence": confidence,
            "signal": signal,
            "rsi": rsi,
            "adx": adx
        }

    except:
        return {
            "symbol": symbol.replace("/USDT", ""),
            "price": 0,
            "confidence": 0,
            "signal": "ERROR",
            "rsi": 0,
            "adx": 0
        }

# ================= MAIN LOOP =================
while True:
    try:
        results = []

        for s in SYMBOLS:
            results.append(analyze_market(s))

        best = max(results, key=lambda x: x["confidence"])

        os.system('cls' if os.name == 'nt' else 'clear')

        print(f"🚀 MULTI-MARKET AI SCANNER | {datetime.now().strftime('%H:%M:%S')}")
        print("------------------------------------------------------------------")

        # ================= MARKET LIST =================
        for r in results:
            print(f"{r['symbol']}: {r['signal']} | Conf: {r['confidence']:.1f}% | RSI {r['rsi']:.1f} | ADX {r['adx']:.1f}")

        print("------------------------------------------------------------------")

        # ================= BEST MARKET =================
        print(f"🔥 BEST MARKET: {best['symbol']}")
        print(f"📊 SIGNAL: {best['signal']}")
        print(f"🎯 CONFIDENCE: {best['confidence']:.1f}%")

        # ================= GLOBAL STATUS =================
        if best['confidence'] >= 70:
            print(f"🟢 ACTION: TRADE {best['symbol']} NOW 🚀")
        else:
            print("🔴 ACTION: NO CLEAR SETUP ❌")

        print("------------------------------------------------------------------")

        # save memory
        memory["last_scan"] = datetime.now().strftime('%H:%M:%S')
        memory["best_market"] = best
        save_memory(memory)

        time.sleep(10)

    except Exception:
        time.sleep(10)