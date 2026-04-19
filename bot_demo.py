import ccxt
import pandas as pd
import ta
import time
import os
from datetime import datetime

# ================= DEMO CONFIGURATION =================
# WEKA API KEYS ZA TESTNET HAPA (Usitumie za Live!)
API_KEY = 'WEKA_TESTNET_KEY_HAPA'
SECRET = 'WEKA_TESTNET_SECRET_HAPA'
SYMBOL = 'BTC/USDT'

# Tumeiambia bot itumie 'testnet' mode
exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})
exchange.set_sandbox_mode(True) # MUHIMU: Hii inawasha Demo Mode

# ================= RISK PARAMETERS (Matched with Backtest) =================
# Hasara ya $0.20 na Faida ya $0.40 kama tulivyofanya kwenye analysis
STOP_LOSS_AMT = 0.20   
TAKE_PROFIT_AMT = 0.40  

def get_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])

def analyze_market():
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    
    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    
    df_1m = get_data(SYMBOL, '1m')
    price = df_1m['close'].iloc[-1]
    ema9_1m = ta.trend.ema_indicator(df_1m['close'], 9).iloc[-1]
    ema21_1m = ta.trend.ema_indicator(df_1m['close'], 21).iloc[-1] 

    trend_15m = "SIDEWAYS" if is_sideways else ("UP" if price > ema9_15m else "DOWN")
    return {"price": price, "trend_15m": trend_15m, "adx_5m": adx_5m, "ema9_1m": ema9_1m, "ema21_1m": ema21_1m}

# ================= MAIN LOOP =================
print("🚀 JASTON MASTER: DEMO MODE ACTIVE (TESTNET)")

m = {"price": 0, "trend_15m": "SCANNING", "adx_5m": 0, "ema21_1m": 0}
counter = 0

try:
    while True:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total']['USDT']
        
        in_trade = False
        active_pnl = 0.0
        side = None
        
        # Check active positions
        for pos in balance['info']['positions']:
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_trade = True
                    side = "LONG" if amt > 0 else "SHORT"
                    active_pnl = float(pos['unrealizedProfit'])

        if counter % 5 == 0: m = analyze_market()

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🛠️ DEMO TRADING | {datetime.now().strftime('%H:%M:%S')}")
        print(f"--------------------------------------------------")
        print(f"💰 TESTNET WALLET: ${usdt_balance:.2f} | PnL: {active_pnl:.4f}")
        print(f"🔍 15M: {m['trend_15m']} | ADX: {m['adx_5m']:.1f}")
        print(f"--------------------------------------------------")

        if in_trade:
            # EXIT LOGIC (Matched with Analysis)
            if active_pnl <= -STOP_LOSS_AMT:
                print("🔴 SL REACHED ($0.20). Closing...")
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
            elif (side == "LONG" and live_price < m['ema21_1m']) or (side == "SHORT" and live_price > m['ema21_1m']):
                print("⚪ EMA EXIT SIGNAL. Closing...")
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
            elif active_pnl >= TAKE_PROFIT_AMT:
                print("🟢 TP REACHED ($0.40). Closing...")
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
        
        elif m['trend_15m'] != "SIDEWAYS" and m['adx_5m'] > 20:
            qty = (usdt_balance * 0.1 * 20) / live_price # Tumia 10% ya demo wallet
            if m['trend_15m'] == "UP" and live_price > m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'buy', qty)
                print("🚀 DEMO LONG OPENED")
            elif m['trend_15m'] == "DOWN" and live_price < m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'sell', qty)
                print("📉 DEMO SHORT OPENED")

        counter += 1
        time.sleep(2)
except Exception as e:
    print(f"Demo Error: {e}")