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

# ================= MAIN LOOP =================
counter = 0
while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        
        # Pata Balance za Wallet na Margin
        balance = exchange.fetch_balance()
        usdt_info = balance['total'].get('USDT', 0.0)
        # Margin Balance (Pesa halisi inayoweza kutumika kufungua trade mpya)
        margin_balance = float(balance['info']['assets'][0]['marginBalance']) if 'info' in balance else usdt_info
        
        df15, df5, df1 = get_data(SYMBOL, '15m'), get_data(SYMBOL, '5m'), get_data(SYMBOL, '1m')
        
        def check_trend(df):
            if df is None: return "WAIT"
            l = df.iloc[-1]
            if l['close'] > l['ema9'] > l['ema21']: return "UP"
            if l['close'] < l['ema9'] < l['ema21']: return "DOWN"
            return "SIDE"

        t15, t5, t1 = check_trend(df15), check_trend(df5), check_trend(df1)
        adx5 = ta.trend.ADXIndicator(df5['high'], df5['low'], df5['close'], 14).adx().iloc[-1] if df5 is not None else 0

        # LOGIC YA POSITION NA PNL
        in_trade, side, pnl_pct, margin_used, current_lev = False, None, 0.0, 0.0, 20
        entry_price = 0.0
        
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                current_lev = int(pos['leverage'])
                if amt != 0:
                    in_trade, side = True, ("LONG" if amt > 0 else "SHORT")
                    entry_price = float(pos['entryPrice'])
                    dist = ((live_price - entry_price) / entry_price) * 100
                    pnl_pct = dist * current_lev if side == "LONG" else -dist * current_lev
                    margin_used = (abs(amt) * live_price) / current_lev

        # DASHBOARD YA CMD
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_info:.2f} | MARGIN BAL: ${margin_balance:.2f}")
        print(f"💵 BTC PRICE: ${live_price:,.2f} | LEV: {current_lev}x")
        print("-" * 60)
        print(f"📊 TRENDS: 15M: {t15} | 5M: {t5} | 1M: {t1} | ADX: {adx5:.1f}")
        print("-" * 60)
        
        if in_trade:
            print(f"✅ TRADE EXECUTED: {side}")
            print(f"   ENTRY: ${entry_price:,.2f} | PnL: {pnl_pct:+.2f}%")
        else:
            print("📡 STATUS: SCANNING MARKET...")

        # SAVE DATA KWA AJILI YA APP
        trade_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_info, "margin_balance": margin_balance, 
            "price": live_price, "leverage": current_lev,
            "sig15": t15, "sig5": t5, "sig1": t1, "adx": adx5,
            "in_trade": in_trade, "side": side, "pnl_pct": pnl_pct, "margin": margin_used
        }
        with open("data.json", "w") as f: json.dump(trade_data, f)
        
        # Git Sync (Kila mzunguko 1)
        if counter % 1 == 0:
            os.system("git add data.json && git commit -m 'sync' --quiet && git push origin master --quiet")
        
        counter += 1
        time.sleep(3)
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)