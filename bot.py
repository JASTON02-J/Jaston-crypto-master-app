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

# ================= FILES =================
MEMORY_FILE = "market_memory.json"
DASHBOARD_FILE = "dashboard.json"

# ================= MEMORY =================
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

# ================= DASHBOARD =================
def update_dashboard(results, best, status="ON"):
    try:
        dashboard = {
            "time": datetime.now().strftime('%H:%M:%S'),
            "status": status,
            "results": results,
            "best": best,
            "balance": 1000,  # replace later with real balance
            "pnl": 0,
            "trades": []
        }

        with open(DASHBOARD_FILE, "w") as f:
            json.dump(dashboard, f, indent=4)

    except Exception as e:
        print("Dashboard write error:", e)

# ================= SAFE FETCH =================
def fetch_ohlcv_safe(symbol, retries=3):
    for i in range(retries):
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
            if data and len(data) > 50:
                return data
        except Exception as e:
            print(f"{symbol} fetch error:", e)
        time.sleep(2)
    return None

# ================= ANALYSIS =================
def analyze_market(symbol):
    try:
        bars = fetch_ohlcv_safe(symbol)

        if bars is None:
            raise Exception("No data")

        df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
        df[['o','h','l','c','v']] = df[['o','h','l','c','v']].astype(float)

        # Indicators
        df['ema9'] = ta.trend.ema_indicator(df['c'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['c'], 21)
        df['rsi'] = ta.momentum.RSIIndicator(df['c'], 14).rsi()
        df['adx'] = ta.trend.ADXIndicator(df['h'], df['l'], df['c'], 14).adx()

        ema9 = df['ema9'].dropna().iloc[-1]
        ema21 = df['ema21'].dropna().iloc[-1]
        rsi = df['rsi'].dropna().iloc[-1]
        adx = df['adx'].dropna().iloc[-1]

        score = 0
        if adx > 20:
            score += 1
        if rsi > 55 or rsi < 45:
            score += 1
        if ema9 > ema21 or ema9 < ema21:
            score += 1

        confidence = (score / 3) * 100

        signal = "OPPORTUNITY 🚀" if confidence >= 70 else "NO OPPORTUNITY ❌"

        return {
            "symbol": symbol.replace("/USDT", ""),
            "price": float(df['c'].iloc[-1]),
            "confidence": confidence,
            "signal": signal,
            "rsi": rsi,
            "adx": adx
        }

    except Exception as e:
        print(symbol, "analysis error:", e)
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
    print("🚀 BOT STARTED...")

    while True:
        try:
            results = []

            for symbol in SYMBOLS:
                res = analyze_market(symbol)
                results.append(res)
                time.sleep(1)

            valid = [r for r in results if r["confidence"] > 0]

            best = max(valid, key=lambda x: x["confidence"]) if valid else results[0]

            # Clear console
            os.system('cls' if os.name == 'nt' else 'clear')

            print(f"TIME: {datetime.now().strftime('%H:%M:%S')}")
            print("==========================================")

            for r in results:
                print(f"{r['symbol']} | {r['signal']} | {r['confidence']:.1f}%")

            print("==========================================")
            print(f"BEST: {best['symbol']} | {best['confidence']:.1f}%")

            # Save memory
            memory["last_scan"] = datetime.now().strftime('%H:%M:%S')
            memory["best"] = best
            save_memory(memory)

            # Update dashboard
            update_dashboard(results, best, status="ON")

            time.sleep(10)

        except Exception as e:
            print("MAIN ERROR:", e)
            update_dashboard([], {}, status="OFF")
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run_bot()