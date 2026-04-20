import ccxt
import pandas as pd
import ta
from datetime import datetime

# ================= CONFIG =================

PAIRS = [
"BTC/USDT",
"ETH/USDT",
"SOL/USDT",
"BNB/USDT"
]

TIMEFRAME = "5m"
HTF = "15m"

STOP_LOSS = 0.01
TAKE_PROFIT = 0.025

INITIAL_BALANCE = 10

# ================= EXCHANGE =================

exchange = ccxt.binance({
"enableRateLimit":True
})

# ================= DATA =================

def get_data(pair,tf):

    bars = exchange.fetch_ohlcv(pair,tf,limit=500)

    df = pd.DataFrame(bars,columns=[
    "time","open","high","low","close","volume"
    ])

    df["time"] = pd.to_datetime(df["time"],unit="ms")

    return df

# ================= INDICATORS =================

def indicators(df):

    df["ema9"] = ta.trend.ema_indicator(df["close"],9)
    df["ema21"] = ta.trend.ema_indicator(df["close"],21)

    df["rsi"] = ta.momentum.RSIIndicator(df["close"],14).rsi()

    adx = ta.trend.ADXIndicator(
    df["high"],
    df["low"],
    df["close"],
    14
    )

    df["adx"] = adx.adx()

    df["vol_ma"] = df["volume"].rolling(20).mean()

    return df

# ================= BACKTEST =================

trades=[]

balance = INITIAL_BALANCE

pair_counter={}

for pair in PAIRS:

    df = get_data(pair,TIMEFRAME)
    htf = get_data(pair,HTF)

    df = indicators(df)

    htf["ema50"]=ta.trend.ema_indicator(htf["close"],50)
    htf["ema200"]=ta.trend.ema_indicator(htf["close"],200)

    df=df.dropna()
    htf=htf.dropna()

    position=None

    for i in range(50,len(df)):

        row=df.iloc[i]

        price=row["close"]

        ema9=row["ema9"]
        ema21=row["ema21"]

        rsi=row["rsi"]
        adx=row["adx"]

        volume=row["volume"]
        vol_ma=row["vol_ma"]

        htf_row=htf.iloc[min(i,len(htf)-1)]

        trend="UP" if htf_row["ema50"]>htf_row["ema200"] else "DOWN"

        signal=None
        score=0

        if ema9>ema21 and trend=="UP":
            signal="LONG"
            score+=1

        elif ema9<ema21 and trend=="DOWN":
            signal="SHORT"
            score+=1

        if rsi>55 or rsi<45:
            score+=1

        if adx>20:
            score+=1

        if volume>vol_ma:
            score+=1

        confidence=(score/4)*100

        if position is None and confidence>=75:

            position={
            "pair":pair,
            "type":signal,
            "entry":price,
            "entry_time":row["time"]
            }

        if position:

            entry=position["entry"]

            if position["type"]=="LONG":

                sl=entry*(1-STOP_LOSS)
                tp=entry*(1+TAKE_PROFIT)

                if row["low"]<=sl:

                    pnl=-STOP_LOSS
                    reason="SL"

                elif row["high"]>=tp:

                    pnl=TAKE_PROFIT
                    reason="TP"

                else:
                    continue

            else:

                sl=entry*(1+STOP_LOSS)
                tp=entry*(1-TAKE_PROFIT)

                if row["high"]>=sl:

                    pnl=-STOP_LOSS
                    reason="SL"

                elif row["low"]<=tp:

                    pnl=TAKE_PROFIT
                    reason="TP"

                else:
                    continue

            profit=balance*pnl
            balance+=profit

            trades.append([
            pair,
            position["type"],
            position["entry_time"],
            row["time"],
            round(profit,3),
            reason
            ])

            pair_counter[pair]=pair_counter.get(pair,0)+1

            position=None

# ================= DASHBOARD =================

print("\n🚀 JASTON FORENSIC BACKTEST (LIVE MIRROR MODE)")
print("============================================================")

print("COIN        TYPE     ENTRY TIME          EXIT TIME           PnL     REASON")
print("--------------------------------------------------------------------------")

for t in trades[:10]:

    coin,typ,entry,exit,pnl,reason=t

    print(f"{coin:<10} {typ:<7} {entry}  {exit}  {pnl:+.3f}   {reason}")

print("==========================================================================")

print("\n🚀 TOTAL TRADES:",len(trades))
print("💰 INITIAL: $",INITIAL_BALANCE)
print("💰 FINAL: $",round(balance,2))
print("📈 NET PROFIT: $",round(balance-INITIAL_BALANCE,4))

print("\n🧠 TRADE ANALYSIS MODE")

if pair_counter:

    most=max(pair_counter,key=pair_counter.get)

    print("📊 MOST ACTIVE MARKET:",most)

print("\n⚠ NOTE: These timestamps can be cross-checked on TradingView for validation")