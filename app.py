# ================= STREAMLIT DASHBOARD =================
# File name: app.py

import streamlit as st
import json
import os
from streamlit_autorefresh import st_autorefresh
# ================= CONFIG =================
DATA_FILE = "trade_data.json"
HISTORY_FILE = "trade_history.json"

# ================= LOAD DATA =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"wins": 0, "losses": 0, "profit": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

# ================= UI DESIGN =================
st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")
st_autorefresh(interval=2000, key="datarefresh")

st.markdown("""
    <h1 style='text-align: center; color: gold;'>🚀 JASTON MASTER TRADE 🚀</h1>
    <h3 style='text-align: center;'>Professional Trading Dashboard</h3>
    <hr>
""", unsafe_allow_html=True)

# ================= LOAD =================
data = load_data()
history = load_history()

# ================= METRICS =================
total = data['wins'] + data['losses']
winrate = (data['wins'] / total * 100) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Total Profit (USDT)", round(data['profit'], 4))
col2.metric("✅ Wins", data['wins'])
col3.metric("❌ Losses", data['losses'])
col4.metric("🎯 Winrate (%)", round(winrate, 2))

st.markdown("---")

# ================= TRADE HISTORY =================
st.subheader("📜 Trade History")

if len(history) == 0:
    st.info("No trades yet...")
else:
    # Show latest trades first
    history = list(reversed(history))

    for trade in history[:10]:
        pnl_color = "green" if trade['pnl'] > 0 else "red"

        st.markdown(f"""
        <div style='padding:10px; border-radius:10px; margin-bottom:10px; background-color:#111;'>
            <b>Side:</b> {trade['side'].upper()} |
            <b>Entry:</b> {trade['entry']} |
            <b>Exit:</b> {trade['exit']} |
            <b style='color:{pnl_color};'>PnL: {round(trade['pnl'], 4)}</b>
        </div>
        """, unsafe_allow_html=True)

# ================= FOOTER =================
st.markdown("---")
st.markdown("<center>⚡ Powered by JASTON MASTER TRADE ⚡</center>", unsafe_allow_html=True)