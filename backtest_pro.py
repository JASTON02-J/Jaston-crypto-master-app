import ccxt
import pandas as pd
import ta
import os
from datetime import datetime

# ================= CONFIG =================
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
INITIAL_CAPITAL = 10.0
LEVERAGE = 20

STOP_LOSS_AMT = 0.20
TAKE_PROFIT_AMT = 0.40

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

# ================= FORENSIC LOG =================
trade_log = []

# ================= ANALYZE =================
def get_data(symbol):
    bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=300)
    df = pd.DataFrame(bars, columns=['time','open','high','low','close','vol'])

    df['ema9'] = ta.trend.ema_indicator(df['close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], 21)
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], 14).adx()

    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

# ================= BACKTEST ENGINE =================
wallet = INITIAL_CAPITAL

for symbol in SYMBOLS:

    df = get_data(symbol)

    in_trade = False
    entry = 0
    entry_time = None
    side = ""
    cooldown = 0

    for i in range(2, len(df)):

        price = df['close'].iloc[i]
        time = df['time'].iloc[i]

        ema_up = df['ema9'].iloc[i] > df['ema21'].iloc[i]
        ema_down = df['ema9'].iloc[i] < df['ema21'].iloc[i]

        adx = df['adx'].iloc[i]

        # ================= ENTRY =================
        if not in_trade and cooldown == 0 and adx > 20:

            if ema_up:
                in_trade = True
                entry = price
                entry_time = time
                side = "LONG"

            elif ema_down:
                in_trade = True
                entry = price
                entry_time = time
                side = "SHORT"

        # ================= EXIT =================
        elif in_trade:

            pnl = (price - entry)/entry if side=="LONG" else (entry - price)/entry
            pnl_usdt = wallet * 0.5 * pnl * LEVERAGE

            sl = entry - (entry * 0.005) if side=="LONG" else entry + (entry * 0.005)
            tp = entry + (entry * 0.01) if side=="LONG" else entry - (entry * 0.01)

            exit_sl = pnl_usdt <= -STOP_LOSS_AMT
            exit_tp = pnl_usdt >= TAKE_PROFIT_AMT
            exit_trend = (ema_down if side=="LONG" else ema_up)

            if exit_sl or exit_tp or exit_trend:

                exit_time = time

                wallet += pnl_usdt

                trade_log.append({
                    "symbol": symbol,
                    "type": side,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "entry_price": entry,
                    "exit_price": price,
                    "sl_level": sl,
                    "tp_level": tp,
                    "pnl": pnl_usdt,
                    "reason": "SL" if exit_sl else ("TP" if exit_tp else "TREND")
                })

                in_trade = False
                cooldown = 3   # 🔥 FIX: prevents overtrading

# ================= DASHBOARD =================
os.system('cls' if os.name == 'nt' else 'clear')

print(f"🚀 JASTON FORENSIC BACKTEST (LIVE MIRROR MODE)")
print("====================================================================")

print(f"{'COIN':<8} {'TYPE':<6} {'ENTRY TIME':<20} {'EXIT TIME':<20} {'PnL':<10} {'REASON'}")
print("--------------------------------------------------------------------")

for t in trade_log[-20:]:  # last 20 trades for readability

    print(f"{t['symbol']:<8} {t['type']:<6} "
          f"{str(t['entry_time'])[:19]:<20} "
          f"{str(t['exit_time'])[:19]:<20} "
          f"{t['pnl']:>+8.3f}   {t['reason']}")

print("====================================================================")

print(f"🚀 TOTAL TRADES: {len(trade_log)}")
print(f"💰 INITIAL: ${INITIAL_CAPITAL}")
print(f"💰 FINAL: ${wallet:.2f}")
print(f"📈 NET PROFIT: ${wallet - INITIAL_CAPITAL:.4f}")

print("====================================================================")

# ================= FORENSIC INSIGHT =================
print("🧠 TRADE ANALYSIS MODE")
print(f"📊 MOST ACTIVE MARKET: {max(set([t['symbol'] for t in trade_log]), key=lambda x: [t['symbol'] for t in trade_log].count(x) if trade_log else 'NONE')}")

print(f"⚠️ NOTE: These timestamps can be cross-checked on TradingView for validation")