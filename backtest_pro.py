import ccxt
import pandas as pd
import ta
import numpy as np
import os
from datetime import datetime

# ================= CONFIGURATION =================
SYMBOL = 'BTC/USDT'
INITIAL_CAPITAL = 10.0 
LEVERAGE = 20 # Tunatumia leverage uliyoweka kwenye bot yako

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

print(f"🔄 Inapakua data za Backtesting...")
bars = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=1500)
df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
df['time'] = pd.to_datetime(df['time'], unit='ms')

# ================= INDICATORS (TRIPLE-TF) =================
df['ema9_15m'] = ta.trend.ema_indicator(df['close'], window=135) # 9 * 15
df['ema21_15m'] = ta.trend.ema_indicator(df['close'], window=315) # 21 * 15
df['adx_5m'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=70).adx() # 14 * 5
df['ema9_1m'] = ta.trend.ema_indicator(df['close'], window=9)

# ================= ENGINE =================
trade_log = []
in_position = False
entry_price = 0
position_type = ""
current_wallet = INITIAL_CAPITAL

for i in range(1, len(df)):
    price = df['close'].iloc[i]
    # Sideways Guard uliyoweka
    is_sideways = abs(df['ema9_15m'].iloc[i] - df['ema21_15m'].iloc[i]) < (price * 0.0003)
    
    if not in_position and not is_sideways and df['adx_5m'].iloc[i] > 20:
        # Check Triple-TF Alignment
        if price > df['ema9_15m'].iloc[i] and price > df['ema9_1m'].iloc[i]:
            in_position, position_type, entry_price = True, "LONG", price
        elif price < df['ema9_15m'].iloc[i] and price < df['ema9_1m'].iloc[i]:
            in_position, position_type, entry_price = True, "SHORT", price

    elif in_position:
        # Exit Logic (Simplified for Backtest)
        exit_long = (position_type == "LONG" and price < df['ema9_1m'].iloc[i])
        exit_short = (position_type == "SHORT" and price > df['ema9_1m'].iloc[i])
        
        if exit_long or exit_short:
            raw_pnl = (price - entry_price)/entry_price if position_type=="LONG" else (entry_price - price)/entry_price
            trade_pnl_usdt = (current_wallet * 0.5) * raw_pnl * LEVERAGE # Tunatumia nusu ya wallet kama margin
            current_wallet += trade_pnl_usdt
            
            trade_log.append({
                'time': df['time'].iloc[i].strftime('%H:%M'),
                'type': position_type,
                'pnl_usdt': trade_pnl_usdt,
                'wallet': current_wallet
            })
            in_position = False

# ================= DASHBOARD =================
os.system('cls' if os.name == 'nt' else 'clear')
print(f"📊 JASTON BACKTEST PRO | {datetime.now().strftime('%H:%M:%S')}")
print(f"--------------------------------------------------")
print(f"{'TIME':<8} {'TYPE':<7} {'PnL (USDT)':<15} {'BALANCE'}")
print(f"--------------------------------------------------")

for t in trade_log:
    icon = "🟢" if t['pnl_usdt'] > 0 else "🔴"
    print(f"{t['time']:<8} {t['type']:<7} {icon} {t['pnl_usdt']:>+8.4f}      ${t['wallet']:.2f}")

print(f"--------------------------------------------------")
net_pnl = current_wallet - INITIAL_CAPITAL
print(f"💰 INITIAL: ${INITIAL_CAPITAL:.2f} | FINAL: ${current_wallet:.2f}")
print(f"📈 NET PROFIT/LOSS: {'🟢' if net_pnl >= 0 else '🔴'} ${net_pnl:.4f}")
print(f"--------------------------------------------------")