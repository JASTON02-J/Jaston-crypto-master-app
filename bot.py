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
DATA_FILE = "trade_data.json"
ACTIVE_FILE = "active_trade.json"
STATUS_FILE = "bot_status.txt"

exchange = ccxt.binance({
    'apiKey': API_KEY, 'secret': SECRET,
    'enableRateLimit': True, 'options': {'defaultType': 'future'}
})

# ================= HELPERS =================
def log_activity(message):
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"log_{today}.txt"
    timestamp = datetime.now().strftime("%H:%M:%S")
    try:
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except: pass

def update_github_sync(status_text):
    try:
        with open(STATUS_FILE, "w") as f: f.write(status_text)
        os.system("git add .")
        os.system(f'git commit -m "sync update"')
        os.system("git push")
    except: print("Sync Failed")

def get_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
    return df

# ================= ANALYSIS =================
def analyze_market():
    # 15M Trend
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    trend_15m = "SIDEWAYS" if is_sideways else ("UP" if df_15m['close'].iloc[-1] > ema9_15m else "DOWN")

    # 5M Momentum
    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    ema9_5m = ta.trend.ema_indicator(df_5m['close'], 9).iloc[-1]
    trend_5m = "UP" if df_5m['close'].iloc[-1] > ema9_5m else "DOWN"

    # 1M Confirmation
    df_1m = get_data(SYMBOL, '1m')
    price = df_1m['close'].iloc[-1]
    
    return {
        "price": price, 
        "trend_15m": trend_15m, 
        "trend_5m": trend_5m, 
        "adx_5m": adx_5m
    }

# ================= MAIN LOOP =================
print("JASTON MASTER TRADE BOT IS ACTIVE...")
update_github_sync("LIVE")

try:
    while True:
        m = analyze_market()
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"=== JASTON MASTER TRADE BOT ===")
        print(f"15M TREND: {m['trend_15m']} | 5M TREND: {m['trend_5m']}")
        print(f"1M: Looking for confirmation...")
        print(f"PRICE: ${m['price']:,.2f} | 5M ADX: {m['adx_5m']:.1f}")
        print(f"-------------------------------")

        if m['trend_15m'] == "SIDEWAYS":
            status = "STATUS: Side-way Market. Waiting for trend..."
        elif m['adx_5m'] < 20:
            status = "STATUS: Low Momentum (ADX < 20). Waiting..."
        else:
            status = "STATUS: Trend is fine, waiting for entry..."
            
        print(status)
        log_activity(f"15M:{m['trend_15m']} | 5M:{m['trend_5m']} | ADX:{m['adx_5m']:.1f} | {status}")
        
        time.sleep(10)

except KeyboardInterrupt:
    print("\nShutting down...")
    update_github_sync("STOPPED")
    log_activity("Bot stopped by user")