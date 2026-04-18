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
        return 20  # Kwa mtaji wako wa sasa ($5.5)
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
    # 15M Trend
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    trend_15m = "SIDEWAYS" if is_sideways else ("UP" if df_15m['close'].iloc[-1] > ema9_15m else "DOWN")

    # 5M Momentum
    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    
    # 1M Confirmation Price
    df_1m = get_data(SYMBOL, '1m')
    price = df_1m['close'].iloc[-1]
    
    return {
        "price": price, 
        "trend_15m": trend_15m, 
        "adx_5m": adx_5m
    }

# ================= MAIN LOOP =================
print("JASTON MASTER TRADE BOT IS ACTIVE...")
update_github_sync("LIVE")

# Hizi ni variable za kuanzia (Initial values)
m = {"price": 0, "trend_15m": "SCANNING", "adx_5m": 0}
counter = 0

try:
    while True:
        # 1. REAL-TIME DATA (PnL na Bei kila sekunde)
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        
        # Pata Balance na Leverage
        balance_info = exchange.fetch_balance()
        usdt_balance = balance_info['total']['USDT']
        current_leverage = get_dynamic_leverage(usdt_balance)
        
        try:
            exchange.set_leverage(current_leverage, SYMBOL)
        except: pass

        # Angalia Open Positions (PnL & Margin)
        positions = exchange.fetch_derivatives_positions([SYMBOL])
        active_pnl = 0.0
        margin_used = 0.0
        in_trade = False

        for pos in positions:
            if float(pos['notional']) != 0:
                active_pnl = float(pos['unrealizedPnl'])
                margin_used = abs(float(pos['notional'])) / current_leverage
                in_trade = True

        # 2. ANALYSIS SYNC (Inafanyika kila baada ya mizunguko 10 kuzuia API Ban)
        if counter % 10 == 0:
            m = analyze_market()

        # 3. DASHBOARD UPDATE (CMD)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER TRADE BOT | {datetime.now().strftime('%H:%M:%S')}")
        print(f"--------------------------------------------------")
        print(f"💰 WALLET: {usdt_balance:.2f} USDT | ⚙️ LEVERAGE: {current_leverage}x")
        print(f"📊 TREND (15M): {m['trend_15m']} | ⚡ ADX (5M): {m['adx_5m']:.1f}")
        print(f"💵 LIVE PRICE: ${live_price:,.2f}")
        print(f"--------------------------------------------------")

        if in_trade:
            pnl_icon = "🟢" if active_pnl >= 0 else "🔴"
            print(f"🔥 ACTIVE TRADE DETECTED!")
            print(f"   Margin Used: {margin_used:.2f} USDT")
            print(f"   Live PnL: {pnl_icon} {active_pnl:.4f} USDT")
        else:
            if m['trend_15m'] == "SIDEWAYS":
                status = "STATUS: Side-way Market. Waiting..."
            elif m['adx_5m'] < 20:
                status = "STATUS: Low Momentum (ADX < 20). Waiting..."
            else:
                status = "STATUS: Trend is fine, scanning for entry..."
            print(status)

        # 4. LOGGING (Kila sekunde 10)
        if counter % 10 == 0:
            log_activity(f"Bal:{usdt_balance:.2f} | PnL:{active_pnl:.4f} | {m['trend_15m']}")

        counter += 1
        time.sleep(1) # REAL-TIME SPEED

except KeyboardInterrupt:
    print("\nShutting down...")
    update_github_sync("STOPPED")
    log_activity("Bot stopped by user")