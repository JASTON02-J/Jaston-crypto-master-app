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
    'apiKey': API_KEY, 'secret': SECRET,
    'enableRateLimit': True, 'options': {'defaultType': 'future'}
})

# Masuala ya History & PnL
session_history = []
total_session_pnl = 0.0
last_position_side = None

def get_data(symbol, timeframe='15m', limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
        df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
        return df
    except: return None

def get_signal(df):
    if df is None: return "SIDE"
    last = df.iloc[-1]
    if last['close'] > last['ema9'] > last['ema21']: return "UP"
    if last['close'] < last['ema9'] < last['ema21']: return "DOWN"
    return "SIDE"

counter = 0
os.system('cls' if os.name == 'nt' else 'clear')

while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0.0)
        
        df15, df1 = get_data(SYMBOL, '15m'), get_data(SYMBOL, '1m')
        sig15, sig1 = get_signal(df15), get_signal(df1)

        # Position Monitoring
        in_trade, active_pnl, side, margin_used = False, 0.0, None, 0.0
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_trade, side = True, ("LONG" if amt > 0 else "SHORT")
                    active_pnl = float(pos['unrealizedProfit'])
                    margin_used = (abs(amt) * live_price) / int(pos['leverage'])
                    last_position_side = side

        # Log History if trade closes (Simple Logic)
        if not in_trade and last_position_side is not None:
            # Hapa tunachukulia trade imefungwa
            trade_record = {
                "Time": datetime.now().strftime('%H:%M:%S'),
                "Side": last_position_side,
                "Result": "CLOSED"
            }
            session_history.insert(0, trade_record)
            last_position_side = None

        # PREPARE DATA FOR APP
        trade_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_balance,
            "price": live_price,
            "sig15": sig15,
            "sig1": sig1,
            "in_trade": in_trade,
            "side": side,
            "pnl": active_pnl,
            "margin": margin_used,
            "total_pnl": total_session_pnl,
            "history": session_history[:5] # Tuma trade 5 za mwisho tu
        }
        
        with open("data.json", "w") as f:
            json.dump(trade_data, f)

        # FAST SYNC TO GITHUB (Every 3 loops ~ 10 seconds)
        if counter % 3 == 0:
            os.system("git add data.json && git commit -m 'sync' --quiet && git push origin master --quiet")

        # CMD DASHBOARD
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_balance:.2f} | BTC: ${live_price:,.2f}")
        print("-" * 50)
        print(f"📊 ANALYSIS: 15M:{sig15} | 1M:{sig1}")
        if in_trade:
            print(f"🔥 ACTIVE: {side} | PnL: {active_pnl:+.4f}")
        else:
            print("📡 STATUS: SCANNING...")

        counter += 1
        time.sleep(3)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)