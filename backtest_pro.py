import ccxt
import pandas as pd
import ta
import numpy as np
import os
from datetime import datetime

# ================= CONFIGURATION =================
SYMBOL = 'BTC/USDT'
INITIAL_CAPITAL = 10.0  # Default Capital ya $10 kama ulivyotaka

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

print(f"🔄 Inapakua data kwa ajili ya Backtesting...")
bars = exchange.fetch_ohlcv(SYMBOL, timeframe='1m', limit=1500)
df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
df['time'] = pd.to_datetime(df['time'], unit='ms')

# Kupata tarehe za mwanzo na mwisho wa data
start_date = df['time'].iloc[0].strftime('%Y-%m-%d %H:%M')
end_date = df['time'].iloc[-1].strftime('%Y-%m-%d %H:%M')

# ================= INDICATORS (TRIPLE-TF LOGIC) =================
df['ema9_15m'] = ta.trend.ema_indicator(df['close'], window=9 * 15)
df['ema21_15m'] = ta.trend.ema_indicator(df['close'], window=21 * 15)
df['adx_5m'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14 * 5).adx()
df['ema9_5m'] = ta.trend.ema_indicator(df['close'], window=9 * 5)
df['ema9_1m'] = ta.trend.ema_indicator(df['close'], window=9)

# ================= SIMULATION ENGINE =================
df['signal'] = 0
for i in range(1, len(df)):
    is_sideways = abs(df['ema9_15m'].iloc[i] - df['ema21_15m'].iloc[i]) < (df['close'].iloc[i] * 0.0003)
    adx_high = df['adx_5m'].iloc[i] > 20
    
    if not is_sideways and adx_high:
        # BUY Logic
        if df['close'].iloc[i] > df['ema9_15m'].iloc[i] and df['close'].iloc[i] > df['ema9_5m'].iloc[i] and df['close'].iloc[i] > df['ema9_1m'].iloc[i]:
            df.loc[i, 'signal'] = 1
        # SELL Logic
        elif df['close'].iloc[i] < df['ema9_15m'].iloc[i] and df['close'].iloc[i] < df['ema9_5m'].iloc[i] and df['close'].iloc[i] < df['ema9_1m'].iloc[i]:
            df.loc[i, 'signal'] = -1

# Piga hesabu ya faida (Strategy Returns)
df['returns'] = df['close'].pct_change()
df['strategy_returns'] = df['returns'] * df['signal'].shift(1)
df['cumulative_profit'] = (1 + df['strategy_returns'].fillna(0)).cumprod()

final_wallet = INITIAL_CAPITAL * df['cumulative_profit'].iloc[-1]
net_profit_usdt = final_wallet - INITIAL_CAPITAL
total_trades = (df['signal'].diff() != 0).astype(bool).sum()

# ================= DASHBOARD REPORT =================
os.system('cls' if os.name == 'nt' else 'clear')
print(f"📊 JASTON BACKTEST DASHBOARD | {datetime.now().strftime('%H:%M')}")
print(f"--------------------------------------------------")
print(f"📅 PERIOD: {start_date} mpaka {end_date}")
print(f"💰 INITIAL CAPITAL: ${INITIAL_CAPITAL:.2f}")
print(f"💰 FINAL WALLET: ${final_wallet:.2f}")
print(f"📈 NET PROFIT: {'🟢' if net_profit_usdt >=0 else '🔴'} ${net_profit_usdt:.4f}")
print(f"🔄 TOTAL TRADES: {total_trades}")
print(f"--------------------------------------------------")
print(f"🧠 LOGIC STATUS:")
print(f"   Triple-TF Filter: ACTIVE")
print(f"   Sideways Guard: ACTIVE")
print(f"   ADX Strength: ACTIVE")
print(f"--------------------------------------------------")