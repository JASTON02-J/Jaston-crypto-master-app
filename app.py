import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

# --- CONFIGURATION & THEME ---
st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .status-box { padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 JASTON MASTER TRADE")

# --- DATA FETCHING ---
def fetch_data():
    # Tumia RAW link ya GitHub yako hapa
    url = "https://raw.githubusercontent.com/JASTON02-J/Jaston-crypto-master-app/master/data.json"
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except:
        return None

data = fetch_data()

if data:
    # Time sync (Assuming Bot sends EAT time)
    last_seen = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
    # Heartbeat check: If no update for 2 minutes, show OFFLINE
    is_online = (datetime.now() - last_seen).total_seconds() < 120

    # --- TOP ROW: STATUS & WALLET ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        bg = "#238636" if is_online else "#da3633"
        txt = "ONLINE (Active)" if is_online else "OFFLINE"
        st.markdown(f'<div class="status-box" style="background-color: {bg}">{txt}</div>', unsafe_allow_html=True)
        st.caption(f"Last sync: {data['timestamp']} (EAT)")
    
    with col2:
        st.metric("Wallet Balance", f"${data['wallet']:.2f}")
    with col3:
        st.metric("Live BTC Price", f"${data['price']:,.1f}")
    with col4:
        st.metric("Leverage", f"{data['leverage']}x")

    st.divider()

    # --- MIDDLE ROW: ANALYSIS & ACTIVE TRADES ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 Market Indicators")
        def fmt(sig): return f"🟢 {sig}" if sig=="UP" else (f"🔴 {sig}" if sig=="DOWN" else f"🟡 {sig}")
        st.write(f"**15M Trend:** {fmt(data['sig15'])}")
        st.write(f"**01M Trend:** {fmt(data['sig1'])}")
        st.progress(min(data['adx']/100, 1.0), text=f"ADX Strength: {data['adx']:.1f}")

    with c2:
        st.subheader("🔥 Active Trade Info")
        if data['in_trade']:
            st.success(f"Side: **{data['side']}** | Margin: **${data['margin']:.2f}**")
            st.metric("Unrealized PnL", f"${data['pnl']:.4f}", delta=f"{data['pnl']:.4f}")
        else:
            st.info("No active trades. Bot is scanning markets...")

    # --- BOTTOM: TRADE HISTORY ---
    st.divider()
    st.subheader("📜 Recent Executed Trades")
    if data.get('history'):
        st.table(pd.DataFrame(data['history']))
    else:
        st.write("Session History: No trades executed yet.")
else:
    st.warning("🔄 Connecting to GitHub Data... Please ensure Bot is running.")

st.empty()