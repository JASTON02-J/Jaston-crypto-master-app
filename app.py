import streamlit as st
import json
import pandas as pd
import time

st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")

st.title("🚀 JASTON MASTER TRADE")

def load_json(file):
    try:
        return json.load(open(file))
    except:
        return {}

data = load_json("dashboard.json")
trades = load_json("trades.json")

# STATUS
status = data.get("status", "STOPPED")
st.markdown(f"### Status: {'🟢 ACTIVE' if status=='ACTIVE' else '🔴 STOPPED'}")

# METRICS
col1, col2, col3 = st.columns(3)
col1.metric("💰 Balance", data.get("balance",0))
col2.metric("📊 Markets", len(data.get("results",[])))
col3.metric("🔥 Best", data.get("best",{}).get("symbol","-"))

st.divider()

# MARKET TABLE
st.subheader("📊 Market Scanner")
st.dataframe(pd.DataFrame(data.get("results",[])), use_container_width=True)

# TRADES
st.subheader("📜 Trade History")

if trades:
    df = pd.DataFrame(trades)

    # PnL CALCULATION
    total_pnl = df["pnl"].sum()
    st.metric("📈 Total PnL", total_pnl)

    st.dataframe(df, use_container_width=True)
else:
    st.info("No trades yet")

time.sleep(5)
st.rerun()