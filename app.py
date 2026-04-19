import streamlit as st
import json
import pandas as pd
import time

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align:center;'>🚀 JASTON MASTER TRADE</h1>", unsafe_allow_html=True)

def load(file):
    try:
        return json.load(open(file))
    except:
        return {}

data = load("dashboard.json")
trades = load("trades.json")

# STATUS
status = data.get("status", "STOPPED")
st.markdown("## 🚦 Bot Status")
st.success("🟢 ACTIVE") if status == "ACTIVE" else st.error("🔴 STOPPED")

# METRICS
c1, c2, c3 = st.columns(3)
c1.metric("💰 Balance", data.get("balance", 0))
c2.metric("⏱ Time", data.get("time", "-"))
c3.metric("📊 Markets", len(data.get("results", [])))

st.divider()

# BEST
best = data.get("best", {})
st.markdown("## 🔥 Best Market")

b1, b2, b3 = st.columns(3)
b1.metric("📈 Symbol", best.get("symbol", "-"))
b2.metric("🎯 Confidence", f"{best.get('confidence',0):.1f}%")
b3.metric("📡 Signal", best.get("signal", "-"))

st.divider()

# TABLE
st.markdown("## 📊 Market Scanner")
st.dataframe(pd.DataFrame(data.get("results", [])), use_container_width=True)

st.divider()

# TRADES
st.markdown("## 📜 Trades")

if trades:
    df = pd.DataFrame(trades)
    st.metric("📉 Total PnL", df["pnl"].sum())
    st.dataframe(df, use_container_width=True)
else:
    st.info("No trades yet 🚫")

time.sleep(5)
st.rerun()