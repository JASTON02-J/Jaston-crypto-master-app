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
TIMEFRAME = '1m'
DATA_FILE = "trade_data.json"
ACTIVE_FILE = "active_trade.json"
STATUS_FILE = "bot_status.txt"
HISTORY_FILE = "trade_history.json"

# Advanced Scalping Settings
BASE_RISK = 0.01 
TRAILING_DISTANCE = 0.3 
COOLDOWN_MINUTES = 5  
MIN_ADX = 20  # Trend strength filter (Avoid Sideways)

exchange = ccxt.binance({
    'apiKey': API_KEY, 'secret': SECRET,
    'enableRateLimit': True, 'options': {'defaultType': 'future'}
})

# ================= STATE & MEMORY MANAGEMENT =================
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
        os.system("git add bot_status.txt")
        os.system('git commit -m "update_status"')
        os.system("git push")
    except:
        pass

trade_data = load_json(DATA_FILE, {"wins": 0, "losses": 0, "profit": 0, "last_loss_time": 0})
active_trade = load_json(ACTIVE_FILE, None)

# ================= ADVANCED ANALYSIS =================
def get_analysis():
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
    
    # 1. Trend & Strength (EMA + ADX)
    df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], 14).adx()
    
    # 2. Momentum (Stoch RSI)
    stoch_rsi = ta.momentum.StochRSIIndicator(df['close'], 14, 3, 3)
    df['stoch_k'] = stoch_rsi.stochrsi_k()
    
    # 3. Support & Resistance (Dynamic Price Action)
    df['resistance'] = df['high'].rolling(window=20).max()
    df['support'] = df['low'].rolling(window=20).min()
    
    # 4. Volatility (Bollinger Bands)
    bb = ta.volatility.BollingerBands(df['close'], 20, 2)
    df['lower_band'] = bb.bollinger_lband()
    df['upper_band'] = bb.bollinger_hband()
    
    return df.iloc[-1]

def open_position(side, price, strategy_reason):
    global active_trade
    current_time = time.time()
    if current_time - trade_data.get('last_loss_time', 0) < (COOLDOWN_MINUTES * 60):
        return

    try:
        balance = exchange.fetch_balance()['total']['USDT']
        amount = (balance * BASE_RISK) / price 
        order = exchange.create_market_order(SYMBOL, side, amount)
        
        sl = price * 0.995 if side == 'buy' else price * 1.005
        tp = price * 1.015 if side == 'buy' else price * 0.985
        
        active_trade = {
            'side': side, 'entry': price, 'amount': amount, 
            'sl': sl, 'tp': tp, 'highest_price': price,
            'strategy': strategy_reason, 'order_id': order['id'], 
            'time': str(datetime.now())
        }
        save_json(ACTIVE_FILE, active_trade)
        update_github_sync(f"ACTIVE: {side.upper()} via {strategy_reason}")
    except Exception as e:
        print(f"❌ Entry Error: {e}")

def close_position(price):
    global active_trade, trade_data
    try:
        side_to_close = 'sell' if active_trade['side'] == 'buy' else 'buy'
        exchange.create_market_order(SYMBOL, side_to_close, active_trade['amount'])
        
        pnl = (price - active_trade['entry']) * active_trade['amount'] if active_trade['side'] == 'buy' else (active_trade['entry'] - price) * active_trade['amount']
        
        # --- PERFORMANCE MEMORY REPORT ---
        print("\n" + "="*30)
        if pnl > 0:
            print(f"✅ WINNER! Strategy: {active_trade['strategy']}")
            print(f"Reason: Price followed trend & momentum after hitting support/resistance.")
            trade_data['wins'] += 1
        else:
            print(f"❌ LOSS. Strategy: {active_trade['strategy']}")
            print(f"Reason: Sudden reversal or spike hit Stop Loss. Cooldown active.")
            trade_data['losses'] += 1
            trade_data['last_loss_time'] = time.time()
        print("="*30 + "\n")
        
        trade_data['profit'] += pnl
        save_json(DATA_FILE, trade_data)
        if os.path.exists(ACTIVE_FILE): os.remove(ACTIVE_FILE)
        active_trade = None
        update_github_sync(f"ACTIVE: Profit ${trade_data['profit']:.2f}")
    except Exception as e:
        print(f"❌ Close Error: {e}")

# ================= MAIN LOOP =================
print("✅ JASTON INTELLIGENCE BOT IS LIVE...")
update_github_sync("ACTIVE")

try:
    while True:
        data = get_analysis()
        price = data['close']
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"=== JASTON MASTER SCALPER (LIVE) ===")
        print(f"💰 PRICE: ${price:,.2f} | ADX: {data['adx']:.1f}")
        print(f"📊 STOCH K: {data['stoch_k']:.1f} | EMA Trend: {'UP' if data['ema9']>data['ema21'] else 'DOWN'}")
        print(f"📈 PROFIT: ${trade_data['profit']:.2f} | W:{trade_data['wins']} L:{trade_data['losses']}")
        print(f"------------------------------------")

        if active_trade:
            # Trailing Stop Loss Logic
            if active_trade['side'] == 'buy':
                if price > active_trade['highest_price']:
                    active_trade['highest_price'] = price
                    new_sl = price * (1 - (TRAILING_DISTANCE / 100))
                    if new_sl > active_trade['sl']: active_trade['sl'] = new_sl
                if price <= active_trade['sl'] or price >= active_trade['tp']:
                    close_position(price)
            else:
                if price < active_trade['highest_price']:
                    active_trade['highest_price'] = price
                    new_sl = price * (1 + (TRAILING_DISTANCE / 100))
                    if new_sl < active_trade['sl']: active_trade['sl'] = new_sl
                if price >= active_trade['sl'] or price <= active_trade['tp']:
                    close_position(price)
        else:
            # CHECK FOR SIDEWAYS MARKET
            if data['adx'] < MIN_ADX:
                print("😴 STATUS: Side-way Market. Waiting for trend...")
            else:
                # ENTRY STRATEGIES
                # 1. Buy: Trend Up + Stoch Oversold + Near Support/Lower Band
                if (data['ema9'] > data['ema21'] and data['stoch_k'] < 20 and price <= data['support'] * 1.001):
                    open_position('buy', price, "EMA_Trend+Stoch_Oversold+Support_Bounce")
                
                # 2. Sell: Trend Down + Stoch Overbought + Near Resistance/Upper Band
                elif (data['ema9'] < data['ema21'] and data['stoch_k'] > 80 and price >= data['resistance'] * 0.999):
                    open_position('sell', price, "EMA_Trend+Stoch_Overbought+Resistance_Reject")

        time.sleep(1)

except KeyboardInterrupt:
    update_github_sync("STOPPED")
    print("🛑 Bot Stopped.")