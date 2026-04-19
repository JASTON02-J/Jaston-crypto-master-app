import ccxt
import pandas as pd
import ta
import time
import os
from datetime import datetime

# ================= CONFIGURATION =================
API_KEY = 'dUTfsZjIuDVwHcaIAYwVEJ4n7Te8jHsEeRc2wJencEPxHC0XKygve29qOYpY1Co9'
SECRET = 'm2h1SRu4tU9wdMdDkqHVII8lpU6qtnCXvajiYOp9uUTxH6iaY37K3fujcOO6IXYh'
SYMBOL = 'BTC/USDT'
STATUS_FILE = "bot_status.txt"

exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})

# ================= RISK MANAGEMENT PARAMETERS =================
STOP_LOSS_PCT = 0.001  
TAKE_PROFIT_PCT = 0.002 

def get_dynamic_leverage(balance):
    if balance < 10: return 20 
    elif balance < 50: return 15
    else: return 10

def update_github_sync(status_text):
    try:
        with open(STATUS_FILE, "w") as f: f.write(status_text)
        # Marekebisho hapa: Tumeongeza 'master' ili kuzuia kosa la pathspec
        os.system("git add . && git commit -m 'bot sync' && git push origin master")
    except: pass

def get_data(symbol, timeframe, limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
    except Exception as e:
        print(f"⚠️ Data Error: {e}")
        return None

# ================= ANALYSIS =================
def analyze_market():
    df_15m = get_data(SYMBOL, '15m')
    if df_15m is None: return None
    
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    
    df_5m = get_data(SYMBOL, '5m')
    if df_5m is None: return None
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    
    df_1m = get_data(SYMBOL, '1m')
    if df_1m is None: return None
    price = df_1m['close'].iloc[-1]
    ema9_1m = ta.trend.ema_indicator(df_1m['close'], 9).iloc[-1]
    ema21_1m = ta.trend.ema_indicator(df_1m['close'], 21).iloc[-1] 

    trend_15m = "SIDEWAYS" if is_sideways else ("UP" if price > ema9_15m else "DOWN")
    
    return {
        "price": price, "trend_15m": trend_15m, "adx_5m": adx_5m,
        "ema9_1m": ema9_1m, "ema21_1m": ema21_1m
    }

# ================= MAIN LOOP =================
print("🚀 JASTON MASTER BOT: RISK-REWARD MODE ACTIVE...")
update_github_sync("LIVE_TRADING")

m = {"price": 0, "trend_15m": "SCANNING", "adx_5m": 0, "ema21_1m": 0}
counter = 0

while True:
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0.0)
        
        in_trade = False
        active_pnl = 0.0
        side = None
        amt = 0
        
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_trade = True
                    side = "LONG" if amt > 0 else "SHORT"
                    active_pnl = float(pos['unrealizedProfit'])

        if counter % 5 == 0:
            analysis = analyze_market()
            if analysis: m = analysis

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER BOT | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_balance:.2f} | PnL: {active_pnl:.4f} USDT")
        print(f"🔍 15M: {m['trend_15m']} | ADX: {m['adx_5m']:.1f}")
        print(f"--------------------------------------------------")

        if in_trade:
            if active_pnl <= -0.20:
                print("⚠️ STOP LOSS REACHED ($0.20). Closing...")
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
            elif side == "LONG" and live_price < m['ema21_1m']:
                print("🔴 EMA 21 Cross (LONG Exit). Closing...")
                exchange.create_market_order(SYMBOL, 'sell', abs(amt))
            elif side == "SHORT" and live_price > m['ema21_1m']:
                print("🟢 EMA 21 Cross (SHORT Exit). Closing...")
                exchange.create_market_order(SYMBOL, 'buy', abs(amt))
            elif active_pnl >= 0.40:
                print("💰 TAKE PROFIT REACHED ($0.40). Closing...")
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))

        elif m['trend_15m'] != "SIDEWAYS" and m['adx_5m'] > 20:
            lev = get_dynamic_leverage(usdt_balance)
            qty = (usdt_balance * 0.5 * lev) / live_price
            if m['trend_15m'] == "UP" and live_price > m['ema9_1m']:
                exchange.set_leverage(lev, SYMBOL)
                exchange.create_market_order(SYMBOL, 'buy', qty)
                print("🚀 LONG ORDER PLACED")
            elif m['trend_15m'] == "DOWN" and live_price < m['ema9_1m']:
                exchange.set_leverage(lev, SYMBOL)
                exchange.create_market_order(SYMBOL, 'sell', qty)
                print("📉 SHORT ORDER PLACED")

        counter += 1
        time.sleep(2)

    except Exception as e:
        print(f"❌ Loop Error: {e}")
        time.sleep(10) # Subiri kidogo kama kuna kosa la mtandao