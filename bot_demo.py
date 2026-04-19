import ccxt
import pandas as pd
import ta
import time
import os
from datetime import datetime

# ================= CONFIGURATION =================
API_KEY = 'OpL4QPs6fOoX8g3DcwreryHY6LS5Yn0ZJsYMktiTmql6tAk6drC5JCY6PXfV7B6o'
SECRET = 'IRwPbetlVoqRsgHWz45LwBhPq73cvo4ig2rb1zl4RuMNWYGYCdkXhpQ8ltbEM633'
SYMBOL = 'BTC/USDT'

# Tofauti hapa: Tunatumia sandbox mode badala ya kulazimisha URL
exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})
exchange.set_sandbox_mode(True) # Hii ndio swichi ya kuingia kwenye Testnet Website

# ================= RISK MANAGEMENT =================
FIXED_MARGIN_USDT = 10.0
STOP_LOSS_AMT = 0.20
TAKE_PROFIT_AMT = 0.40
LEVERAGE = 20

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
os.system('cls' if os.name == 'nt' else 'clear')
print("🚀 JASTON MASTER BOT (DEMO) IS CONNECTING...")

m = {"price": 0, "trend_15m": "SCANNING", "adx_5m": 0, "ema21_1m": 0}
counter = 0

try:
    try: exchange.set_leverage(LEVERAGE, SYMBOL)
    except: pass

    while True:
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total']['USDT']
        
        in_trade = False
        active_pnl = 0.0
        side = None
        margin_used = 0.0
        
        for pos in balance['info']['positions']:
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    in_trade = True
                    side = "LONG" if amt > 0 else "SHORT"
                    active_pnl = float(pos['unrealizedProfit'])
                    margin_used = (abs(amt) * live_price) / LEVERAGE

        if counter % 5 == 0: m = analyze_market()

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER BOT (DEMO) | {datetime.now().strftime('%H:%M:%S')}")
        print(f"--------------------------------------------------")
        print(f"💰 WALLET: {usdt_balance:.2f} USDT | ⚙️ LEVERAGE: {LEVERAGE}x")
        print(f"💵 LIVE PRICE: ${live_price:,.2f}")
        print(f"--------------------------------------------------")
        
        t15m_color = "🟢" if m['trend_15m'] == "UP" else ("🔴" if m['trend_15m'] == "DOWN" else "🟡")
        print(f"🔍 MARKET DIRECTION:")
        print(f"   [15M Trend]: {m['trend_15m']} {t15m_color}")
        print(f"   [5M ADX]: {m['adx_5m']:.1f}")
        print(f"--------------------------------------------------")

        if in_trade:
            pnl_icon = "🟢" if active_pnl >= 0 else "🔴"
            print(f"🔥 ACTIVE TRADE ({side}):")
            print(f"   Margin Used: {margin_used:.2f} USDT")
            print(f"   Live PnL: {pnl_icon} {active_pnl:.4f} USDT")
            # Logics za exit ziko hapa kama kawaida...

        elif m['trend_15m'] != "SIDEWAYS" and m['adx_5m'] > 20:
            qty = (FIXED_MARGIN_USDT * LEVERAGE) / live_price 
            if m['trend_15m'] == "UP" and live_price > m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'buy', qty)
            elif m['trend_15m'] == "DOWN" and live_price < m['ema9_1m']:
                exchange.create_market_order(SYMBOL, 'sell', qty)

        counter += 1
        time.sleep(2)
except Exception as e:
    print(f"Error: {e}")