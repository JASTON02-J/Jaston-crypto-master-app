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

# ================= AUTO-LEVERAGE LOGIC =================
def get_dynamic_leverage(balance):
    if balance < 10:
        return 20 
    elif balance < 50:
        return 15
    elif balance < 200:
        return 10
    else:
        return 5

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
    # 15M Trend (Major Direction)
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    trend_15m = "SIDEWAYS" if is_sideways else ("UP" if df_15m['close'].iloc[-1] > ema9_15m else "DOWN")

    # 5M Momentum (Strength)
    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    ema9_5m = ta.trend.ema_indicator(df_5m['close'], 9).iloc[-1]
    trend_5m = "UP" if df_5m['close'].iloc[-1] > ema9_5m else "DOWN"

    # 1M Confirmation
    df_1m = get_data(SYMBOL, '1m')
    price = df_1m['close'].iloc[-1]
    ema9_1m = ta.trend.ema_indicator(df_1m['close'], 9).iloc[-1]
    trend_1m = "UP" if price > ema9_1m else "DOWN"
    
    return {
        "price": price, 
        "trend_15m": trend_15m, 
        "trend_5m": trend_5m, 
        "trend_1m": trend_1m,
        "adx_5m": adx_5m
    }

# ================= MAIN LOOP =================
print("JASTON MASTER TRADE BOT IS ACTIVE...")
update_github_sync("LIVE")

m = {"price": 0, "trend_15m": "SCANNING", "trend_5m": "SCANNING", "trend_1m": "SCANNING", "adx_5m": 0}
counter = 0

try:
    while True:
        # 1. REAL-TIME DATA
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        
        balance_info = exchange.fetch_balance()
        usdt_balance = balance_info['total']['USDT']
        current_leverage = get_dynamic_leverage(usdt_balance)
        
        try:
            exchange.set_leverage(current_leverage, SYMBOL)
        except: pass

        active_pnl = 0.0
        margin_used = 0.0
        in_trade = False

        try:
            for pos in balance_info['info']['positions']:
                if pos['symbol'] == SYMBOL.replace('/', ''):
                    amt = float(pos['positionAmt'])
                    if amt != 0:
                        active_pnl = float(pos['unrealizedProfit'])
                        margin_used = (abs(amt) * live_price) / current_leverage
                        in_trade = True
        except: pass

        # 2. ANALYSIS SYNC (Kila baada ya mizunguko 10)
        if counter % 10 == 0:
            try:
                m = analyze_market()
            except: pass

        # 3. DASHBOARD UPDATE (Visual Learning Mode)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER TRADE BOT | {datetime.now().strftime('%H:%M:%S')}")
        print(f"--------------------------------------------------")
        print(f"💰 WALLET: {usdt_balance:.2f} USDT | ⚙️ LEVERAGE: {current_leverage}x")
        print(f"💵 LIVE PRICE: ${live_price:,.2f}")
        print(f"--------------------------------------------------")
        
        # Breakdown ya Market Analysis kwa ajili ya kujifunza
        t15m_color = "🟢" if m['trend_15m'] == "UP" else ("🔴" if m['trend_15m'] == "DOWN" else "🟡")
        t5m_color = "🟢" if m['trend_5m'] == "UP" else "🔴"
        t1m_color = "🟢" if m['trend_1m'] == "UP" else "🔴"
        
        print(f"🔍 MARKET DIRECTION:")
        print(f"   [15M Trend]: {m['trend_15m']} {t15m_color}")
        print(f"   [5M Momentum]: {m['trend_5m']} {t5m_color} | ADX: {m['adx_5m']:.1f}")
        print(f"   [1M Status]: {m['trend_1m']} {t1m_color} (Last Entry Scan)")
        print(f"--------------------------------------------------")

        # Decision Engine Logic Explanation
        if in_trade:
            decision = "STATUS: Holding Position. Monitoring SL/TP..."
        elif m['trend_15m'] == "SIDEWAYS":
            decision = "DECISION: STAY OUT - Market is Sideways (No Clear Trend)"
        elif m['adx_5m'] < 20:
            decision = "DECISION: STAY OUT - Low Volatility (ADX < 20)"
        elif m['trend_15m'] != m['trend_5m']:
            decision = f"DECISION: WAITING - 15M ({m['trend_15m']}) and 5M ({m['trend_5m']}) Conflict"
        else:
            decision = f"DECISION: SCANNING 1M - Seeking {m['trend_15m']} entry confirmation"

        print(f"🤖 BOT LOGIC: {decision}")
        print(f"--------------------------------------------------")

        if in_trade:
            pnl_icon = "🟢" if active_pnl >= 0 else "🔴"
            print(f"🔥 ACTIVE TRADE:")
            print(f"   Margin Used: {margin_used:.2f} USDT")
            print(f"   Live PnL: {pnl_icon} {active_pnl:.4f} USDT")
        
        # 4. LOGGING & COUNTER
        if counter % 10 == 0:
            log_activity(f"Price:{live_price} | 15M:{m['trend_15m']} | ADX:{m['adx_5m']:.1f}")

        counter += 1
        time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down...")
    update_github_sync("STOPPED")
    log_activity("Bot stopped by user")