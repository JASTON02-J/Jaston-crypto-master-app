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

# muhimu sana kwa futures
exchange.set_sandbox_mode(False)

# ================= MEMORY =================
MEMORY_FILE = "market_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            return json.load(open(MEMORY_FILE))
        except:
            return {}
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f)

memory = load_memory()

# ================= SCAN FUNCTION =================
def analyze_market(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=150)

        if not bars or len(bars) < 50:
            raise Exception("Not enough data")

        df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

        # kuhakikisha numeric
        df[['o','h','l','c','v']] = df[['o','h','l','c','v']].astype(float)

        # indicators
        df['ema9'] = ta.trend.ema_indicator(df['c'], window=9)
        df['ema21'] = ta.trend.ema_indicator(df['c'], window=21)
        df['rsi'] = ta.momentum.RSIIndicator(df['c'], window=14).rsi()
        df['adx'] = ta.trend.ADXIndicator(df['h'], df['l'], df['c'], window=14).adx()

        # remove NaN
        df = df.dropna()

        if len(df) < 10:
            raise Exception("Indicators not ready")

        ema9 = df['ema9'].iloc[-1]
        ema21 = df['ema21'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        adx = df['adx'].iloc[-1]

        ema_up = ema9 > ema21
        ema_down = ema9 < ema21

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
            "price": float(df['c'].iloc[-1]),
            "confidence": float(confidence),
            "signal": signal,
            "rsi": float(rsi),
            "adx": float(adx)
        }

    except Exception as e:
        print(f"ERROR on {symbol}: {str(e)}")  # 👈 utaona kosa halisi
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

        for r in results:
            print(f"{r['symbol']}: {r['signal']} | Conf: {r['confidence']:.1f}% | RSI {r['rsi']:.1f} | ADX {r['adx']:.1f}")

        print("------------------------------------------------------------------")

        print(f"🔥 BEST MARKET: {best['symbol']}")
        print(f"📊 SIGNAL: {best['signal']}")
        print(f"🎯 CONFIDENCE: {best['confidence']:.1f}%")

        if best['confidence'] >= 70:
            print(f"🟢 ACTION: TRADE {best['symbol']} NOW 🚀")
        else:
            print("🔴 ACTION: NO CLEAR SETUP ❌")

        print("------------------------------------------------------------------")

        memory["last_scan"] = datetime.now().strftime('%H:%M:%S')
        memory["best_market"] = best
        save_memory(memory)

        time.sleep(10)

    except Exception as e:
        print("MAIN LOOP ERROR:", str(e))
        time.sleep(10)