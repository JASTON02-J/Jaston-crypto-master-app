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
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(data):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Memory save error:", e)

memory = load_memory()

# ================= SAFE FETCH =================
def fetch_ohlcv_safe(symbol, retries=3, delay=2):
    for attempt in range(retries):
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)

            if data and len(data) > 50:
                return data

            print(f"[{symbol}] Not enough data, retrying...")

        except Exception as e:
            print(f"[{symbol}] Fetch error (try {attempt+1}): {e}")

        time.sleep(delay)

    return None

# ================= ANALYSIS =================
def analyze_market(symbol):
    try:
        bars = fetch_ohlcv_safe(symbol)

        if bars is None:
            raise Exception("No market data received")

        df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])

        # Ensure numeric types
        df[['o','h','l','c','v']] = df[['o','h','l','c','v']].astype(float)

        # ================= INDICATORS =================
        df['ema9'] = ta.trend.ema_indicator(df['c'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['c'], 21)
        df['rsi'] = ta.momentum.RSIIndicator(df['c'], 14).rsi()
        df['adx'] = ta.trend.ADXIndicator(df['h'], df['l'], df['c'], 14).adx()

        # Get last valid values
        ema9 = df['ema9'].dropna().iloc[-1]
        ema21 = df['ema21'].dropna().iloc[-1]
        rsi = df['rsi'].dropna().iloc[-1]
        adx = df['adx'].dropna().iloc[-1]

        ema_up = ema9 > ema21
        ema_down = ema9 < ema21

        # ================= SCORE ENGINE (UNCHANGED) =================
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

    except Exception as e:
        print(f"[{symbol}] ANALYSIS ERROR:", e)

        return {
            "symbol": symbol.replace("/USDT", ""),
            "price": 0,
            "confidence": 0,
            "signal": "ERROR",
            "rsi": 0,
            "adx": 0
        }

# ================= MAIN LOOP =================
def run_bot():
    print("Bot is starting...")

    while True:
        try:
            results = []

            for symbol in SYMBOLS:
                result = analyze_market(symbol)
                results.append(result)

                # Prevent rate limit
                time.sleep(1)

            # Get best market safely
            valid_results = [r for r in results if r["confidence"] > 0]

            if valid_results:
                best = max(valid_results, key=lambda x: x["confidence"])
            else:
                best = results[0]

            # Clear screen
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

            # ================= GLOBAL ACTION =================
            if best['confidence'] >= 70:
                print(f"🟢 ACTION: TRADE {best['symbol']} NOW 🚀")
            else:
                print("🔴 ACTION: NO CLEAR SETUP ❌")

            print("------------------------------------------------------------------")

            # ================= SAVE MEMORY =================
            memory["last_scan"] = datetime.now().strftime('%H:%M:%S')
            memory["best_market"] = best
            save_memory(memory)

            time.sleep(10)

        except Exception as e:
            print("MAIN LOOP ERROR:", e)
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run_bot()