import ccxt
import pandas as pd
import ta
import time
import os
import json
from datetime import datetime

# ================= CONFIGURATION =================
API_KEY = 'WEKA_API_KEY_YAKO'
SECRET = 'WEKA_SECRET_YAKO'
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
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0.0)
        
        df15, df5, df1 = get_data(SYMBOL, '15m'), get_data(SYMBOL, '5m'), get_data(SYMBOL, '1m')
        
        def check_trend(df):
            if df is None: return "WAIT"
            l = df.iloc[-1]
            if l['close'] > l['ema9'] > l['ema21']: return "UP"
            if l['close'] < l['ema9'] < l['ema21']: return "DOWN"
            return "SIDE"

        t15, t5, t1 = check_trend(df15), check_trend(df5), check_trend(df1)
        adx5 = ta.trend.ADXIndicator(df5['high'], df5['low'], df5['close'], 14).adx().iloc[-1] if df5 is not None else 0

        # LOGIC YA ENTRY & REASONS
        market_status = "SCANNING"
        reason = "Wait: Trends not aligned"
        entry, tp, sl = 0, 0, 0
        
        if t15 == t1 and t15 != "SIDE":
            if adx5 > 20:
                market_status = f"🔥 {t15} SIGNAL"
                reason = f"Trend Match & ADX Strong ({adx5:.1f})"
                entry = live_price
                sl = entry * 0.99 if t15 == "UP" else entry * 1.01
                tp = entry * 1.02 if t15 == "UP" else entry * 0.98
            else:
                reason = f"Trend {t15} but ADX ({adx5:.1f}) Weak"

        # CHECK POSITIONS
        in_trade, side, pnl_pct, margin_used, current_lev = False, None, 0.0, 0.0, 20
        executed_time = "N/A"
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                current_lev = int(pos['leverage'])
                if amt != 0:
                    in_trade, side = True, ("LONG" if amt > 0 else "SHORT")
                    entry_p = float(pos['entryPrice'])
                    dist = ((live_price - entry_p) / entry_p) * 100
                    pnl_pct = dist * current_lev if side == "LONG" else -dist * current_lev
                    margin_used = (abs(amt) * live_price) / current_lev
                    executed_time = datetime.now().strftime('%H:%M:%S')

        # CMD DASHBOARD
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_balance:.2f} | LEVERAGE: {current_lev}x")
        print(f"💵 BTC PRICE: ${live_price:,.2f}")
        print("-" * 60)
        print(f"📊 TRENDS: 15M:{t15} | 5M:{t5} | 1M:{t1}")
        print(f"📈 ADX: {adx5:.1f} | REASON: {reason}")
        print("-" * 60)
        
        if in_trade:
            print(f"🔥 TRADE EXECUTED: {side} | Margin: ${margin_used:.2f} | PnL: {pnl_pct:+.2f}%")
        else:
            print(f"📡 STATUS: {market_status}")

        # SAVE DATA
        trade_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt_balance, "price": live_price, "leverage": current_lev,
            "sig15": t15, "sig5": t5, "sig1": t1, "adx": adx5,
            "status": market_status, "reason": reason,
            "in_trade": in_trade, "side": side, "pnl_pct": pnl_pct, "margin": margin_used,
            "entry": entry, "tp": tp, "sl": sl, "executed_at": executed_time
        }
        with open("data.json", "w") as f: json.dump(trade_data, f)
        
        # Pushing to Git
        if counter % 1 == 0:
            os.system("git add data.json && git commit -m 'sync' --quiet && git push origin master --quiet")
        
        counter += 1
        time.sleep(4)
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)