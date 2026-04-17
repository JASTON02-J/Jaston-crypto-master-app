import ccxt
import pandas as pd
import ta
import time
import json
import os

def update_status(status):
    with open("bot_status.txt", "w") as f:
        f.write(status)
    # Hapa ndipo unapo-sync na GitHub moja kwa moja
    os.system("git add bot_status.txt")
    os.system('git commit -m "update status"')
    os.system("git push")

# Unapo-stop bot yako:
update_status("STOPPED")

# ================= CONFIG =================
API_KEY = 'UqjUuCgKJvVYVYrs6pmbGNOngRMBKVeVZ6NbUnx2goW7iuneSBaCBLI3hwWlesL8'
SECRET = 'xv19ZTtg8ArsEZ2F4YB1KAEX5xDBZ4g7eiYM7j7skLBTvkDOwLmTA9xPmMQ1aI8V'

symbol = 'BTC/USDT'
timeframe = '1m'

BASE_RISK = 0.01
MAX_RISK = 0.02

MAX_DAILY_TRADES = 5
COOLDOWN = 20

DATA_FILE = "trade_data.json"

# Trailing + TP settings
BREAKEVEN_ATR = 1.0
TRAILING_ATR = 1.5
TP_RR = 1.5   # fixed TP for 50%

# ================= STATE =================
daily_trades = 0
last_trade_time = 0
current_position = None

# ================= EXCHANGE =================
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})
exchange.options['adjustForTimeDifference'] = True
exchange.load_markets()

# ================= DATA =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"wins": 0, "losses": 0, "profit": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ================= INDICATORS =================
def get_df():
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=120)
    df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])

    df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()

    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14)
    df['atr'] = atr.average_true_range()

    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
    df['adx'] = adx.adx()

    return df

# ================= STRATEGY =================
def strategy(df):
    last = df.iloc[-1]

    if last['adx'] < 20:
        return 'hold', None

    if last['ema9'] > last['ema21'] and last['rsi'] < 40:
        return 'buy', last['atr']

    if last['ema9'] < last['ema21'] and last['rsi'] > 60:
        return 'sell', last['atr']

    return 'hold', None

# ================= DISPLAY =================
def show_status(balance, data):
    total = data['wins'] + data['losses']
    winrate = (data['wins'] / total * 100) if total > 0 else 0

    print("\n===== BOT STATUS =====")
    print(f"Balance: {balance:.2f} USDT")
    print(f"Profit: {data['profit']:.2f}")
    print(f"Wins: {data['wins']} | Losses: {data['losses']} | Winrate: {winrate:.2f}%")
    print(f"Trades Today: {daily_trades}")

    if current_position:
        print(f"Active Trade: {current_position['side']} | Entry: {current_position['entry']} | SL: {current_position['sl']}")
    else:
        print("No active trade")

# ================= OPEN TRADE =================
def open_trade(signal, atr):
    global current_position, daily_trades, last_trade_time

    balance = exchange.fetch_balance()['total']['USDT']
    risk_percent = min(BASE_RISK + (balance / 1000), MAX_RISK)
    risk_amount = balance * risk_percent

    price = exchange.fetch_ticker(symbol)['last']

    sl_distance = atr * 1.2
    total_amount = risk_amount / sl_distance
    half = total_amount / 2

    if signal == 'buy':
        sl = price - sl_distance
        tp = price + atr * TP_RR
        side = 'buy'
    else:
        sl = price + sl_distance
        tp = price - atr * TP_RR
        side = 'sell'

    # Open full position
    exchange.create_market_order(symbol, side, total_amount)

    # TP for 50%
    exit_side = 'sell' if side == 'buy' else 'buy'
    exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', exit_side, half,
        params={'stopPrice': tp, 'reduceOnly': True})

    current_position = {
        'side': signal,
        'entry': price,
        'sl': sl,
        'amount': total_amount,
        'half': half,
        'atr': atr,
        'tp': tp,
        'breakeven_done': False
    }

    daily_trades += 1
    last_trade_time = time.time()

    print(f"Trade Opened: {signal.upper()} at {price} | TP(50%) at {tp}")

# ================= MANAGE TRADE =================
def manage_trade(data):
    global current_position

    if current_position is None:
        return

    price = exchange.fetch_ticker(symbol)['last']
    entry = current_position['entry']
    atr = current_position['atr']
    side = current_position['side']

    move = abs(price - entry)

    # Break-even
    if not current_position['breakeven_done']:
        if move >= atr * BREAKEVEN_ATR:
            current_position['sl'] = entry
            current_position['breakeven_done'] = True
            print("Break-even activated")

    # Trailing
    if current_position['breakeven_done']:
        if side == 'buy':
            new_sl = price - atr * TRAILING_ATR
            if new_sl > current_position['sl']:
                current_position['sl'] = new_sl
                print(f"Trailing SL moved to {new_sl}")
        else:
            new_sl = price + atr * TRAILING_ATR
            if new_sl < current_position['sl']:
                current_position['sl'] = new_sl
                print(f"Trailing SL moved to {new_sl}")

    # Exit
    if side == 'buy' and price <= current_position['sl']:
        close_trade(price, data)
    elif side == 'sell' and price >= current_position['sl']:
        close_trade(price, data)

# ================= CLOSE =================
def close_trade(price, data):
    global current_position

    exit_side = 'sell' if current_position['side'] == 'buy' else 'buy'

    exchange.create_market_order(symbol, exit_side, current_position['half'])

    pnl = (price - current_position['entry']) * current_position['amount']

    if pnl > 0:
        data['wins'] += 1
    else:
        data['losses'] += 1

    data['profit'] += pnl
    save_data(data)

    print(f"Trade Closed | PnL: {pnl:.2f}")

    current_position = None

# ================= MAIN =================
data = load_data()

while True:
    try:
        balance = exchange.fetch_balance()['total']['USDT']
        show_status(balance, data)

        if daily_trades >= MAX_DAILY_TRADES:
            print("Daily limit reached")
            break

        if time.time() - last_trade_time < COOLDOWN:
            time.sleep(5)
            continue

        df = get_df()

        if current_position:
            manage_trade(data)
        else:
            signal, atr = strategy(df)
            if signal != 'hold':
                open_trade(signal, atr)

        time.sleep(5)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)