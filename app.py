import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")

# CSS Decoration
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .status-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 JASTON MASTER TRADE")

def fetch_data():
    url = "https://raw.githubusercontent.com/JASTON02-J/Jaston-crypto-master-app/master/data.json"
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except: return None

data = fetch_data()

if data:
    last_seen = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
    is_online = (datetime.now() - last_seen).total_seconds() < 120 # Offline after 2 mins

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        bg = "#238636" if is_online else "#da3633"
        st.markdown(f'<div class="status-box" style="background-color: {bg}">BOT: {"ONLINE" if is_online else "OFFLINE"}</div>', unsafe_allow_html=True)
    with col2: st.metric("Wallet", f"${data['wallet']:.2f}")
    with col3: st.metric("BTC Price", f"${data['price']:,.1f}")
    with col4: st.metric("Leverage", f"{data['leverage']}x")

    st.divider()
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 Indicators")
        st.write(f"15M Trend: {'🟢 UP' if data['sig15']=='UP' else '🔴 DOWN' if data['sig15']=='DOWN' else '🟡 SIDE'}")
        st.write(f"01M Trend: {'🟢 UP' if data['sig1']=='UP' else '🔴 DOWN' if data['sig1']=='DOWN' else '🟡 SIDE'}")
        st.progress(min(data['adx']/100, 1.0), text=f"ADX: {data['adx']:.1f}")

    with c2:
        st.subheader("🔥 Active Trade")
        if data['in_trade']:
            st.success(f"{data['side']} | Margin: ${data['margin']:.2f}")
            st.metric("PnL", f"${data['pnl']:.4f}", delta=f"{data['pnl']:.4f}")
        else: st.info("Scanning Market...")
else:
    st.warning("Connecting to GitHub...")