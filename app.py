import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="JASTON DASHBOARD", layout="wide")

# UI Custom CSS kwa ajili ya muonekano safi
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

def get_remote_data(filename):
    # Hakikisha URL hii ni sahihi kulingana na GitHub yako
    url = f"https://raw.githubusercontent.com/JASTON02-J/Jaston-crypto-master-app/master/{filename}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

data = get_remote_data("data.json")
history = get_remote_data("history.json")

# ONLINE/STOPPED Logic
is_online = False
if data and data.get("status") == "ONLINE":
    is_online = True

st.title("🦅 JASTON MASTER TRADE PRO")

# Status Bar
if is_online:
    st.success("SYSTEM STATUS: ONLINE")
else:
    st.error("SYSTEM STATUS: STOPPED")

if data:
    # Safu ya kwanza ya Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wallet Balance", f"${data.get('wallet', 0.0):.2f}")
    c2.metric("Margin Balance", f"${data.get('margin_balance', 0.0):.2f}")
    c3.metric("BTC Price", f"${data.get('price', 0.0):,.1f}")
    c4.metric("Live PnL (%)", f"{data.get('pnl', 0.0):+.2f}%")

    st.divider()

    # Safu ya pili: Trends na Market Status
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Trends Analysis")
        st.write(f"**15M Trend:** {data.get('t15', 'N/A')}")
        st.write(f"**05M Trend:** {data.get('t5', 'N/A')}")
        st.write(f"**01M Trend:** {data.get('t1', 'N/A')}")

    with col_b:
        st.subheader("🔥 Execution Status")
        if data.get('in_trade'):
            st.warning(f"EXECUTING: {data.get('side')}")
            st.info(f"Reason: {data.get('reason', 'Active Trade')}")
        else:
            st.info(f"Reason: {data.get('reason', 'Scanning...')}")

    # --- SEHEMU YA HISTORY (JEDWALI) ---
    st.divider()
    st.subheader("📜 Recent Trade History")
    
    if history and len(history) > 0:
        # Tunatengeneza DataFrame ya Pandas kwa ajili ya Jedwali
        df_history = pd.DataFrame(history)
        
        # Kupanga safu (columns) ziwe na mpangilio mzuri
        # Tunageuza mpangilio ili trade mpya iwe juu (reverse)
        st.table(df_history.iloc[::-1]) 
    else:
        st.info("No trade history recorded yet. Jedwali litaonekana baada ya trade ya kwanza kukamilika.")

else:
    st.warning("Inasubiri data kutoka GitHub... Hakikisha Bot inafanya kazi.")

# Auto refresh kila baada ya sekunde 10
time.sleep(10)
st.rerun()