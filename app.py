import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")

# Decoration CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .status-card { padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 20px; color: white; }
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
    # Logic ya Heartbeat (EAT Time)
    last_update = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
    diff = (datetime.now() - last_update).total_seconds()
    is_active = diff < 45 # Kama bot iko kimya > 45s, inasoma STOPPED

    # TOP METRICS
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        bg = "#238636" if is_active else "#da3633"
        status_txt = "ONLINE (Active)" if is_active else "STOPPED (Offline)"
        st.markdown(f'<div class="status-card" style="background-color: {bg}">{status_txt}</div>', unsafe_allow_html=True)
    
    with col2: st.metric("Wallet Balance", f"${data['wallet']:.2f}")
    with col3: st.metric("Total Session PnL", f"${data.get('total_pnl', 0.0):+.4f}")
    with col4: st.metric("BTC Price", f"${data['price']:,.1f}")

    st.divider()

    # TRADING INFO
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 Indicators")
        st.write(f"15M Signal: **{data['sig15']}**")
        st.write(f"01M Signal: **{data['sig1']}**")

    with c2:
        st.subheader("🔥 Active Position")
        if data['in_trade'] and is_active:
            st.success(f"{data['side']} Position Open | Margin: ${data['margin']:.2f}")
            st.metric("Floating PnL", f"${data['pnl']:.4f}", delta=f"{data['pnl']:.4f}")
        else:
            st.info("No active trades found at the moment.")

    # EXECUTED TRADES
    st.divider()
    st.subheader("📜 Executed Trade History (Recent)")
    if data.get('history'):
        st.table(pd.DataFrame(data['history']))
    else:
        st.write("Waiting for the first trade to be executed...")
else:
    st.warning("Connecting to Engine...")