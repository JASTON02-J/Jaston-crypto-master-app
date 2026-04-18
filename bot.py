import ccxt
import pandas as pd
import ta
import time
import os
import json
from datetime import datetime

# ================= CONFIG (LIVE API KEYS) =================
API_KEY = 'UqjUuCgKJvVYVYrs6pmbGNOngRMBKVeVZ6NbUnx2goW7iuneSBaCBLI3hwWlesL8'
SECRET = 'xv19ZTtg8ArsEZ2F4YB1KAEX5xDBZ4g7eiYM7j7skLBTvkDOwLmTA9xPmMQ1aI8V'
SYMBOL = 'BTC/USDT'
DATA_FILE = "trade_data.json"
ACTIVE_FILE = "active_trade.json"
STATUS_FILE = "bot_status.txt"

# Settings
BASE_RISK = 0.01          
TRAILING_DISTANCE = 0.3   
COOLDOWN_MINUTES = 5      
MIN_ADX = 20              

exchange = ccxt.binance({
    'apiKey': API_KEY, 'secret': SECRET,
    'enableRateLimit': True, 'options': {'defaultType': 'future'}
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
    except: pass

def get_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
    return df

# ================= BRAIN: TRIPLE TF + CANDLE =================
def analyze_market():
    # 1. 15m TREND
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    
    # Logic ya Sideways: Kama EMA zimekaribiana sana
    is_sideways_15m = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    trend_15m = "SIDEWAYS" if is_sideways_15m else ("UP" if df_15m['close'].iloc[-1] > ema9_15m else "DOWN")

    # 2. 5m MOMENTUM
    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    ema9_5m = ta.trend.ema_indicator(df_5m['close'], 9).iloc[-1]
    trend_5m = "UP" if df_5m['close'].iloc[-1] > ema9_5m else "DOWN"

    # 3. 1m ENTRY
    df_1m = get_data(SYMBOL, '1m')
    last = df_1m.iloc[-1]
    prev = df_1m.iloc[-2]
    
    body = abs(last['close'] - last['open'])
    lower_wick = min(last['close'], last['open']) - last['low']
    upper_wick = last['high'] - max(last['close'], last['open'])
    
    is_bull_signal = (last['close'] > prev['open'] and last['open'] < prev['close']) or (lower_wick > (body * 2))
    is_bear_signal = (last['close'] < prev['open'] and last['open'] > prev['close']) or (upper_wick > (body * 2))

    stoch_k = ta.momentum.StochRSIIndicator(df_1m['close'], 14, 3, 3).stochrsi_k().iloc[-1]

    return {
        "price": last['close'],
        "trend_15m": trend_15m,
        "trend_5m": trend_5m,
        "adx_5m": adx_5m,
        "stoch_k": stoch_k,
        "buy_signal": is_bull_signal,
        "sell_signal": is_bear_signal
    }

trade_data = load_json(DATA_FILE, {"wins": 0, "losses": 0, "profit": 0, "last_loss_time": 0})
active_trade = load_json(ACTIVE_FILE, None)

def open_position(side, price, strategy):
    global active_trade
    try:
        balance = exchange.fetch_balance()['total']['USDT']
        amount = (balance * BASE_RISK) / price 
        exchange.create_market_order(SYMBOL, side, amount)
        
        sl = price * 0.995 if side == 'buy' else price * 1.005
        tp = price * 1.015 if side == 'buy' else price * 0.985
        
        active_trade = {'side': side, 'entry': price, 'amount': amount, 'sl': sl, 'tp': tp, 'highest_price': price, 'strategy': strategy}
        save_json(ACTIVE_FILE, active_trade)
        update_github_sync(f"JASTON MASTER TRADE: ENTERED {side.upper()}")
    except Exception as e: print(f"Entry Error: {e}")

def close_position(price):
    global active_trade, trade_data
    try:
        side_to_close = 'sell' if active_trade['side'] == 'buy' else 'buy'
        exchange.create_market_order(SYMBOL, side_to_close, active_trade['amount'])
        pnl = (price - active_trade['entry']) * active_trade['amount'] if active_trade['side'] == 'buy' else (active_trade['entry'] - price) * active_trade['amount']
        
        trade_data['profit'] += pnl
        if pnl > 0: trade_data['wins'] += 1
        else: trade_data['losses'] += 1; trade_data['last_loss_time'] = time.time()
        
        save_json(DATA_FILE, trade_data)
        if os.path.exists(ACTIVE_FILE): os.remove(ACTIVE_FILE)
        active_trade = None
        update_github_sync(f"JASTON MASTER TRADE: CLOSED PNL ${pnl:.2f}")
    except Exception as e: print(f"Close Error: {e}")

# ================= MAIN LOOP =================
print("🚀 JASTON MASTER TRADE BOT IS ACTIVE...")

# --- ONGEZA MSTARI HUU HAPA CHINI ---
update_github_sync("Jaston Master Bot is LIVE and Scanning... 🔍")

try:
    while True:
        m = analyze_market()
        # ... (code zingine zote zinaendelea hapa)
try:
    while True:
        m = analyze_market()
        price = m['price']
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"=== JASTON MASTER TRADE BOT ===")
        print(f"🔵 15M TREND: {m['trend_15m']} | 🟢 5M TREND: {m['trend_5m']}")
        print(f"💰 PRICE: ${price:,.2f} | ⚡ 5M ADX: {m['adx_5m']:.1f}")
        print(f"📈 PROFIT: ${trade_data['profit']:.2f} | W:{trade_data['wins']} L:{trade_data['losses']}")
        print(f"-------------------------------")

        if active_trade:
            if active_trade['side'] == 'buy':
                if price > active_trade['highest_price']: active_trade['highest_price'] = price
                if price <= active_trade['sl'] or price >= active_trade['tp']: close_position(price)
            else:
                if price < active_trade['highest_price']: active_trade['highest_price'] = price
                if price >= active_trade['sl'] or price <= active_trade['tp']: close_position(price)
        else:
            # HII NDIO SEHEMU ULIYOULIZIA:
            if m['adx_5m'] < MIN_ADX or m['trend_15m'] == "SIDEWAYS":
                print("😴 STATUS: Side-way Market. Waiting for trend...")
            else:
                if m['trend_15m'] == "UP" and m['trend_5m'] == "UP" and m['stoch_k'] < 30 and m['buy_signal']:
                    open_position('buy', price, "Triple_TF_Buy")
                elif m['trend_15m'] == "DOWN" and m['trend_5m'] == "DOWN" and m['stoch_k'] > 70 and m['sell_signal']:
                    open_position('sell', price, "Triple_TF_Sell")
                else:
                    print("🔍 STATUS: Trend is okay, waiting for 1m Entry Signal...")

        time.sleep(2)
except KeyboardInterrupt: print("🛑 Stopped.")