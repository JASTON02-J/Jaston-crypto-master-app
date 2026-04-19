import ccxt
import pandas as pd
import ta
import time
import os
import json
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

def save_history(side, entry, pnl):
    history_file = 'history.json'
    now = datetime.now()
    new_entry = {
        "Date": now.strftime("%Y-%m-%d"),
        "Time": now.strftime("%H:%M:%S"),
        "Side": side,
        "Entry": f"${entry:,.2f}",
        "PnL": f"{pnl:+.2f}%"
    }
    
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except: history = []
    
    history.append(new_entry)
    with open(history_file, 'w') as f:
        json.dump(history[-10:], f) # Tunatunza trades 10 tu za mwisho

# ================= MAIN LOOP =================
counter = 0
last_trade_state = False # Kujua kama trade imefungwa

while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        
        # Pata Wallet na Margin Balance
        usdt_total = balance['total'].get('USDT', 0.0)
        margin_balance = float(balance['info']['assets'][0]['marginBalance']) if 'info' in balance else usdt_total
        
        # Uchambuzi
        df15 = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', limit=50)
        df15 = pd.DataFrame(df15, columns=['t','o','h','l','c','v'])
        ema9 = ta.trend.ema_indicator(df15['c'], 9).iloc[-1]
        ema21 = ta.trend.ema_indicator(df15['c'], 21).iloc[-1]
        adx = ta.trend.ADXIndicator(df15['h'], df15['l'], df15['c']).adx().iloc[-1]
        
        # Trends logic
        trend = "UP" if live_price > ema9 > ema21 else "DOWN" if live_price < ema9 < ema21 else "SIDE"

        # Position Info
        in_trade, side, pnl_pct, margin_used, entry_p = False, "NONE", 0.0, 0.0, 0.0
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

        # Record History trade ikifungwa
        if last_trade_state == True and in_trade == False:
             # Hapa unaweza kuongeza logic ya kurekodi trade iliyopita
             pass
        last_trade_state = in_trade

        # CMD DISPLAY (Dashboard yako ya sasa)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_total:.2f} | MARGIN: ${margin_balance:.2f}")
        print(f"💵 BTC PRICE: ${live_price:,.2f} | ADX: {adx:.1f}")
        print("-" * 60)
        print(f"📊 TREND 15M: {trend} | STATUS: {'IN TRADE' if in_trade else 'SCANNING'}")
        
        if in_trade:
            print(f"✅ TRADE EXECUTED: {side} | ENTRY: {entry_p:,.2f}")
            print(f"📈 LIVE PnL: {pnl_pct:+.2f}% | MARGIN USED: ${margin_used:.2f}")
        else:
            print("💡 REASON: Waiting for signal alignment...")
        print("-" * 60)

        # SAVE DATA FOR APP
        data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_total, "margin_balance": margin_balance,
            "price": live_price, "trend": trend, "adx": adx,
            "in_trade": in_trade, "side": side, "pnl": pnl_pct, "margin_used": margin_used
        }
        with open("data.json", "w") as f: json.dump(data, f)
        
        # PUSH TO GIT
        os.system("git add data.json history.json && git commit -m 'sync' --quiet && git push origin master --quiet")
        
        counter += 1
        time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)