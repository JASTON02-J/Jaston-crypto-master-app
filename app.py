import streamlit as st
import requests
import json
from datetime import datetime
import time
import pandas as pd

st.set_page_config(page_title="JASTON DASHBOARD", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .status-card { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

def get_remote_data(filename):
    url = f"https://raw.githubusercontent.com/JASTON02-J/Jaston-crypto-master-app/master/{filename}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except: return None

data = get_remote_data("data.json")
history = get_remote_data("history.json")

# ONLINE/OFFLINE CHECK (Updated to 5 Minutes)
is_online = False
if data:
    last_sync = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
    # Tofauti ya muda iwe chini ya sekunde 300 (Dakika 5)
    if (datetime.now() - last_sync).total_seconds() < 300:
        is_online = True

st.title("🦅 JASTON MASTER TRADE PRO")

if is_online:
    st.markdown('<div class="status-card" style="background-color: #238636;">SYSTEM STATUS: ONLINE</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-card" style="background-color: #da3633;">SYSTEM STATUS: OFFLINE (BOT STOPPED)</div>', unsafe_allow_html=True)

if data:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wallet Balance", f"${data['wallet']:.2f}")
    c2.metric("Margin Balance", f"${data['margin_balance']:.2f}")
    c3.metric("BTC Price", f"${data['price']:,.1f}")
    c4.metric("Live PnL (%)", f"{data['pnl']:+.2f}%")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Market Indicators")
        st.write(f"Trend: {data['trend']}")
        st.progress(min(data['adx']/100, 1.0), text=f"ADX Strength: {data['adx']:.1f}")

    with col_b:
        st.subheader("🔥 Execution Status")
        if data['in_trade']:
            st.success(f"✅ TRADE EXECUTED: {data['side']}")
            st.write(f"Margin Used: ${data['margin_used']:.2f}")
        else:
            st.info("📡 Scanning market...")

    st.divider()
    st.subheader("📜 Recent Trade History")
    if history:
        st.table(pd.DataFrame(history).iloc[::-1])
    else:
        st.write("Waiting for the first trade history...")

time.sleep(5)
st.rerun()