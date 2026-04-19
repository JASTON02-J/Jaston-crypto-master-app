import streamlit as st
import requests
import json
from datetime import datetime
import time

st.set_page_config(page_title="JASTON DASHBOARD", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .status-card { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

def fetch_data():
    url = "https://raw.githubusercontent.com/JASTON02-J/Jaston-crypto-master-app/master/data.json"
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except: return None

data = fetch_data()

# LOGIC YA ONLINE/OFFLINE (Strict Timeout)
is_online = False
if data:
    last_sync = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
    # Kama sekunde 15 zimepita bila data mpya, hesabu kama bot imezimwa
    if (datetime.now() - last_sync).total_seconds() < 15:
        is_online = True

st.title("🚀 JASTON MASTER TRADE PRO")

# DASHBOARD HEADER
if is_online:
    st.markdown('<div class="status-card" style="background-color: #238636;">SYSTEM STATUS: ONLINE</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-card" style="background-color: #da3633;">SYSTEM STATUS: OFFLINE (BOT STOPPED)</div>', unsafe_allow_html=True)

if data:
    # MSTARI WA KWANZA: WALLET NA PRICE
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wallet Balance", f"${data.get('wallet', 0.0):.2f}")
    c2.metric("Margin Balance", f"${data.get('margin_balance', 0.0):.2f}")
    c3.metric("BTC Price", f"${data.get('price', 0.0):,.1f}")
    c4.metric("PnL (%)", f"{data.get('pnl_pct', 0.0):+.2f}%")

    st.divider()

    # MSTARI WA PILI: TRENDS NA TRADE EXECUTED
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("📊 Market Indicators")
        st.write(f"15M Trend: {data.get('sig15')}")
        st.write(f"05M Trend: {data.get('sig5')}")
        st.write(f"01M Trend: {data.get('sig1')}")
        st.progress(min(data.get('adx', 0)/100, 1.0), text=f"ADX Strength: {data.get('adx', 0):.1f}")

    with col_b:
        st.subheader("🔥 Execution Status")
        if data.get('in_trade'):
            st.success(f"✅ TRADE EXECUTED: {data.get('side')}")
            st.write(f"Margin Used: ${data.get('margin', 0.0):.2f}")
            st.write(f"Live Update: {data.get('timestamp')}")
        else:
            st.info("📡 Scanning... No active trade at the moment.")

else:
    st.warning("Connecting to GitHub data...")

time.sleep(5)
st.rerun()