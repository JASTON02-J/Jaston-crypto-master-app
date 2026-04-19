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

RISK_PER_TRADE = 0.02  # 2% risk
RR_RATIO = 2           # Risk:Reward 1:2

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

DASHBOARD_FILE = "dashboard.json"
TRADES_FILE = "trades.json"

# ================= INIT FILES =================
if not os.path.exists(TRADES_FILE):
    with open(TRADES_FILE, "w") as f:
        json.dump([], f)

# ================= SAVE DASHBOARD =================
def save_dashboard(data):
    with open(DASHBOARD_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ================= SAVE TRADE =================
def log_trade(trade):
    trades = json.load(open(TRADES_FILE))
    trades.append(trade)
    with open(TRADES_FILE, "w") as f:
        json.dump(trades, f, indent=4)

# ================= FETCH =================
def fetch_ohlcv_safe(symbol):
    for _ in range(3):
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
            if data:
                return data
        except:
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

        df['ema9'] = ta.trend.ema_indicator(df['c'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['c'], 21)
        df['rsi'] = ta.momentum.RSIIndicator(df['c'], 14).rsi()
        df['adx'] = ta.trend.ADXIndicator(df['h'], df['l'], df['c'], 14).adx()

        ema9 = df['ema9'].dropna().iloc[-1]
        ema21 = df['ema21'].dropna().iloc[-1]
        rsi = df['rsi'].dropna().iloc[-1]
        adx = df['adx'].dropna().iloc[-1]

        ema_up = ema9 > ema21
        ema_down = ema9 < ema21

        score = 0
        if adx > 20:
            score += 1
        if rsi > 55 or rsi < 45:
            score += 1
        if ema_up or ema_down:
            score += 1

        confidence = (score / 3) * 100
        signal = "BUY" if ema_up else "SELL"

        return {
            "symbol": symbol,
            "price": df['c'].iloc[-1],
            "confidence": confidence,
            "signal": signal,
            "rsi": rsi,
            "adx": adx
        }

    except:
        return None

# ================= EXECUTE TRADE =================
def execute_trade(data, balance):
    symbol = data["symbol"]
    price = data["price"]

    risk_amount = balance * RISK_PER_TRADE
    qty = risk_amount / price

    if data["signal"] == "BUY":
        sl = price * 0.99
        tp = price * (1 + 0.02)
    else:
        sl = price * 1.01
        tp = price * (1 - 0.02)

    try:
        exchange.create_market_order(symbol, data["signal"].lower(), qty)

        trade = {
            "time": datetime.now().strftime('%H:%M:%S'),
            "symbol": symbol,
            "side": data["signal"],
            "entry": price,
            "sl": sl,
            "tp": tp,
            "status": "OPEN",
            "pnl": 0
        }

        log_trade(trade)

    except Exception as e:
        print("Trade error:", e)

# ================= MAIN LOOP =================
def run_bot():
    while True:
        try:
            results = []

            for s in SYMBOLS:
                r = analyze_market(s)
                if r:
                    results.append(r)
                time.sleep(1)

            best = max(results, key=lambda x: x["confidence"])

            balance = exchange.fetch_balance()['total']['USDT']

            if best["confidence"] >= 70:
                execute_trade(best, balance)

            dashboard_data = {
                "status": "ACTIVE",
                "time": datetime.now().strftime('%H:%M:%S'),
                "balance": balance,
                "results": results,
                "best": best
            }

            save_dashboard(dashboard_data)

            time.sleep(10)

        except Exception as e:
            print("Error:", e)
            save_dashboard({"status": "STOPPED"})
            time.sleep(5)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        save_dashboard({"status": "STOPPED"})