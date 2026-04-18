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

# Initialize Exchange
exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})

# ================= HELPERS =================
def log_activity(message):
    """Inatunza kumbukumbu kwenye faili la leo la .txt"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"log_{today}.txt"
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    try:
        with open(log_file, "a") as f:
            f.write(full_message + "\n")
    except:
        pass

def update_github_sync(status_text):
    """Inatuma hali ya bot GitHub bila kutumia emoji kuzuia errors"""
    try:
        with open(STATUS_FILE, "w") as f: 
            f.write(status_text)
        
        log_activity(f"SYSTEM: {status_text}")
        
        os.system("git add .")
        os.system(f'git commit -m "sync update"')
        os.system("git push")
    except Exception as e:
        print(f"Sync Error: {e}")

def get_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
    return df

# ================= CORE STRATEGY =================
def analyze_market():
    df_15m = get_data(SYMBOL, '15m')
    ema9 = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21 = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    trend = "UP" if df_15m['close'].iloc[-1] > ema9 else "DOWN"

    df_5m = get_data(SYMBOL, '5m')
    adx = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]

    return {"price": df_15m['close'].iloc[-1], "trend": trend, "adx": adx}

# ================= MAIN LOOP =================
print("JASTON MASTER BOT IS STARTING...")
update_github_sync("LIVE")
log_activity("Bot started successfully")

try:
    while True:
        m = analyze_market()
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"=== JASTON MASTER TRADE ===")
        print(f"PRICE: ${m['price']:,.2f}")
        print(f"TREND: {m['trend']} | ADX: {m['adx']:.1f}")
        
        if m['adx'] < 20:
            status = "Waiting: Side-way Market"
        else:
            status = f"Scanning: {m['trend']} Trend"
            
        print(f"STATUS: {status}")
        
        # Rekodi kila baada ya mzunguko wa uchambuzi
        log_activity(f"Price: {m['price']} | {status}")
        
        time.sleep(10)

except KeyboardInterrupt:
    print("\nShutting down...")
    update_github_sync("STOPPED")
    log_activity("Bot stopped by user")
    print("Dashboard updated to OFFLINE.")