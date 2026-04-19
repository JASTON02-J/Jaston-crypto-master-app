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

exchange = ccxt.binance({
    'apiKey': API_KEY, 
    'secret': SECRET,
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})

# ================= UTILITIES =================
def get_data(symbol, timeframe, limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
        df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
        return df
    except: return None

def get_signal(df):
    if df is None: return "WAIT"
    last = df.iloc[-1]
    if last['close'] > last['ema9'] > last['ema21']: return "UP"
    if last['close'] < last['ema9'] < last['ema21']: return "DOWN"
    return "SIDE"

# ================= MAIN LOOP =================
os.system('cls' if os.name == 'nt' else 'clear')
print("🚀 JASTON MASTER PRO: INITIALIZING SYSTEMS...")

while True:
    try:
        # 1. Fetch Market & Account Data
        ticker = exchange.fetch_ticker(SYMBOL)
        live_price = ticker['last']
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0.0)
        
        # 2. Get Technicals for Dashboard
        df15 = get_data(SYMBOL, '15m')
        df5 = get_data(SYMBOL, '5m')
        df1 = get_data(SYMBOL, '1m')
        
        sig15 = get_signal(df15)
        sig5 = get_signal(df5)
        sig1 = get_signal(df1)
        
        adx5 = ta.trend.ADXIndicator(df5['high'], df5['low'], df5['close'], 14).adx().iloc[-1] if df5 is not None else 0

        # 3. Position Monitoring
        in_trade = False
        active_pnl = 0.0
        side = None
        margin_used = 0.0
        current_lev = 20
        
        for pos in balance['info'].get('positions', []):
            if pos['symbol'] == SYMBOL.replace('/', ''):
                amt = float(pos['positionAmt'])
                current_lev = int(pos['leverage'])
                if amt != 0:
                    in_trade = True
                    side = "LONG" if amt > 0 else "SHORT"
                    active_pnl = float(pos['unrealizedProfit'])
                    margin_used = (abs(amt) * live_price) / current_lev

        # 4. PROFESSIONAL DASHBOARD
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"🚀 JASTON MASTER PRO | {datetime.now().strftime('%H:%M:%S')}")
        print(f"--------------------------------------------------")
        print(f"💰 WALLET: ${usdt_balance:.2f} | LEVERAGE: {current_lev}x")
        print(f"💵 BTC PRICE: ${live_price:,.2f}")
        print(f"--------------------------------------------------")
        
        def color(s): return "🟢 UP" if s == "UP" else ("🔴 DOWN" if s == "DOWN" else "🟡 SIDE")
        print(f"📊 MARKET ANALYSIS:")
        print(f"   [15M Trend]: {color(sig15)}")
        print(f"   [05M Trend]: {color(sig5)}  (ADX: {adx5:.1f})")
        print(f"   [01M Trend]: {color(sig1)}")
        print(f"--------------------------------------------------")

        if in_trade:
            print(f"🔥 ACTIVE TRADE: {side}")
            print(f"   Margin Used: ${margin_used:.2f} USDT")
            print(f"   PnL Status : {active_pnl:+.4f} USDT")
        else:
            print(f"📡 BOT STATUS: SCANNING FOR ALIGNMENT...")
            # Logic: Entry only if 15M and 1M align and ADX > 20
            if sig15 == sig1 and sig15 != "SIDE" and adx5 > 20:
                if usdt_balance >= 10.0:
                    qty = max(0.001, (usdt_balance * 0.5 * current_lev) / live_price)
                    order_side = 'buy' if sig15 == "UP" else 'sell'
                    exchange.create_market_order(SYMBOL, order_side, qty)
                    print(f"✅ {order_side.upper()} ORDER EXECUTED!")
                else:
                    print("⚠️ INSUFFICIENT BALANCE (Min $10 required)")

        time.sleep(3)

    except Exception as e:
        print(f"❌ System Error: {e}")
        time.sleep(10)