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
os.system('cls' if os.name == 'nt' else 'clear')

while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0.0)
        
        df15, df5, df1 = get_data(SYMBOL, '15m'), get_data(SYMBOL, '5m'), get_data(SYMBOL, '1m')
        sig15, sig5, sig1 = get_signal(df15), get_signal(df5), get_signal(df1)
        adx5 = ta.trend.ADXIndicator(df5['high'], df5['low'], df5['close'], 14).adx().iloc[-1] if df5 is not None else 0

        in_trade, active_pnl, side, margin_used, current_lev = False, 0.0, None, 0.0, 20
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                current_lev = int(pos['leverage'])
                if amt != 0:
                    in_trade, side = True, ("LONG" if amt > 0 else "SHORT")
                    active_pnl = float(pos['unrealizedProfit'])
                    margin_used = (abs(amt) * live_price) / current_lev

        # FAST SYNC DATA (Every loop)
        trade_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_balance, "price": live_price, "leverage": current_lev,
            "sig15": sig15, "sig5": sig5, "sig1": sig1, "adx": adx5,
            "in_trade": in_trade, "side": side, "pnl": active_pnl, "margin": margin_used,
            "history": [] 
        }
        with open("data.json", "w") as f:
            json.dump(trade_data, f)

        # GIT SYNC (Every 2 loops ~ 6 seconds)
        if counter % 2 == 0:
            os.system("git add data.json && git commit -m 'sync' --quiet && git push origin master --quiet")

        # CMD DASHBOARD
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_balance:.2f} | LEVERAGE: {current_lev}x")
        print(f"💵 BTC PRICE: ${live_price:,.2f}")
        print("-" * 50)
        print(f"📊 TRENDS: 15M:{sig15} | 5M:{sig5} | 1M:{sig1} | ADX:{adx5:.1f}")
        
        if in_trade:
            print(f"🔥 ACTIVE: {side} | Margin: ${margin_used:.2f} | PnL: {active_pnl:+.4f}")
        else:
            print("📡 STATUS: SCANNING...")
            if sig15 == sig1 and sig15 != "SIDE" and adx5 > 20:
                if usdt_balance >= 10.0:
                    qty = max(0.001, (usdt_balance * 0.5 * current_lev) / live_price)
                    exchange.create_market_order(SYMBOL, 'buy' if sig15 == "UP" else 'sell', qty)

        counter += 1
        time.sleep(3)
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)