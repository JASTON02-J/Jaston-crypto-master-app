import ccxt
import pandas as pd
import ta
import time
import os
import json
import atexit
from datetime import datetime

# ================= CONFIGURATION =================
API_KEY = 'dUTfsZjIuDVwHcaIAYwVEJ4n7Te8jHsEeRc2wJencEPxHC0XKygve29qOYpY1Co9'
SECRET = 'm2h1SRu4tU9wdMdDkqHVII8lpU6qtnCXvajiYOp9uUTxH6iaY37K3fujcOO6IXYh'
SYMBOL = 'BTC/USDT'

exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})

def get_trend(timeframe):
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, timeframe=timeframe, limit=50)
        df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
        ema9 = ta.trend.ema_indicator(df['c'], 9).iloc[-1]
        ema21 = ta.trend.ema_indicator(df['c'], 21).iloc[-1]
        price = df['c'].iloc[-1]
        return "UP" if price > ema9 > ema21 else "DOWN" if price < ema9 < ema21 else "SIDE"
    except: return "N/A"

def signal_stop():
    # Inatuma STOPPED bila maneno mengi
    try:
        data = {"status": "STOPPED", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        with open("data.json", "w") as f: json.dump(data, f)
        os.system("git add . && git commit -m 'stop' --quiet && git push origin master --quiet")
    except: pass

atexit.register(signal_stop)

# ================= MAIN LOOP =================
while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        
        # Balance & Indicators
        usdt_total = balance['total'].get('USDT', 0.0)
        margin_balance = float(balance['info']['assets'][0]['marginBalance']) if 'info' in balance else usdt_total
        
        t15 = get_trend('15m')
        t5 = get_trend('5m')
        t1 = get_trend('1m')
        
        # Logic ya Reason
        reason = "Waiting for EMA alignment"
        if t15 == t5 == t1 != "SIDE":
            reason = f"Ready for {t15} Signal"

        # Position Tracking
        in_trade, side, pnl_pct = False, "NONE", 0.0
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', '') and float(pos['positionAmt']) != 0:
                in_trade = True
                side = "LONG" if float(pos['positionAmt']) > 0 else "SHORT"
                entry = float(pos['entryPrice'])
                lev = int(pos['leverage'])
                dist = ((live_price - entry) / entry) * 100
                pnl_pct = dist * lev if side == "LONG" else -dist * lev
                reason = f"Executing {side} trade"

        # CMD DASHBOARD
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_total:.2f} | MARGIN: ${margin_balance:.2f}")
        print(f"💵 BTC PRICE: ${live_price:,.2f}")
        print("-" * 50)
        print(f"📊 TREND 15M: {t15}")
        print(f"📊 TREND 05M: {t5}")
        print(f"📊 TREND 01M: {t1}")
        print("-" * 50)
        print(f"💡 STATUS: {'IN TRADE' if in_trade else 'SCANNING'}")
        print(f"📝 REASON: {reason}")
        if in_trade: print(f"📈 LIVE PnL: {pnl_pct:+.2f}%")
        print("-" * 50)

        # SAVE & SYNC
        data = {
            "status": "ONLINE", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_total, "margin_balance": margin_balance, "price": live_price,
            "t15": t15, "t5": t5, "t1": t1, "in_trade": in_trade, "side": side, 
            "pnl": pnl_pct, "reason": reason
        }
        with open("data.json", "w") as f: json.dump(data, f)
        os.system("git add . && git commit -m 'sync' --quiet && git push origin master --quiet")
        
        time.sleep(10)
    except Exception:
        time.sleep(10)