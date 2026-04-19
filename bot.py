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

def signal_offline():
    print("\n⚠️ BOT STOPPED. Syncing status...")
    offline_data = {"status": "STOPPED", "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    with open("data.json", "w") as f: json.dump(offline_data, f)
    # Amri rahisi ya Git isiyo na maneno mengi
    os.system("git add . && git commit -m 'offline' --quiet && git push origin master --quiet")

atexit.register(signal_offline)

# ================= MAIN LOOP =================
while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        
        usdt_total = balance['total'].get('USDT', 0.0)
        margin_balance = float(balance['info']['assets'][0]['marginBalance']) if 'info' in balance else usdt_total
        
        df15 = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', limit=50)
        df = pd.DataFrame(df15, columns=['t','o','h','l','c','v'])
        ema9 = ta.trend.ema_indicator(df['c'], 9).iloc[-1]
        ema21 = ta.trend.ema_indicator(df['c'], 21).iloc[-1]
        adx = ta.trend.ADXIndicator(df['h'], df['l'], df['c']).adx().iloc[-1]
        
        trend = "UP" if live_price > ema9 > ema21 else "DOWN" if live_price < ema9 < ema21 else "SIDE"

        in_trade, side, pnl_pct, margin_used = False, "NONE", 0.0, 0.0
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_trade, side = True, ("LONG" if amt > 0 else "SHORT")
                    entry_p = float(pos['entryPrice'])
                    lev = int(pos['leverage'])
                    dist = ((live_price - entry_p) / entry_p) * 100
                    pnl_pct = dist * lev if side == "LONG" else -dist * lev
                    margin_used = (abs(amt) * live_price) / lev

        # CMD DISPLAY (CLEAN)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_total:.2f} | MARGIN: ${margin_balance:.2f}")
        print(f"💵 BTC PRICE: ${live_price:,.2f} | ADX: {adx:.1f}")
        print("-" * 50)
        print(f"📊 TREND 15M: {trend} | STATUS: ONLINE")
        if in_trade: print(f"✅ EXECUTED: {side} | PnL: {pnl_pct:+.2f}%")
        print("-" * 50)

        # SAVE DATA (Safe format)
        data = {
            "status": "ONLINE",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_total, "margin_balance": margin_balance,
            "price": live_price, "trend": trend, "adx": adx,
            "in_trade": in_trade, "side": side, "pnl": pnl_pct, "margin_used": margin_used,
            "reason": "Scanning..."
        }
        with open("data.json", "w") as f: json.dump(data, f)
        
        os.system("git add . && git commit -m 'sync' --quiet && git push origin master --quiet")
        time.sleep(10)
    except Exception as e:
        time.sleep(5)