import streamlit as st
import os
import time
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="Jaston Master Trade", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { background: #161b22; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ================= LOAD DATA =================
def get_bot_status():
    if os.path.exists("bot_status.txt"):
        with open("bot_status.txt", "r") as f:
            return f.read().strip()
    return "UNKNOWN"

def get_latest_logs():
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"log_{today}.txt"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            return lines[-5:] # Inaonyesha mistari 5 ya mwisho
    return ["No logs found for today."]

# ================= UI ELEMENTS =================
st.title("🚀 JASTON MASTER TRADE")

# Status Bar
status = get_bot_status()
if "STOPPED" in status.upper():
    st.error(f"🔴 BOT STATUS: OFFLINE (Stopped)")
else:
    st.success(f"🟢 BOT STATUS: ONLINE (Active)")

st.divider()

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Profit", "$0.00") # Hapa unaweza kuunganisha trade_data.json
col2.metric("Active Symbol", "BTC/USDT")
col3.metric("Strategy", "Triple TF")

st.divider()

# Main Layout
left, right = st.columns([2, 1])

with left:
    st.subheader("📡 Recent Activity Logs (Ripoti ya Leo)")
    logs = get_latest_logs()
    for log in reversed(logs):
        st.text(log.strip())

with right:
    st.subheader("⚙️ Bot Info")
    st.info(f"**Current Action:** {status}")
    if st.button("Manual Refresh"):
        st.rerun()

# Auto Refresh
time.sleep(5)
st.rerun()