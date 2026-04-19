import ccxt
import pandas as pd
import ta
import time
import os
import json
from datetime import datetime

# ================= CONFIGURATION =================
API_KEY = 'WEKA_API_KEY_YAKO_HAPA'
SECRET = 'WEKA_SECRET_YAKO_HAPA'
SYMBOL = 'BTC/USDT'

exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})

def get_data(symbol, timeframe, limit=100):
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

# ================= MAIN LOOP =================
counter = 0
while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0.0)
        
        df15, df5, df1 = get_data(SYMBOL, '15m'), get_data(SYMBOL, '5m'), get_data(SYMBOL, '1m')
        sig15, sig5, sig1 = get_signal(df15), get_signal(df5), get_signal(df1)
        
        # EMA CROSSOVER LOGIC
        crossover_msg = "STABLE"
        if df5 is not None:
            if df5['ema9'].iloc[-2] <= df5['ema21'].iloc[-2] and df5['ema9'].iloc[-1] > df5['ema21'].iloc[-1]:
                crossover_msg = "🚀 BULLISH CROSS"
            elif df5['ema9'].iloc[-2] >= df5['ema21'].iloc[-2] and df5['ema9'].iloc[-1] < df5['ema21'].iloc[-1]:
                crossover_msg = "⚠️ BEARISH CROSS"

        adx5 = ta.trend.ADXIndicator(df5['high'], df5['low'], df5['close'], 14).adx().iloc[-1] if df5 is not None else 0

        # TRACK ACTIVE TRADES
        in_trade, side, active_pnl, pnl_pct, margin_used, current_lev = False, None, 0.0, 0.0, 0.0, 20
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                current_lev = int(pos['leverage'])
                if amt != 0:
                    in_trade, side = True, ("LONG" if amt > 0 else "SHORT")
                    active_pnl = float(pos['unrealizedProfit'])
                    entry = float(pos['entryPrice'])
                    dist = ((live_price - entry) / entry) * 100
                    pnl_pct = dist * current_lev if side == "LONG" else -dist * current_lev
                    margin_used = (abs(amt) * live_price) / current_lev

        # SAVE DATA FOR STREAMLIT
        trade_data = {
            "status": "RUNNING",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_balance, "price": live_price, "leverage": current_lev,
            "sig15": sig15, "sig5": sig5, "sig1": sig1, "adx": adx5,
            "crossover": crossover_msg, "in_trade": in_trade, "side": side,
            "pnl": active_pnl, "pnl_pct": pnl_pct, "margin": margin_used
        }
        with open("data.json", "w") as f:
            json.dump(trade_data, f)

        # GIT PUSH (Every 2 loops)
        if counter % 2 == 0:
            os.system("git add data.json && git commit -m 'sync' --quiet && git push origin master --quiet")

        # CMD DISPLAY
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🦅 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_balance:.2f} | PnL: {pnl_pct:+.2f}%")
        print(f"📊 TREND: 15M:{sig15} | CROSS: {crossover_msg}")
        print("-" * 50)
        
        if not in_trade and sig15 == sig1 and sig15 != "SIDE" and adx5 > 20:
             # Logic ya kufungua trade hapa
             pass

        counter += 1
        time.sleep(3)
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)