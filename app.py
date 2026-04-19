import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="JASTON DASHBOARD", layout="wide")

def get_remote_data(filename):
    url = f"https://raw.githubusercontent.com/JASTON02-J/Jaston-crypto-master-app/master/{filename}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except: return None

data = get_remote_data("data.json")
history = get_remote_data("history.json")

# ONLINE/STOPPED Logic
is_online = False
if data and data.get("status") == "ONLINE":
    is_online = True

st.title("🦅 JASTON MASTER TRADE PRO")

if is_online:
    st.success("SYSTEM STATUS: ONLINE")
else:
    st.error("SYSTEM STATUS: STOPPED")

if data:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wallet Balance", f"${data.get('wallet', 0.0):.2f}")
    c2.metric("Margin Balance", f"${data.get('margin_balance', 0.0):.2f}")
    c3.metric("BTC Price", f"${data.get('price', 0.0):,.1f}")
    c4.metric("Live PnL (%)", f"{data.get('pnl', 0.0):+.2f}%")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Trends Analysis")
        st.write(f"15M: {data.get('t15', 'N/A')}")
        st.write(f"05M: {data.get('t5', 'N/A')}")
        st.write(f"01M: {data.get('t1', 'N/A')}")

    with col_b:
        st.subheader("🔥 Market Status")
        st.info(f"Reason: {data.get('reason', 'Scanning...')}")
        if data.get('in_trade'):
            st.warning(f"EXECUTED: {data.get('side')}")

    st.divider()
    st.subheader("📜 Trade History")
    if history:
        st.table(pd.DataFrame(history).iloc[::-1])
    else:
        st.write("No history recorded.")

time.sleep(10)
st.rerun()