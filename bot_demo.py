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

# REKEBISHO: Kutumia URL za Testnet moja kwa moja kuepuka "Deprecation Error"
exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {
        'defaultType': 'future',
        'urls': {
            'api': {
                'public': 'https://testnet.binancefuture.com/fapi/v1',
                'private': 'https://testnet.binancefuture.com/fapi/v1',
            }
        }
    }
})

# ================= RISK MANAGEMENT =================
FIXED_MARGIN_USDT = 10.0 # Kiasi cha kutumia kwa kila trade
STOP_LOSS_AMT = 0.20     # Hasara ya ukomo ($0.20)
TAKE_PROFIT_AMT = 0.40    # Faida ya ukomo ($0.40)
LEVERAGE = 20

def get_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])

def analyze_market():
    # 15M Trend Analysis
    df_15m = get_data(SYMBOL, '15m')
    ema9_15m = ta.trend.ema_indicator(df_15m['close'], 9).iloc[-1]
    ema21_15m = ta.trend.ema_indicator(df_15m['close'], 21).iloc[-1]
    is_sideways = abs(ema9_15m - ema21_15m) < (df_15m['close'].iloc[-1] * 0.0003)
    
    # 5M Momentum
    df_5m = get_data(SYMBOL, '5m')
    adx_5m = ta.trend.ADXIndicator(df_5m['high'], df_5m['low'], df_5m['close'], 14).adx().iloc[-1]
    
    # 1M Confirmation
    df_1m = get_data(SYMBOL, '1m')
    price = df_1m['close'].iloc[-1]
    ema9_1m = ta.trend.ema_indicator(df_1m['close'], 9).iloc[-1]
    ema21_1m = ta.trend.ema_indicator(df_1m['close'], 21).iloc[-1] 

    trend_15m = "SIDEWAYS" if is_sideways else ("UP" if price > ema9_15m else "DOWN")
    return {"price": price, "trend_15m": trend_15m, "adx_5m": adx_5m, "ema9_1m": ema9_1m, "ema21_1m": ema21_1m}

# ================= MAIN LOOP =================
os.system('cls' if os.name == 'nt' else 'clear')
print("🚀 JASTON MASTER TRADE BOT (DEMO MODE) IS CONNECTING...")

m = {"price": 0, "trend_15m": "SCANNING", "adx_5m": 0, "ema21_1m": 0}
counter = 0

try:
    # Set Leverage
    try: exchange.set_leverage(LEVERAGE, SYMBOL)
    except Exception as e: print(f"Leverage Set Info: {e}")

    while True:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total']['USDT']
        
        in_trade = False
        active_pnl = 0.0
        side = None
        margin_used = 0.0
        amt = 0
        
        # Monitor Position
        for pos in balance['info']['positions']:
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_trade = True
                    side = "LONG" if amt > 0 else "SHORT"
                    active_pnl = float(pos['unrealizedProfit'])
                    margin_used = (abs(amt) * live_price) / LEVERAGE

        if counter % 5 == 0:
            try: m = analyze_market()
            except: pass

        # DASHBOARD (Matched with Live Style)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER BOT (DEMO) | {datetime.now().strftime('%H:%M:%S')}")
        print(f"--------------------------------------------------")
        print(f"💰 WALLET: {usdt_balance:.2f} USDT | ⚙️ LEVERAGE: {LEVERAGE}x")
        print(f"💵 LIVE PRICE: ${live_price:,.2f}")
        print(f"--------------------------------------------------")
        
        t15m_color = "🟢" if m['trend_15m'] == "UP" else ("🔴" if m['trend_15m'] == "DOWN" else "🟡")
        print(f"🔍 MARKET DIRECTION:")
        print(f"   [15M Trend]: {m['trend_15m']} {t15m_color}")
        print(f"   [5M ADX Strength]: {m['adx_5m']:.1f}")
        print(f"--------------------------------------------------")

        if in_trade:
            pnl_icon = "🟢" if active_pnl >= 0 else "🔴"
            print(f"🔥 ACTIVE TRADE ({side}):")
            print(f"   Margin Used: {margin_used:.2f} USDT")
            print(f"   Live PnL: {pnl_icon} {active_pnl:.4f} USDT")
            
            # EXIT LOGIC
            if active_pnl <= -STOP_LOSS_AMT:
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
                print("🛑 STOP LOSS EXECUTED")
            elif (side == "LONG" and live_price < m['ema21_1m']) or (side == "SHORT" and live_price > m['ema21_1m']):
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
                print("⚪ EMA EXIT EXECUTED")
            elif active_pnl >= TAKE_PROFIT_AMT:
                exchange.create_market_order(SYMBOL, 'sell' if side == 'LONG' else 'buy', abs(amt))
                print("💰 TAKE PROFIT EXECUTED")
        
        elif m['trend_15m'] != "SIDEWAYS" and m['adx_5m'] > 20:
            # ENTRY LOGIC ($10 Fixed Margin)
            qty = (FIXED_MARGIN_USDT * LEVERAGE) / live_price 
            if m['trend_15m'] == "UP" and live_price > m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'buy', qty)
                print("🚀 LONG POSITION OPENED")
            elif m['trend_15m'] == "DOWN" and live_price < m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'sell', qty)
                print("📉 SHORT POSITION OPENED")

        counter += 1
        time.sleep(2)

except Exception as e:
    print(f"Critical Bot Error: {e}")
    time.sleep(5)