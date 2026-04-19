import ccxt
import pandas as pd
import ta
import time
import os
from datetime import datetime

# ================= CONFIGURATION =================
API_KEY = 'dUTfsZjIuDVwHcaIAYwVEJ4n7Te8jHsEeRc2wJencEPxHC0XKygve29qOYpY1Co9'
SECRET = 'm2h1SRu4tU9wdMdDkqHVII8lpU6qtnCXvajiYOp9uUTxH6iaY37K3fujcOO6IXYh'
SYMBOL = 'BTC/USDT'
STATUS_FILE = "bot_status.txt"

exchange = ccxt.binance({
    'apiKey': API_KEY, 'secret': SECRET,
    'enableRateLimit': True, 'options': {'defaultType': 'future'}
})

# ================= RISK MANAGEMENT PARAMETERS =================
# Kwa mtaji wa $10 na 20x Leverage:
# Hasara ya $0.20 = 2% ya mtaji. Hii ni sawa na 0.1% price movement.
STOP_LOSS_PCT = 0.001  # 0.1% price move
TAKE_PROFIT_PCT = 0.002 # 0.2% price move (Risk Reward 1:2)

def get_dynamic_leverage(balance):
    if balance < 10: return 20 
    elif balance < 50: return 15
    else: return 10

def update_github_sync(status_text):
    try:
        with open(STATUS_FILE, "w") as f: f.write(status_text)
        os.system("git add . && git commit -m 'bot sync' && git push")
    except: pass

def get_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])

# ================= ANALYSIS =================
def analyze_market():
    # 15M Trend & Sideways Guard
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    
    # 5M ADX Strength
    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    
    # 1M Confirmation & Trailing Exit (EMA 21)
    df_1m = get_data(SYMBOL, '1m')
    price = df_1m['close'].iloc[-1]
    ema9_1m = ta.trend.ema_indicator(df_1m['close'], 9).iloc[-1]
    ema21_1m = ta.trend.ema_indicator(df_1m['close'], 21).iloc[-1] # Trailing Support

    trend_15m = "SIDEWAYS" if is_sideways else ("UP" if price > ema9_15m else "DOWN")
    
    return {
        "price": price, "trend_15m": trend_15m, "adx_5m": adx_5m,
        "ema9_1m": ema9_1m, "ema21_1m": ema21_1m
    }

# ================= MAIN LOOP =================
print("JASTON MASTER BOT: RISK-REWARD MODE ACTIVE...")
update_github_sync("LIVE_TRADING")

m = {"price": 0, "trend_15m": "SCANNING", "adx_5m": 0, "ema21_1m": 0}
counter = 0

try:
    while True:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total']['USDT']
        
        # Position Info
        in_trade = False
        active_pnl = 0.0
        side = None
        
        for pos in balance['info']['positions']:
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_trade = True
                    side = "LONG" if amt > 0 else "SHORT"
                    active_pnl = float(pos['unrealizedProfit'])
                    entry_price = float(pos['entryPrice'])

        if counter % 5 == 0: m = analyze_market()

        # Dashboard
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER BOT | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 WALLET: ${usdt_balance:.2f} | PnL: {active_pnl:.4f} USDT")
        print(f"🔍 15M: {m['trend_15m']} | ADX: {m['adx_5m']:.1f}")
        print(f"--------------------------------------------------")

        # LOGIC: EXIT CONTROL (Ili asitoke mapema)
        if in_trade:
            # 1. Hard Stop Loss ($0.20 Target)
            if active_pnl <= -0.20:
                print("⚠️ STOP LOSS REACHED ($0.20). Closing...")
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
            
            # 2. Trailing Exit (EMA 21) - Inampa nafasi ya kupumua
            elif side == "LONG" and live_price < m['ema21_1m']:
                print("🔴 EMA 21 Cross (LONG Exit). Closing...")
                exchange.create_market_order(SYMBOL, 'sell', abs(amt))
            elif side == "SHORT" and live_price > m['ema21_1m']:
                print("🟢 EMA 21 Cross (SHORT Exit). Closing...")
                exchange.create_market_order(SYMBOL, 'buy', abs(amt))
            
            # 3. Take Profit (Target $0.40 kwa Risk Reward 1:2)
            elif active_pnl >= 0.40:
                print("💰 TAKE PROFIT REACHED ($0.40). Closing...")
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))

        # LOGIC: ENTRY CONTROL
        elif m['trend_15m'] != "SIDEWAYS" and m['adx_5m'] > 20:
            qty = (usdt_balance * 0.5 * get_dynamic_leverage(usdt_balance)) / live_price
            if m['trend_15m'] == "UP" and live_price > m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'buy', qty)
                print("🚀 LONG ORDER PLACED")
            elif m['trend_15m'] == "DOWN" and live_price < m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'sell', qty)
                print("📉 SHORT ORDER PLACED")

        counter += 1
        time.sleep(2)

except Exception as e:
    print(f"Error: {e}")
    update_github_sync("ERROR_STOP")