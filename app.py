import streamlit as st
import os
import time
import json
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="Jaston Master Trade", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { 
        background: #161b22; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# ================= LOAD DATA FUNCTIONS =================
def get_bot_status():
    if os.path.exists("bot_status.txt"):
        try:
            with open("bot_status.txt", "r") as f:
                return f.read().strip()
        except: return "ERROR"
    return "UNKNOWN"

def load_trade_data():
    """Inasoma faida, hasara na PnL kutoka trade_data.json"""
    default = {"wins": 0, "losses": 0, "profit": 0.0}
    if os.path.exists("trade_data.json"):
        try:
            with open("trade_data.json", "r") as f:
                return json.load(f)
        except: return default
    return default

def get_latest_logs():
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"log_{today}.txt"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                return lines[-8:] # Inaonyesha mistari 8 ya mwisho kwa muonekano bora
        except: return ["Error reading logs."]
    return ["No activity recorded yet today."]

# ================= DATA PROCESSING =================
data = load_trade_data()
wins = data.get("wins", 0)
losses = data.get("losses", 0)
pnl = data.get("profit", 0.0)
total_trades = wins + losses

# ================= UI ELEMENTS =================
st.title("🚀 JASTON MASTER TRADE")

# Status Bar
status = get_bot_status()
if "STOPPED" in status.upper():
    st.error(f"🔴 BOT STATUS: OFFLINE (Stopped)")
else:
    st.success(f"🟢 BOT STATUS: ONLINE (Active)")

st.divider()

# --- ROW 1: TRADING SUMMARY ---
st.subheader("📊 Trading Performance (Today)")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

# Total Trades
m_col1.metric("Total Trades", f"{total_trades}")

# Total Gain (Wins)
m_col2.metric("Total Gain (Wins)", f"✅ {wins}")

# Total Lose (Losses)
m_col3.metric("Total Lose", f"❌ {losses}")

# PnL (Profit and Loss)
pnl_color = "normal" if pnl >= 0 else "inverse"
m_col4.metric("Total PnL (Profit)", f"${pnl:,.2f}", delta=f"{pnl:,.2f}", delta_color=pnl_color)

st.divider()

# --- ROW 2: LOGS AND INFO ---
left, right = st.columns([2, 1])

with left:
    st.subheader("📡 Recent Activity Logs")
    logs = get_latest_logs()
    # Tunatumia box kuonyesha logs
    log_text = "".join(reversed(logs))
    st.code(log_text, language="bash")

with right:
    st.subheader("⚙️ System Info")
    st.info(f"**Current Action:** {status}")
    st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
    
    if st.button("🔄 Manual Refresh"):
        st.rerun()

# Auto Refresh kila baada ya sekunde 10
time.sleep(5)
st.rerun()