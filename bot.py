import ccxt
import pandas as pd
import ta
import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ================= CONFIG =================

API_KEY = os.getenv("OGewM9ZghugzimAbvvkwC3DMUri19S1mAUECkya5XHsc4D8gw4AfUIuvqG4tOe9R")
SECRET = os.getenv("PxXWbVdrlCUfykBSlAd3XO5AhqfCi1OCmLi3gQMoBfxu97CxDhxKc042NQWRLKZw")

SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"]

TIMEFRAME = "5m"
HTF = "15m"

RISK_PER_TRADE = 0.02
STOP_LOSS = 0.01
TAKE_PROFIT = 0.025
COOLDOWN = 60

MEMORY_FILE = "bot_memory.json"
HISTORY_FILE = "trade_history.json"

# ================= EXCHANGE =================

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": SECRET,
    "enableRateLimit": True,
    "options": {"defaultType": "future"}
})

exchange.load_markets()

# ================= MEMORY =================

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            return json.load(open(MEMORY_FILE))
        except:
            pass
    return {"trades":0,"wins":0,"losses":0,"pnl":0,"last_trade":"NONE","last_trade_time":0}

def save_memory(data):
    with open(MEMORY_FILE,"w") as f:
        json.dump(data,f)

memory = load_memory()

# ================= HISTORY =================

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            return json.load(open(HISTORY_FILE))
        except:
            pass
    return []

def save_history(data):
    with open(HISTORY_FILE,"w") as f:
        json.dump(data,f)

history = load_history()

# ================= WALLET =================

def get_wallet_info():
    try:
        balance = exchange.fetch_balance()
        wallet = balance["USDT"]["free"]
        margin = balance["USDT"].get("used",0)
        return wallet, margin
    except:
        return 0,0

# ================= DATA =================

def get_data(symbol,tf):
    try:
        bars = exchange.fetch_ohlcv(symbol,tf,limit=200)
        df = pd.DataFrame(bars,columns=["t","o","h","l","c","v"])
        df[["o","h","l","c","v"]] = df[["o","h","l","c","v"]].astype(float)
        return df
    except:
        return None

# ================= VOLATILITY ENGINE =================

def calculate_volatility(df):
    df["return"] = df["c"].pct_change()
    vol = df["return"].rolling(14).std().iloc[-1]
    return abs(vol*100) if not pd.isna(vol) else 0


def classify_volatility(vol):

    if vol < 0.2:
        return "LOW", "SAFE"
    elif vol < 0.5:
        return "NORMAL", "SAFE"
    elif vol < 1.0:
        return "MEDIUM", "CAUTION"
    elif vol < 2.0:
        return "HIGH", "RISKY"
    else:
        return "EXTREME", "DANGER"

# ================= LEVERAGE SYSTEM =================

def get_leverage_and_mode(conf, vol):

    leverage = 5
    mode = "cross"

    if conf >= 90:
        leverage = 12 if vol < 0.3 else 7
        mode = "isolated"
    elif conf >= 80:
        leverage = 10 if vol < 0.3 else 5
        mode = "isolated"
    else:
        leverage = 5
        mode = "cross"

    return leverage, mode

# ================= ANALYSIS =================

def analyze_market(symbol):

    df = get_data(symbol,TIMEFRAME)
    htf = get_data(symbol,HTF)

    if df is None or htf is None:
        return None

    df["ema9"] = ta.trend.ema_indicator(df["c"],9)
    df["ema21"] = ta.trend.ema_indicator(df["c"],21)
    df["rsi"] = ta.momentum.RSIIndicator(df["c"],14).rsi()
    df["adx"] = ta.trend.ADXIndicator(df["h"],df["l"],df["c"],14).adx()
    df["vol_ma"] = df["v"].rolling(20).mean()

    htf["ema50"] = ta.trend.ema_indicator(htf["c"],50)
    htf["ema200"] = ta.trend.ema_indicator(htf["c"],200)

    df = df.dropna()
    htf = htf.dropna()

    last = df.iloc[-1]
    last_htf = htf.iloc[-1]

    price = float(last["c"])
    rsi = float(last["rsi"])
    adx = float(last["adx"])
    volume = float(last["v"])
    vol_ma = float(last["vol_ma"])

    trend = "UP" if last_htf["ema50"] > last_htf["ema200"] else "DOWN"

    signal = "NONE"
    score = 0

    if last["ema9"] > last["ema21"] and trend == "UP":
        signal = "BUY"
        score += 2
    elif last["ema9"] < last["ema21"] and trend == "DOWN":
        signal = "SELL"
        score += 2

    if 50 < rsi < 70:
        score += 1
    if adx > 20:
        score += 2
    if volume > vol_ma:
        score += 1

    confidence = min((score/6)*100,100)

    volatility = calculate_volatility(df)
    volatility_label, risk_level = classify_volatility(volatility)

    leverage, mode = get_leverage_and_mode(confidence, volatility)

    return {
        "symbol":symbol,
        "price":price,
        "signal":signal,
        "confidence":confidence,
        "rsi":rsi,
        "adx":adx,
        "volatility":volatility,
        "volatility_label":volatility_label,
        "risk_level":risk_level,
        "leverage":leverage,
        "mode":mode
    }

# ================= LIVE POSITIONS =================

def get_live_positions():

    try:
        positions = exchange.fetch_positions()
        live = []

        for p in positions:
            size = float(p.get("contracts") or 0)
            if size == 0:
                continue

            live.append({
                "symbol": p["symbol"],
                "entry": float(p.get("entryPrice") or 0),
                "current": float(p.get("markPrice") or 0),
                "pnl": float(p.get("unrealizedPnl") or 0),
                "leverage": float(p.get("leverage") or 0),
                "liquidation": p.get("liquidationPrice","N/A")
            })

        return live

    except:
        return []

# ================= DASHBOARD (UNCHANGED) =================

def dashboard(results,best):

    wallet, margin = get_wallet_info()

    os.system("cls" if os.name=="nt" else "clear")

    print("===================================================")
    print("              JASTON MASTER TRADE")
    print("        Advanced AI Futures Trading Engine")
    print("===================================================")

    print("TIME:",datetime.now().strftime("%H:%M:%S"))

    for r in results:
        print(f"{r['symbol']} | {r['signal']} | Conf {r['confidence']:.1f}% | RSI {r['rsi']:.1f} | ADX {r['adx']:.1f}")

    print("---------------------------------------------------")
    print("🔥 BEST:",best["symbol"],best["signal"],best["confidence"])
    print("💰 Wallet:",wallet,"USDT")
    print("⚡ Leverage:",best["leverage"])
    print("🧭 Mode:",best["mode"])

    # ================= ONLY ADDITIONS BELOW =================

    print("---------------------------------------------------")
    print("🌊 VOLATILITY:", f"{best['volatility']:.2f}%")
    print("📊 STATE:", best["volatility_label"])
    print("⚠️ RISK:", best["risk_level"])

    print("---------------------------------------------------")
    print("📡 LIVE POSITIONS")

    live = get_live_positions()

    for p in live:
        print(p["symbol"],p["pnl"],p["leverage"],p["entry"],p["current"])

    print("---------------------------------------------------")
    print("📜 CLOSED TRADES")

    closed = [h for h in history if h.get("status") == "CLOSED"]

    for c in closed[-5:]:
        print(c["symbol"],c["side"],c["pnl"])

# ================= MAIN LOOP =================

while True:

    results = []

    for s in SYMBOLS:
        data = analyze_market(s)
        if data:
            results.append(data)

    best = max(results,key=lambda x:x["confidence"])

    dashboard(results,best)

    time.sleep(15)