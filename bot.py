import ccxt
import pandas as pd
import ta
import time
import json
import os
import signal
import sys

# ================= CONFIG =================
API_KEY = 'UqjUuCgKJvVYVYrs6pmbGNOngRMBKVeVZ6NbUnx2goW7iuneSBaCBLI3hwWlesL8'
SECRET = 'xv19ZTtg8ArsEZ2F4YB1KAEX5xDBZ4g7eiYM7j7skLBTvkDOwLmTA9xPmMQ1aI8V'
ACTIVE_FILE = "active_trade.json"
DATA_FILE = "trade_data.json"
symbol = 'BTC/USDT'
timeframe = '1m'

BASE_RISK = 0.01
MAX_RISK = 0.02
MAX_DAILY_TRADES = 5
COOLDOWN = 20
BREAKEVEN_ATR = 1.0
TRAILING_ATR = 1.5
TP_RR = 1.5

# ================= STATE =================
daily_trades = 0
last_trade_time = 0
current_position = None

# ================= FUNCTIONS =================
def update_status(status):
    """Inasoma hali ya bot na kuituma GitHub"""
    with open("bot_status.txt", "w") as f:
        f.write(status)
    try:
        os.system("git add bot_status.txt")
        os.system(f'git commit -m "Auto-update: {status}"')
        os.system("git push")
    except:
        print("Git push imeshindikana, angalia internet.")

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"wins": 0, "losses": 0, "profit": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def handle_exit(sig, frame):
    print("\nBot inasimamishwa...")
    update_status("STOPPED")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

# ================= EXCHANGE =================
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# ================= LOGIC =================
def get_df():
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=120)
    df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
    df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
    return df

def strategy(df):
    last = df.iloc[-1]
    if last['adx'] < 20: return 'hold', None
    if last['ema9'] > last['ema21'] and last['rsi'] < 40: return 'buy', last['atr']
    if last['ema9'] < last['ema21'] and last['rsi'] > 60: return 'sell', last['atr']
    return 'hold', None

def open_trade(signal_type, atr):
    global current_position, daily_trades, last_trade_time
    balance = exchange.fetch_balance()['total']['USDT']
    risk_percent = min(BASE_RISK + (balance / 1000), MAX_RISK)
    risk_amount = balance * risk_percent
    price = exchange.fetch_ticker(symbol)['last']
    sl_distance = atr * 1.2
    total_amount = risk_amount / sl_distance
    
    if signal_type == 'buy':
        sl, tp = price - sl_distance, price + atr * TP_RR
    else:
        sl, tp = price + sl_distance, price - atr * TP_RR

    exchange.create_market_order(symbol, signal_type, total_amount)
    current_position = {'side': signal_type, 'entry': price, 'sl': sl, 'tp': tp, 'amount': total_amount, 'atr': atr, 'breakeven_done': False}
    with open(ACTIVE_FILE, "w") as f: json.dump(current_position, f)
    daily_trades += 1
    last_trade_time = time.time()

def manage_trade(data):
    global current_position
    price = exchange.fetch_ticker(symbol)['last']
    # Add your trade exit logic here...
    pass

# ================= MAIN LOOP =================
data = load_data()
print("Bot inaanza...")
update_status("ACTIVE")

while True:
    try:
        balance = exchange.fetch_balance()['total']['USDT']
        if daily_trades >= MAX_DAILY_TRADES:
            update_status("STOPPED")
            break
        
        df = get_df()
        if current_position:
            manage_trade(data)
        else:
            sig, atr = strategy(df)
            if sig != 'hold': open_trade(sig, atr)
        
        time.sleep(10)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)