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

MAX_DRAWDOWN = 10
ALERT_LEVELS = [5,7,9]

bot_running = True
initial_balance = None
alerted_levels = set()

# ================= EXCHANGE =================

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": SECRET,
    "enableRateLimit": True,
    "options": {"defaultType": "future"}
})

exchange.load_markets()

# ================= WALLET =================

def get_wallet():
    b = exchange.fetch_balance()
    return b["USDT"]["total"], b["USDT"]["free"]

# ================= RISK ENGINE =================

def drawdown(current):
    if initial_balance == 0:
        return 0
    return ((initial_balance - current)/initial_balance)*100

def alert(msg):
    print("ALERT:", msg)

def close_all():
    try:
        for p in exchange.fetch_positions():
            size = float(p.get("contracts") or 0)
            if size == 0:
                continue
            side = "sell" if size > 0 else "buy"
            exchange.create_market_order(p["symbol"], side, abs(size))
    except:
        pass

def shutdown():
    global bot_running
    alert("🛑 10% loss reached - bot stopped")
    close_all()
    bot_running = False

# ================= MIN TRADE =================

def min_trade(symbol):
    try:
        m = exchange.market(symbol)
        base = m['limits']['cost']['min'] or 5
        fee = m.get('taker',0.0004)
        return round(base*(1+fee*2),2)
    except:
        return 5

# ================= LIQUIDATION RISK ENGINE =================

def liquidation_risk(vol, lev):

    # proxy model: high leverage + high volatility = danger
    risk = vol * lev

    if risk < 5:
        return "LOW"
    elif risk < 10:
        return "MEDIUM"
    elif risk < 15:
        return "HIGH"
    else:
        return "DANGER"

# ================= SMART LEVERAGE =================

def smart_leverage(conf, vol, balance):

    base = 5

    if conf >= 90:
        base = 12
    elif conf >= 80:
        base = 10

    # volatility penalty
    if vol > 1.5:
        base -= 4
    elif vol > 1.0:
        base -= 2

    # balance protection
    if balance < 50:
        base = min(base,5)
    elif balance < 200:
        base = min(base,7)
    elif balance < 1000:
        base = min(base,10)

    return max(3, base)

# ================= DATA =================

def data(symbol):
    bars = exchange.fetch_ohlcv(symbol,TIMEFRAME,limit=200)
    df = pd.DataFrame(bars,columns=["t","o","h","l","c","v"])
    df[["o","h","l","c","v"]] = df[["o","h","l","c","v"]].astype(float)
    return df

# ================= ANALYSIS =================

def analyze(symbol):

    df = data(symbol)
    htf = data(symbol)

    df["ema9"] = ta.trend.ema_indicator(df["c"],9)
    df["ema21"] = ta.trend.ema_indicator(df["c"],21)
    df["rsi"] = ta.momentum.RSIIndicator(df["c"],14).rsi()
    df["adx"] = ta.trend.ADXIndicator(df["h"],df["l"],df["c"],14).adx()

    df = df.dropna()

    last = df.iloc[-1]

    signal = "NONE"
    score = 0

    if last["ema9"] > last["ema21"]:
        signal="BUY"; score+=2
    else:
        signal="SELL"; score+=2

    if 50 < last["rsi"] < 70: score+=1
    if last["adx"] > 20: score+=2

    conf = min(score/6*100,100)

    vol = abs(df["c"].pct_change().rolling(14).std().iloc[-1]*100)

    balance,_ = get_wallet()

    lev = smart_leverage(conf,vol,balance)

    risk_level = liquidation_risk(vol,lev)

    if risk_level == "DANGER":
        lev = 3  # force safe mode

    return {
        "symbol":symbol,
        "signal":signal,
        "confidence":conf,
        "vol":vol,
        "leverage":lev,
        "risk":risk_level,
        "price":float(last["c"])
    }

# ================= DASHBOARD =================

def dashboard(results,best):

    total,_ = get_wallet()

    os.system("cls" if os.name=="nt" else "clear")

    print("===================================================")
    print("              JASTON MASTER TRADE")
    print("===================================================")

    print("TIME:",datetime.now().strftime("%H:%M:%S"))

    for r in results:
        print(f"{r['symbol']} | {r['signal']} | Conf {r['confidence']:.1f}%")

    print("---------------------------------------------------")
    print("🔥 BEST:",best["symbol"])
    print("⚡ Leverage:",best["leverage"])

    print("🛡️ Risk Level:",best["risk"])
    print("📉 Volatility:",best["vol"])

    print("💰 Wallet:",total)

    print("---------------------------------------------------")
    print("📊 MIN TRADE")

    for s in SYMBOLS:
        print(s,"→",min_trade(s))

# ================= INIT =================

initial_balance,_ = get_wallet()

# ================= LOOP =================

while bot_running:

    balance,_ = get_wallet()

    dd = drawdown(balance)

    if dd >= MAX_DRAWDOWN:
        shutdown()
        break

    results = []

    for s in SYMBOLS:
        r = analyze(s)
        results.append(r)

    best = max(results,key=lambda x:x["confidence"])

    dashboard(results,best)

    time.sleep(15)