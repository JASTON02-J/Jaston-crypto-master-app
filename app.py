import streamlit as st
import requests
import json
from datetime import datetime
import time

st.set_page_config(page_title="JASTON DASHBOARD", layout="wide")

# BUSINESS DECORATION
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .status-card { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; }
    .running { background-color: #238636; color: white; border: 1px solid #2ea043; }
    .stopped { background-color: #da3633; color: white; border: 1px solid #f85149; }
    </style>
    """, unsafe_allow_html=True)

def fetch_data():
    url = "https://raw.githubusercontent.com/JASTON02-J/Jaston-crypto-master-app/master/data.json"
    try:
        r = requests.get(url, timeout=3)
        return r.json()
    except: return None

data = fetch_data()

# LOGIC YA STATUS
bot_status = "STOPPED"
if data:
    last_sync = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
    if (datetime.now() - last_sync).total_seconds() < 20:
        bot_status = "RUNNING"

st.title("🦅 JASTON MASTER TRADE PRO")

# STATUS DISPLAY
css_class = "running" if bot_status == "RUNNING" else "stopped"
st.markdown(f'<div class="status-card {css_class}">BOT STATUS: {bot_status}</div>', unsafe_allow_html=True)

if data:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("BTC PRICE", f"${data['price']:,.2f}")
    c2.metric("WALLET", f"${data['wallet']:.2f}")
    c3.metric("LIVE PnL %", f"{data['pnl_pct']:.2f}%", delta=f"${data['pnl']:.2f}")
    c4.metric("LEVERAGE", f"{data['leverage']}x")

    st.divider()
    
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("📡 Signals")
        st.write(f"15M Trend: {data['sig15']}")
        st.write(f"EMA Cross: **{data['crossover']}**")
        st.progress(min(data['adx']/100, 1.0), text=f"ADX: {data['adx']:.1f}")

    with col_right:
        st.subheader("🔥 Active Trade")
        if data['in_trade']:
            st.success(f"Position: {data['side']}")
            st.write(f"Margin: ${data['margin']:.2f}")
            st.write(f"Last Update: {data['timestamp']}")
        else:
            st.info("Scanning for opportunities...")

time.sleep(5)
st.rerun()