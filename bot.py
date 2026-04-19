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

session_history = []
total_session_pnl = 0.0

def get_analysis(symbol, timeframe):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=50)
        df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
        ema9 = ta.trend.ema_indicator(df['close'], 9).iloc[-1]
        ema21 = ta.trend.ema_indicator(df['close'], 21).iloc[-1]
        adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], 14).adx().iloc[-1]
        close = df['close'].iloc[-1]
        cross = "BULLISH" if ema9 > ema21 else "BEARISH"
        trend = "UP" if (close > ema9 and cross == "BULLISH") else "DOWN" if (close < ema9 and cross == "BEARISH") else "SIDE"
        return trend, round(adx, 1), cross
    except: return "SIDE", 0, "Wait"

while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt = balance['total'].get('USDT', 0.0)
        
        # ANALYSIS
        t15, a15, c15 = get_analysis(SYMBOL, '15m')
        t5, a5, c5 = get_analysis(SYMBOL, '5m')
        t1, a1, c1 = get_analysis(SYMBOL, '1m')

        # POSITION MONITOR
        in_t, pnl, side, marg = False, 0.0, None, 0.0
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_t, side = True, ("LONG" if amt > 0 else "SHORT")
                    pnl = float(pos['unrealizedProfit'])
                    marg = (abs(amt) * live_price) / int(pos['leverage'])

        # PREPARE DATA
        trade_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "wallet": usdt, "price": live_price, "total_pnl": total_session_pnl,
            "sig15": t15, "adx15": a15, "cross15": c15,
            "sig5": t5, "adx5": a5, "cross5": c5,
            "sig1": t1, "adx1": a1, "cross1": c1,
            "in_trade": in_t, "side": side, "pnl": pnl, "margin": marg,
            "history": session_history[:5]
        }
        
        with open("data.json", "w") as f:
            json.dump(trade_data, f)

        # ULTRA FAST SYNC (Sekunde 1-2 kurekodi na kupandisha)
        os.system("git add data.json && git commit -m 'sync' --quiet && git push origin master --quiet")

        # UI CMD
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON ENGINE | DAR: {trade_data['timestamp']}")
        print(f"💰 WALLET: ${usdt:.2f} | BTC: ${live_price:,.2f}")
        print("-" * 55)
        print(f"15M: {t15} | 5M: {t5} | 1M: {t1}")
        print("-" * 55)
        
        time.sleep(1) # Tunazunguka kila sekunde 1 kwa ajili ya kasi ya ajabu
    except Exception as e:
        time.sleep(2)