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

SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"]

TIMEFRAME = "5m"
HTF = "15m"

LEVERAGE = 5
RISK_PER_TRADE = 0.02

STOP_LOSS = 0.01
TAKE_PROFIT = 0.025
TRAILING = 0.008

COOLDOWN = 60

# ================= EXCHANGE =================

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

exchange.set_sandbox_mode(False)

# ================= MEMORY =================

MEMORY_FILE = "bot_memory.json"

def load_memory():

    if os.path.exists(MEMORY_FILE):
        return json.load(open(MEMORY_FILE))

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

    positions = exchange.fetch_positions()

    for p in positions:

        if p['symbol'] == symbol.replace("/",""):

            if float(p['contracts']) > 0:
                return True

    return False

# ================= DATA FETCH =================

def get_data(symbol,tf):

    bars = exchange.fetch_ohlcv(symbol,tf,limit=150)

    df = pd.DataFrame(bars,columns=['t','o','h','l','c','v'])

    df[['o','h','l','c','v']] = df[['o','h','l','c','v']].astype(float)

    return df

# ================= MARKET ANALYSIS =================

def analyze_market(symbol):

    df = get_data(symbol,TIMEFRAME)
    htf = get_data(symbol,HTF)

    df['ema9'] = ta.trend.ema_indicator(df['c'],9)
    df['ema21'] = ta.trend.ema_indicator(df['c'],21)

    df['rsi'] = ta.momentum.RSIIndicator(df['c'],14).rsi()
    df['adx'] = ta.trend.ADXIndicator(df['h'],df['l'],df['c'],14).adx()

    df['vol_ma'] = df['v'].rolling(20).mean()

    htf['ema50'] = ta.trend.ema_indicator(htf['c'],50)
    htf['ema200'] = ta.trend.ema_indicator(htf['c'],200)

    df = df.dropna()
    htf = htf.dropna()

    last = df.iloc[-1]
    last_htf = htf.iloc[-1]

    price = last['c']

    ema9 = last['ema9']
    ema21 = last['ema21']

    rsi = last['rsi']
    adx = last['adx']

    volume = last['v']
    vol_ma = last['vol_ma']

    htf_trend = "UP" if last_htf['ema50'] > last_htf['ema200'] else "DOWN"

    signal = "NONE"

    score = 0

    # TREND

    if ema9 > ema21 and htf_trend == "UP":
        signal = "BUY"
        score += 1

    if ema9 < ema21 and htf_trend == "DOWN":
        signal = "SELL"
        score += 1

    # MOMENTUM

    if rsi > 55 or rsi < 45:
        score += 1

    # TREND STRENGTH

    if adx > 20:
        score += 1

    # VOLUME SPIKE

    if volume > vol_ma:
        score += 1

    confidence = (score/4)*100

    return {

        "symbol":symbol,
        "price":price,
        "signal":signal,
        "confidence":confidence,
        "rsi":rsi,
        "adx":adx
    }

# ================= EXECUTE TRADE =================

def execute_trade(data):

    symbol = data["symbol"]
    signal = data["signal"]
    price = data["price"]

    balance = exchange.fetch_balance()

    usdt = balance['USDT']['free']

    risk_amount = usdt * RISK_PER_TRADE

    size = risk_amount / price

    if signal == "BUY":

        order = exchange.create_market_buy_order(symbol,size)

        sl = price*(1-STOP_LOSS)
        tp = price*(1+TAKE_PROFIT)

    else:

        order = exchange.create_market_sell_order(symbol,size)

        sl = price*(1+STOP_LOSS)
        tp = price*(1-TAKE_PROFIT)

    amount = order['amount']

    if signal == "BUY":

        exchange.create_order(
            symbol,
            'STOP_MARKET',
            'sell',
            amount,
            None,
            {'stopPrice':sl}
        )

        exchange.create_order(
            symbol,
            'TAKE_PROFIT_MARKET',
            'sell',
            amount,
            None,
            {'stopPrice':tp}
        )

    else:

        exchange.create_order(
            symbol,
            'STOP_MARKET',
            'buy',
            amount,
            None,
            {'stopPrice':sl}
        )

        exchange.create_order(
            symbol,
            'TAKE_PROFIT_MARKET',
            'buy',
            amount,
            None,
            {'stopPrice':tp}
        )

    memory["trades"] += 1
    memory["last_trade"] = symbol + " " + signal
    memory["last_trade_time"] = time.time()

# ================= DASHBOARD =================

def dashboard(results,best):

    os.system('cls' if os.name=='nt' else 'clear')

    print("==============================================================")
    print("                JASTON MASTER TRADE")
    print("        Advanced AI Futures Trading Engine")
    print("==============================================================")

    print("TIME:",datetime.now().strftime('%H:%M:%S'))

    print("--------------------------------------------------------------")

    for r in results:

        print(
        f"{r['symbol']} | {r['signal']} | "
        f"Conf {r['confidence']:.1f}% | "
        f"RSI {r['rsi']:.1f} | ADX {r['adx']:.1f}"
        )

    print("--------------------------------------------------------------")

    print("🔥 BEST MARKET:",best['symbol'])
    print("SIGNAL:",best['signal'])
    print("CONFIDENCE:",f"{best['confidence']:.1f}%")

    print("--------------------------------------------------------------")

    trades = memory["trades"]
    wins = memory["wins"]

    winrate = 0

    if trades>0:
        winrate = (wins/trades)*100

    print("📊 BOT STATISTICS")

    print("Trades:",memory["trades"])
    print("Wins:",memory["wins"])
    print("Losses:",memory["losses"])
    print("Winrate:",f"{winrate:.1f}%")
    print("PnL:",memory["pnl"])
    print("Last Trade:",memory["last_trade"])

    print("--------------------------------------------------------------")

# ================= MAIN LOOP =================

while True:

    try:

        results = []

        for s in SYMBOLS:

            data = analyze_market(s)

            results.append(data)

        best = max(results,key=lambda x:x["confidence"])

        dashboard(results,best)

        cooldown_ok = time.time() - memory["last_trade_time"] > COOLDOWN

        if best["confidence"] >= 75 and cooldown_ok:

            if not position_open(best["symbol"]):

                execute_trade(best)

        save_memory(memory)

        time.sleep(15)

    except Exception as e:

        print("ERROR:",e)

        time.sleep(10)