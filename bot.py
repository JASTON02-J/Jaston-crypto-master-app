import ccxt
import pandas as pd
import ta
import os
import time
import json
from datetime import datetime

# ================= CONFIG =================
API_KEY = "dUTfsZjIuDVwHcaIAYwVEJ4n7Te8jHsEeRc2wJencEPxHC0XKygve29qOYpY1Co9Y"
SECRET = "m2h1SRu4tU9wdMdDkqHVII8lpU6qtnCXvajiYOp9uUTxH6iaY37K3fujcOO6IXYh"

SYMBOLS = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "BNB/USDT:USDT"]

RISK_PER_TRADE = 0.02

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

exchange.load_markets()

DASHBOARD_FILE = "dashboard.json"
TRADES_FILE = "trades.json"

# ================= INIT FILE =================
if not os.path.exists(TRADES_FILE):
    with open(TRADES_FILE, "w") as f:
        json.dump([], f)

# ================= SAVE =================
def save_dashboard(data):
    with open(DASHBOARD_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_trade(trade):
    trades = json.load(open(TRADES_FILE))
    trades.append(trade)
    with open(TRADES_FILE, "w") as f:
        json.dump(trades, f, indent=4)

# ================= FETCH =================
def fetch_data(symbol):
    for _ in range(3):
        try:
            return exchange.fetch_ohlcv(symbol, '5m', limit=100)
        except:
            time.sleep(2)
    return None

# ================= ANALYSIS =================
def analyze(symbol):
    try:
        data = fetch_data(symbol)
        if not data:
            return None

        df = pd.DataFrame(data, columns=['t','o','h','l','c','v'])
        df[['o','h','l','c','v']] = df[['o','h','l','c','v']].astype(float)

        df['ema9'] = ta.trend.ema_indicator(df['c'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['c'], 21)
        df['rsi'] = ta.momentum.RSIIndicator(df['c'], 14).rsi()
        df['adx'] = ta.trend.ADXIndicator(df['h'], df['l'], df['c'], 14).adx()

        ema9 = df['ema9'].dropna().iloc[-1]
        ema21 = df['ema21'].dropna().iloc[-1]
        rsi = df['rsi'].dropna().iloc[-1]
        adx = df['adx'].dropna().iloc[-1]
        price = df['c'].iloc[-1]

        ema_up = ema9 > ema21

        score = 0
        if adx > 20: score += 1
        if rsi > 55 or rsi < 45: score += 1
        if ema_up or not ema_up: score += 1

        confidence = (score / 3) * 100

        signal = "BUY" if ema_up else "SELL"

        return {
            "symbol": symbol,
            "price": price,
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

    try:
        market = exchange.market(symbol)
        min_qty = market['limits']['amount']['min']

        risk_amount = balance * RISK_PER_TRADE
        qty = risk_amount / price

        qty = max(qty, min_qty)
        qty = float(exchange.amount_to_precision(symbol, qty))

        if qty < min_qty:
            print(f"Skipped {symbol}, qty too small")
            return

        side = "buy" if data["signal"] == "BUY" else "sell"

        exchange.create_market_order(symbol, side, qty)

        trade = {
            "time": datetime.now().strftime('%H:%M:%S'),
            "symbol": symbol,
            "side": side.upper(),
            "entry": price,
            "qty": qty,
            "status": "OPEN",
            "pnl": 0
        }

        log_trade(trade)
        print(f"TRADE EXECUTED: {symbol} {side} {qty}")

    except Exception as e:
        print("Trade error:", e)

# ================= MAIN =================
def run():
    while True:
        try:
            results = []

            for s in SYMBOLS:
                r = analyze(s)
                if r:
                    results.append(r)
                time.sleep(1)

            if not results:
                continue

            best = max(results, key=lambda x: x["confidence"])

            balance = exchange.fetch_balance()['total']['USDT']

            if best["confidence"] >= 70:
                execute_trade(best, balance)

            dashboard = {
                "status": "ACTIVE",
                "time": datetime.now().strftime('%H:%M:%S'),
                "balance": balance,
                "results": results,
                "best": best
            }

            save_dashboard(dashboard)

            time.sleep(10)

        except Exception as e:
            print("ERROR:", e)
            save_dashboard({"status": "STOPPED"})
            time.sleep(5)

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        save_dashboard({"status": "STOPPED"})