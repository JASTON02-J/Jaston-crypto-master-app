import ccxt
import pandas as pd
import ta
import time
import os
import json

# ================= CONFIG (LIVE API KEYS) =================
API_KEY = 'UqjUuCgKJvVYVYrs6pmbGNOngRMBKVeVZ6NbUnx2goW7iuneSBaCBLI3hwWlesL8'
SECRET = 'xv19ZTtg8ArsEZ2F4YB1KAEX5xDBZ4g7eiYM7j7skLBTvkDOwLmTA9xPmMQ1aI8V'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'
DATA_FILE = "trade_data.json"
ACTIVE_FILE = "active_trade.json"
STATUS_FILE = "bot_status.txt"

# Risk Management Settings
BASE_RISK = 0.01  # 1% of total balance per trade
TRAILING_DISTANCE = 0.5 # Trailing Stop Loss at 0.5%

# Initialize Binance Exchange (Futures)
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# ================= STATE MANAGEMENT =================
def load_json(file, default):
    if not os.path.exists(file): return default
    try:
        with open(file, "r") as f: return json.load(f)
    except: return default

def save_json(file, data):
    with open(file, "w") as f: json.dump(data, f, indent=4)

def update_github_sync(status_text):
    """Sends bot status to GitHub to update the Streamlit Dashboard"""
    try:
        with open(STATUS_FILE, "w") as f:
            f.write(status_text)
        
        # Fixed Git commands to avoid pathspec errors
        os.system("git add bot_status.txt")
        os.system('git commit -m "update_status"')
        os.system("git push")
    except Exception as e:
        print(f"Sync Error: {e}")

trade_data = load_json(DATA_FILE, {"wins": 0, "losses": 0, "profit": 0})
active_trade = load_json(ACTIVE_FILE, None)

# ================= TRADING FUNCTIONS =================
def get_analysis():
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
    return df.iloc[-1]

def open_position(side, price):
    global active_trade
    try:
        balance = exchange.fetch_balance()['total']['USDT']
        amount = (balance * BASE_RISK) / price 
        
        print(f"🚀 EXECUTING LIVE {side.upper()} ORDER...")
        order = exchange.create_market_order(SYMBOL, side, amount)
        
        # Initial SL (1.5%) and TP (3.0%)
        sl = price * 0.985 if side == 'buy' else price * 1.015
        tp = price * 1.03 if side == 'buy' else price * 0.97
        
        active_trade = {
            'side': side, 'entry': price, 'amount': amount, 
            'sl': sl, 'tp': tp, 'highest_price': price,
            'order_id': order['id']
        }
        save_json(ACTIVE_FILE, active_trade)
        update_github_sync(f"ACTIVE: {side.upper()} at {price}")
    except Exception as e:
        print(f"❌ Order Failed: {e}")

def close_position(price):
    global active_trade, trade_data
    try:
        side_to_close = 'sell' if active_trade['side'] == 'buy' else 'buy'
        print(f"🔒 CLOSING POSITION AT ${price}...")
        
        exchange.create_market_order(SYMBOL, side_to_close, active_trade['amount'])
        
        pnl = (price - active_trade['entry']) * active_trade['amount'] if active_trade['side'] == 'buy' else (active_trade['entry'] - price) * active_trade['amount']
        
        trade_data['profit'] += pnl
        if pnl > 0: trade_data['wins'] += 1
        else: trade_data['losses'] += 1
        
        save_json(DATA_FILE, trade_data)
        if os.path.exists(ACTIVE_FILE): os.remove(ACTIVE_FILE)
        active_trade = None
        update_github_sync(f"ACTIVE: Profit ${trade_data['profit']:.2f}")
    except Exception as e:
        print(f"❌ Close Failed: {e}")

# ================= MAIN LOOP =================
print("✅ JASTON MASTER BOT IS STARTING...")
update_github_sync("ACTIVE")

try:
    while True:
        last_data = get_analysis()
        current_price = last_data['close']
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"=== JASTON MASTER TRADE (LIVE BINANCE) ===")
        print(f"💰 PRICE: ${current_price:,.2f} | RSI: {last_data['rsi']:.1f}")
        print(f"📈 PROFIT: ${trade_data['profit']:.2f} | W:{trade_data['wins']} L:{trade_data['losses']}")
        print(f"-------------------------------------------")

        if active_trade:
            # Trailing Stop Logic
            if active_trade['side'] == 'buy':
                if current_price > active_trade['highest_price']:
                    active_trade['highest_price'] = current_price
                    new_sl = current_price * (1 - (TRAILING_DISTANCE / 100))
                    if new_sl > active_trade['sl']: active_trade['sl'] = new_sl
                
                if current_price <= active_trade['sl'] or current_price >= active_trade['tp']:
                    close_position(current_price)

            elif active_trade['side'] == 'sell':
                if current_price < active_trade['highest_price']:
                    active_trade['highest_price'] = current_price
                    new_sl = current_price * (1 + (TRAILING_DISTANCE / 100))
                    if new_sl < active_trade['sl']: active_trade['sl'] = new_sl
                
                if current_price >= active_trade['sl'] or current_price <= active_trade['tp']:
                    close_position(current_price)

            pnl = (current_price - active_trade['entry']) * active_trade['amount'] if active_trade['side'] == 'buy' else (active_trade['entry'] - current_price) * active_trade['amount']
            print(f"📡 POS: {active_trade['side'].upper()} | Entry: {active_trade['entry']:.2f}")
            print(f"🛡️ SL: {active_trade['sl']:.2f} | LIVE PnL: ${pnl:.2f}")
        else:
            print("😴 STATUS: Analyzing Market...")
            if last_data['ema9'] > last_data['ema21'] and last_data['rsi'] < 35:
                open_position('buy', current_price)
            elif last_data['ema9'] < last_data['ema21'] and last_data['rsi'] > 65:
                open_position('sell', current_price)

        time.sleep(1) 

except KeyboardInterrupt:
    print("\n🛑 SHUTTING DOWN... Updating status to GitHub.")
    update_github_sync("STOPPED")
    print("✅ Dashboard set to STOPPED. Goodbye!")