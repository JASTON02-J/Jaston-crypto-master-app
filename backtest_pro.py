import ccxt
import pandas as pd
import ta
import os
from datetime import datetime

# ================= CONFIGURATION (Kama Bot ya Live) =================
SYMBOL = 'BTC/USDT'
INITIAL_CAPITAL = 10.0 
LEVERAGE = 20
STOP_LOSS_AMT = 0.20   # Atoke kwa hasara ya $0.20
TAKE_PROFIT_AMT = 0.40  # Atoke kwa faida ya $0.40

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

print(f"Connecting to exchange...")
print(f"Fetching 5000 candles to match Live Bot logic...")

bars = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=5000)
df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])
df['time'] = pd.to_datetime(df['time'], unit='ms')

# ================= INDICATORS (Matched with Live Bot) =================
df['ema9_15m'] = ta.trend.ema_indicator(df['close'], window=135)
df['ema21_15m'] = ta.trend.ema_indicator(df['close'], window=315)
df['adx_5m'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=70).adx()
df['ema9_5m'] = ta.trend.ema_indicator(df['close'], window=45)
df['ema9_1m'] = ta.trend.ema_indicator(df['close'], window=9)
df['ema21_1m'] = ta.trend.ema_indicator(df['close'], window=21) # Hii ndio Trailing Exit

# ================= ENGINE =================
trade_log = []
in_position = False
entry_price = 0
entry_time = None
position_type = ""
current_wallet = INITIAL_CAPITAL

for i in range(1, len(df)):
    price = df['close'].iloc[i]
    is_sideways = abs(df['ema9_15m'].iloc[i] - df['ema21_15m'].iloc[i]) < (price * 0.0003)
    
    if not in_position and not is_sideways and df['adx_5m'].iloc[i] > 20:
        # Entry Logic (Same as Live Bot)
        if price > df['ema9_15m'].iloc[i] and price > df['ema9_1m'].iloc[i]:
            in_position, position_type, entry_price = True, "LONG", price
            entry_time = df['time'].iloc[i]
        elif price < df['ema9_15m'].iloc[i] and price < df['ema9_1m'].iloc[i]:
            in_position, position_type, entry_price = True, "SHORT", price
            entry_time = df['time'].iloc[i]

    elif in_position:
        # Piga hesabu ya PnL ya sasa (Floating PnL)
        raw_pnl = (price - entry_price)/entry_price if position_type=="LONG" else (entry_price - price)/entry_price
        active_pnl_usdt = (current_wallet * 0.5) * raw_pnl * LEVERAGE 
        
        # 1. STOP LOSS CHECK ($0.20)
        exit_sl = active_pnl_usdt <= -STOP_LOSS_AMT
        
        # 2. TAKE PROFIT CHECK ($0.40)
        exit_tp = active_pnl_usdt >= TAKE_PROFIT_AMT
        
        # 3. EMA 21 TRAILING EXIT (Kama ile ya Live)
        exit_ema = (position_type == "LONG" and price < df['ema21_1m'].iloc[i]) or \
                   (position_type == "SHORT" and price > df['ema21_1m'].iloc[i])
        
        if exit_sl or exit_tp or exit_ema:
            current_wallet += active_pnl_usdt
            reason = "SL 🔴" if exit_sl else ("TP 🟢" if exit_tp else "EMA ⚪")
            
            trade_log.append({
                'date': entry_time.strftime('%m-%d'),
                'time': entry_time.strftime('%H:%M'),
                'type': position_type,
                'pnl': active_pnl_usdt,
                'wallet': current_wallet,
                'reason': reason
            })
            in_position = False

# ================= DASHBOARD =================
os.system('cls' if os.name == 'nt' else 'clear')
print(f"📊 JASTON BACKTEST PRO (SYNCED WITH LIVE BOT) | {datetime.now().strftime('%H:%M:%S')}")
print(f"---------------------------------------------------------------------------")
print(f"{'DATE':<8} {'TIME':<8} {'TYPE':<7} {'REASON':<8} {'PnL (USDT)':<15} {'BALANCE'}")
print(f"---------------------------------------------------------------------------")

for t in trade_log:
    print(f"{t['date']:<8} {t['time']:<8} {t['type']:<7} {t['reason']:<8} {t['pnl']:>+8.4f}      ${t['wallet']:.2f}")

print(f"---------------------------------------------------------------------------")
print(f"🚀 TOTAL TRADES: {len(trade_log)}")
print(f"💰 INITIAL: ${INITIAL_CAPITAL:.2f} | FINAL: ${current_wallet:.2f}")
print(f"📈 NET PROFIT: ${current_wallet - INITIAL_CAPITAL:.4f}")
print(f"---------------------------------------------------------------------------")