import streamlit as st
import json
import os
import time
from datetime import datetime

# ================= CONFIGURATION =================
st.set_page_config(
    page_title="Jaston Master Trade Dashboard",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS kurembesha muonekano
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return default
    return default

# Load Data
trade_data = load_json("trade_data.json", {"wins": 0, "losses": 0, "profit": 0})
active_trade = load_json("active_trade.json", None)

# ================= HEADER & STATUS CHECK =================
st.title("🚀 JASTON MASTER TRADE")

# Feature Mpya: Bot Connectivity Status
if os.path.exists("bot_status.txt"):
    with open("bot_status.txt", "r") as f:
        status_text = f.read()
    
    if "STOPPED" in status_text.upper():
        st.error("🔴 BOT STATUS: STOPPED (OFFLINE)")
    else:
        st.success("🟢 BOT STATUS: ACTIVE (ONLINE)")
else:
    st.warning("⚪ BOT STATUS: INITIALIZING...")

st.markdown("---")

# ================= TOP METRICS (Usizibadilishe) =================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Profit", f"${trade_data.get('profit', 0):.2f}")
with col2:
    st.metric("Wins ✅", trade_data.get('wins', 0))
with col3:
    st.metric("Losses ❌", trade_data.get('losses', 0))
with col4:
    total = trade_data['wins'] + trade_data['losses']
    winrate = (trade_data['wins'] / total * 100) if total > 0 else 0
    st.metric("Winrate %", f"{winrate:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ================= MAIN CONTENT =================
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("📡 Live Market Monitor")
    
    # Sehemu ya Current Action
    if os.path.exists("bot_status.txt"):
        with open("bot_status.txt", "r") as f:
            status = f.read()
        st.info(f"**Current Action:** {status} 🔍")
    else:
        st.write("Waiting for bot data...")

    st.divider()
    
    # Kuonyesha Active Trade (Kama ipo)
    if active_trade:
        st.subheader("📝 Open Position Details")
        side = active_trade['side'].upper()
        color = "green" if side == "BUY" else "red"
        st.markdown(f"### <span style='color:{color}'>{side} Position Active</span>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entry Price", f"${active_trade['entry']:,}")
        c2.metric("Stop Loss", f"${active_trade['sl']:,}")
        c3.metric("Take Profit", f"${active_trade['tp']:,}")
    else:
        st.write("No active trades at the moment. The bot is scanning the market.")

with right_col:
    # Feature ya Bot Configuration (Usizibadilishe)
    st.subheader("⚙️ Bot Configuration")
    st.write("**Symbol:** BTC/USDT")
    st.write("**Risk Per Trade:** 1%")
    st.write("**Strategy:** Triple Timeframe (15m, 5m, 1m)")
    st.write("**Indicators:** EMA, ADX, Stoch RSI, Candle Patterns")
    
    if st.button("Refresh Dashboard"):
        st.rerun()

# Auto-refresh kila baada ya sekunde 5 ili kuona mabadiliko haraka
time.sleep(5)
st.rerun()