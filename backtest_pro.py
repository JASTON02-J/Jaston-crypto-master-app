import ccxt
import pandas as pd
import ta
import numpy as np
import os
from datetime import datetime

# ================= CONFIGURATION =================
SYMBOL = 'BTC/USDT'
INITIAL_CAPITAL = 10.0 
LEVERAGE = 20

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

print(f"Connecting to exchange...")
print(f"Fetching historical data for {SYMBOL}...")
print(f"Downloading 5000 candles for deep analysis. Please wait...")

bars = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=5000)
df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
df['time'] = pd.to_datetime(df['time'], unit='ms')

# ================= INDICATORS (TRIPLE-TF) =================
df['ema9_15m'] = ta.trend.ema_indicator(df['close'], window=135)
df['ema21_15m'] = ta.trend.ema_indicator(df['close'], window=315)
df['adx_5m'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=70).adx()
df['ema9_5m'] = ta.trend.ema_indicator(df['close'], window=45)
# Tumeongeza EMA21 kwa ajili ya Exit salama zaidi
df['ema9_1m'] = ta.trend.ema_indicator(df['close'], window=9)
df['ema21_1m'] = ta.trend.ema_indicator(df['close'], window=21)

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
        if price > df['ema9_15m'].iloc[i] and price > df['ema9_5m'].iloc[i] and price > df['ema9_1m'].iloc[i]:
            in_position, position_type, entry_price = True, "LONG", price
            entry_time = df['time'].iloc[i]
        elif price < df['ema9_15m'].iloc[i] and price < df['ema9_5m'].iloc[i] and price < df['ema9_1m'].iloc[i]:
            in_position, position_type, entry_price = True, "SHORT", price
            entry_time = df['time'].iloc[i]

    elif in_position:
        # BORESHA EXIT: Tunatumia EMA 21 badala ya 9 ili kuipa trade nafasi
        exit_long = (position_type == "LONG" and price < df['ema21_1m'].iloc[i])
        exit_short = (position_type == "SHORT" and price > df['ema21_1m'].iloc[i])
        
        if exit_long or exit_short:
            raw_pnl = (price - entry_price)/entry_price if position_type=="LONG" else (entry_price - price)/entry_price
            # Piga hesabu ya PnL kwa kutumia 20x leverage
            trade_pnl_usdt = (current_wallet * 0.5) * raw_pnl * LEVERAGE 
            current_wallet += trade_pnl_usdt
            
            trade_log.append({
                'date': entry_time.strftime('%Y-%m-%d'),
                'time': entry_time.strftime('%H:%M'),
                'type': position_type,
                'pnl_usdt': trade_pnl_usdt,
                'wallet': current_wallet
            })
            in_position = False

# ================= DASHBOARD =================
os.system('cls' if os.name == 'nt' else 'clear')
print(f"📊 JASTON MASTER BACKTEST REPORT | {datetime.now().strftime('%H:%M:%S')}")
print(f"----------------------------------------------------------------------")
print(f"{'DATE':<12} {'TIME':<8} {'TYPE':<7} {'PnL (USDT)':<15} {'BALANCE'}")
print(f"----------------------------------------------------------------------")

for t in trade_log:
    icon = "🟢" if t['pnl_usdt'] > 0 else "🔴"
    print(f"{t['date']:<12} {t['time']:<8} {t['type']:<7} {icon} {t['pnl_usdt']:>+8.4f}      ${t['wallet']:.2f}")

print(f"----------------------------------------------------------------------")
net_pnl = current_wallet - INITIAL_CAPITAL
print(f"🚀 TOTAL TRADES: {len(trade_log)}")
print(f"💰 INITIAL: ${INITIAL_CAPITAL:.2f} | FINAL: ${current_wallet:.2f}")
print(f"📈 NET P/L: {'🟢' if net_pnl >= 0 else '🔴'} ${net_pnl:.4f}")
print(f"----------------------------------------------------------------------")