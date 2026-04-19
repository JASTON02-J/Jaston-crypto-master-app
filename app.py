import streamlit as st
import requests
import json
from datetime import datetime
import time

st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")

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

# LOGIC YA STATUS (Heartbeat Fix)
is_online = False
if data and 'timestamp' in data:
    try:
        last_seen = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
        # Kama bot haijatuma data kwa zaidi ya sekunde 30, weka OFFLINE
        if (datetime.now() - last_seen).total_seconds() < 30:
            is_online = True
    except: is_online = False

if data:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        bg = "#238636" if is_online else "#da3633"
        st.markdown(f'<div class="status-box" style="background-color: {bg}">BOT: {"ONLINE" if is_online else "OFFLINE"}</div>', unsafe_allow_html=True)
    with col2: st.metric("Wallet", f"${data.get('wallet', 0.0):.2f}")
    with col3: st.metric("BTC Price", f"${data.get('price', 0.0):,.1f}")
    with col4: st.metric("Leverage", f"{data.get('leverage', 0)}x")

    st.divider()

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 Indicators")
        st.write(f"15M Trend: {'🟢 UP' if data.get('sig15')=='UP' else '🔴 DOWN' if data.get('sig15')=='DOWN' else '🟡 SIDE'}")
        st.write(f"01M Trend: {'🟢 UP' if data.get('sig1')=='UP' else '🔴 DOWN' if data.get('sig1')=='DOWN' else '🟡 SIDE'}")
        st.progress(min(data.get('adx', 0)/100, 1.0), text=f"ADX: {data.get('adx', 0):.1f}")
        # Hapa tumetumia .get kuzuia KeyError
        st.caption(f"Reason: {data.get('reason', 'Syncing...')}")

    with c2:
        st.subheader("🔥 Execution Room")
        if data.get('in_trade'):
            st.success(f"TRADE EXECUTED: {data.get('side')} | Time: {data.get('executed_at', 'N/A')}")
            st.metric("PnL (%)", f"{data.get('pnl_pct', 0.0):.2f}%")
        else:
            st.info(f"Scanning Market... Status: {data.get('status', 'Scanning')}")
else:
    st.warning("Connecting to GitHub...")

time.sleep(5)
st.rerun()