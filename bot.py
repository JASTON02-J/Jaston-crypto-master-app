import ccxt
import pandas as pd
import ta
import os
import time
import json
from datetime import datetime

# ================= CONFIG =================

API_KEY = os.getenv("dUTfsZjIuDVwHcaIAYwVEJ4n7Te8jHsEeRc2wJencEPxHC0XKygve29qOYpY1Co9")
SECRET = os.getenv("m2h1SRu4tU9wdMdDkqHVII8lpU6qtnCXvajiYOp9uUTxH6iaY37K3fujcOO6IXYh")

SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"]

TIMEFRAME = "5m"
HTF = "15m"

RISK_PER_TRADE = 0.02
STOP_LOSS = 0.01
TAKE_PROFIT = 0.025
COOLDOWN = 60

MEMORY_FILE = "bot_memory.json"

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

    return {
        "trades":0,
        "wins":0,
        "losses":0,
        "pnl":0,
        "last_trade":"NONE",
        "last_trade_time":0
    }

def save_memory(data):
    with open(MEMORY_FILE,"w") as f:
        json.dump(data,f)

memory = load_memory()

# ================= POSITION CHECK =================

def position_open(symbol):
    try:
        positions = exchange.fetch_positions()
        for p in positions:
            if p["symbol"] == symbol.replace("/",""):
                if float(p.get("contracts",0)) > 0:
                    return True
    except:
        pass
    return False

# ================= BALANCE =================

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

# ================= ANALYSIS =================

def analyze_market(symbol):

    try:

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
        ema9 = float(last["ema9"])
        ema21 = float(last["ema21"])
        rsi = float(last["rsi"])
        adx = float(last["adx"])
        volume = float(last["v"])
        vol_ma = float(last["vol_ma"])

        trend = "UP" if last_htf["ema50"] > last_htf["ema200"] else "DOWN"

        signal = "NONE"
        score = 0

        if ema9 > ema21 and trend == "UP":
            signal = "BUY"
            score += 2

        elif ema9 < ema21 and trend == "DOWN":
            signal = "SELL"
            score += 2

        if 50 < rsi < 70:
            score += 1

        if adx > 20:
            score += 2

        if volume > vol_ma:
            score += 1

        confidence = min((score/6)*100,100)

        return {
            "symbol":symbol,
            "price":price,
            "signal":signal,
            "confidence":confidence,
            "rsi":rsi,
            "adx":adx
        }

    except:
        return None

# ================= TRAILING STOP =================

def create_trailing_stop(symbol, side, size, callback=0.5):

    try:
        params = {
            "callbackRate": callback,
            "reduceOnly": True
        }

        if side == "BUY":
            return exchange.create_order(symbol,"TRAILING_STOP_MARKET","sell",size,None,params)

        else:
            return exchange.create_order(symbol,"TRAILING_STOP_MARKET","buy",size,None,params)

    except Exception as e:
        print("TRAILING ERROR:",e)

# ================= EXECUTE TRADE =================

def execute_trade(data):

    try:

        symbol = data["symbol"]
        signal = data["signal"]
        price = data["price"]

        wallet, margin = get_wallet_info()

        if wallet < 10:
            return

        risk_amount = wallet * RISK_PER_TRADE
        size = risk_amount / price

        if signal == "BUY":

            exchange.create_market_buy_order(symbol,size)

            sl = price * (1 - STOP_LOSS)
            exchange.create_order(symbol,"STOP_MARKET","sell",size,None,{"stopPrice":sl,"reduceOnly":True})

            create_trailing_stop(symbol,"BUY",size,0.5)

        else:

            exchange.create_market_sell_order(symbol,size)

            sl = price * (1 + STOP_LOSS)
            exchange.create_order(symbol,"STOP_MARKET","buy",size,None,{"stopPrice":sl,"reduceOnly":True})

            create_trailing_stop(symbol,"SELL",size,0.5)

        memory["trades"] += 1
        memory["last_trade"] = symbol + " " + signal
        memory["last_trade_time"] = time.time()

    except Exception as e:
        print("TRADE ERROR:",e)

# ================= UPDATE PNL =================

def update_pnl():

    try:
        positions = exchange.fetch_positions()

        total_pnl = 0

        for p in positions:

            pnl = float(p.get("unrealizedPnl",0))
            total_pnl += pnl

        memory["pnl"] = total_pnl

    except:
        pass

# ================= DASHBOARD =================

def dashboard(results,best):

    wallet, margin = get_wallet_info()

    os.system("cls" if os.name=="nt" else "clear")

    print("===================================================")
    print("              JASTON MASTER TRADE")
    print("        Advanced AI Futures Trading Engine")
    print("===================================================")

    print("TIME:",datetime.now().strftime("%H:%M:%S"))
    print("---------------------------------------------------")

    for r in results:
        print(f"{r['symbol']} | {r['signal']} | Conf {r['confidence']:.1f}% | RSI {r['rsi']:.1f} | ADX {r['adx']:.1f}")

    print("---------------------------------------------------")

    print("🔥 BEST MARKET:",best["symbol"])
    print("SIGNAL:",best["signal"])
    print("CONFIDENCE:",f"{best['confidence']:.1f}%")

    print("---------------------------------------------------")

    trades = memory["trades"]
    wins = memory["wins"]
    winrate = (wins/trades)*100 if trades>0 else 0

    print("📊 BOT STATISTICS")
    print("Trades:",memory["trades"])
    print("Wins:",memory["wins"])
    print("Losses:",memory["losses"])
    print("Winrate:",f"{winrate:.1f}%")
    print("PnL:",round(memory["pnl"],2))
    print("Last Trade:",memory["last_trade"])

    print("---------------------------------------------------")

    print("💰 WALLET INFO")
    print("Wallet Balance:",round(wallet,2),"USDT")
    print("Margin Used:",round(margin,2),"USDT")

    print("---------------------------------------------------")

# ================= MAIN LOOP =================

while True:

    try:

        results = []

        for s in SYMBOLS:

            data = analyze_market(s)

            if data:
                results.append(data)

        if not results:
            time.sleep(10)
            continue

        best = max(results,key=lambda x:x["confidence"])

        dashboard(results,best)

        cooldown_ok = time.time() - memory["last_trade_time"] > COOLDOWN

        if best["confidence"] >= 75 and cooldown_ok:

            if not position_open(best["symbol"]):
                execute_trade(best)

        update_pnl()
        save_memory(memory)

        time.sleep(15)

    except Exception as e:
        print("MAIN LOOP ERROR:",e)
        time.sleep(10)