import ccxt
import pandas as pd
import ta
import time
import os
import json
from datetime import datetime

# ================= CONFIG (LIVE API KEYS) =================
API_KEY = 'dUTfsZjIuDVwHcaIAYwVEJ4n7Te8jHsEeRc2wJencEPxHC0XKygve29qOYpY1Co9'
SECRET = 'm2h1SRu4tU9wdMdDkqHVII8lpU6qtnCXvajiYOp9uUTxH6iaY37K3fujcOO6IXYh'
SYMBOL = 'BTC/USDT'
DATA_FILE = "trade_data.json"
ACTIVE_FILE = "active_trade.json"
STATUS_FILE = "bot_status.txt"

# Settings
BASE_RISK = 0.01          
MIN_ADX = 20              

exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})

# ================= DATA HELPERS =================
def load_json(file, default):
    if not os.path.exists(file): return default
    try:
        with open(file, "r") as f: return json.load(f)
    except: return default

def save_json(file, data):
    with open(file, "w") as f: json.dump(data, f, indent=4)

def update_github_sync(status_text):
    try:
        with open(STATUS_FILE, "w") as f: f.write(status_text)
        os.system("git add .")
        os.system(f'git commit -m "update: {status_text}"')
        os.system("git push")
    except Exception as e:
        print(f"Sync Error: {e}")

def get_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
    return df

# ================= BRAIN: TRIPLE TF =================
def analyze_market():
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways_15m = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    trend_15m = "SIDEWAYS" if is_sideways_15m else ("UP" if df_15m['close'].iloc[-1] > ema9_15m else "DOWN")

    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    ema9_5m = ta.trend.ema_indicator(df_5m['close'], 9).iloc[-1]
    trend_5m = "UP" if df_5m['close'].iloc[-1] > ema9_5m else "DOWN"

    df_1m = get_data(SYMBOL, '1m')
    stoch_k = ta.momentum.StochRSIIndicator(df_1m['close'], 14, 3, 3).stochrsi_k().iloc[-1]

    return {"price": df_1m['close'].iloc[-1], "trend_15m": trend_15m, "trend_5m": trend_5m, "adx_5m": adx_5m, "stoch_k": stoch_k}

trade_data = load_json(DATA_FILE, {"wins": 0, "losses": 0, "profit": 0})
active_trade = load_json(ACTIVE_FILE, None)

# ================= MAIN LOOP =================
print("🚀 JASTON MASTER TRADE BOT IS ACTIVE...")
update_github_sync("Jaston Master Bot is LIVE and Scanning... 🔍")

try:
    while True:
        m = analyze_market()
        price = m['price']
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"=== JASTON MASTER TRADE BOT ===")
        print(f"🔵 15M TREND: {m['trend_15m']} | 🟢 5M TREND: {m['trend_5m']}")
        print(f"💰 PRICE: ${price:,.2f} | ⚡ 5M ADX: {m['adx_5m']:.1f}")
        print(f"-------------------------------")

        if active_trade:
            if active_trade['side'] == 'buy' and (price <= active_trade['sl'] or price >= active_trade['tp']):
                pass
        else:
            if m['adx_5m'] < MIN_ADX or m['trend_15m'] == "SIDEWAYS":
                print("😴 STATUS: Side-way Market. Waiting...")
            else:
                print("🔍 STATUS: Trend is okay, waiting for entry...")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Shutting down...")
    update_github_sync("STOPPED 🛑") 
    print("✅ Dashboard updated to OFFLINE.")