import streamlit as st
import json
import os
from streamlit_autorefresh import st_autorefresh

# ================= MIPANGILIO =================
st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")
# Inajisafisha kila sekunde 5 ili uone faida inavyobadilika
st_autorefresh(interval=5000, key="datarefresh")

# MAFAILI YA DATA
DATA_FILE = "trade_data.json"
ACTIVE_FILE = "active_trade.json"
STATUS_FILE = "bot_status.txt"

# KAZI ZA KUPAKIA DATA
def load_json(file_path, default):
    if not os.path.exists(file_path): return default
    try:
        with open(file_path, "r") as f: return json.load(f)
    except: return default

def get_bot_status():
    if not os.path.exists(STATUS_FILE): return "UNKNOWN"
    try:
        with open(STATUS_FILE, "r") as f: return f.read().strip().upper()
    except: return "UNKNOWN"

# ================= DASHBOARD UI =================
st.markdown("<h1 style='text-align:center; color:gold;'>🚀 JASTON MASTER TRADE 🚀</h1>", unsafe_allow_html=True)

# HALI YA BOT
status = get_bot_status()
if "ACTIVE" in status:
    st.success(f"🟢 BOT STATUS: {status}")
else:
    st.error(f"🔴 BOT STATUS: {status}")

# VIPIMO VYA FAIDA (METRICS)
data = load_json(DATA_FILE, {"wins": 0, "losses": 0, "profit": 0})
total_trades = data['wins'] + data['losses']
winrate = (data['wins'] / total_trades * 100) if total_trades > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Profit", f"${data['profit']:.2f}")
col2.metric("✅ Wins", data['wins'])
col3.metric("❌ Losses", data['losses'])
col4.metric("🎯 Winrate", f"{winrate:.1f}%")

st.markdown("---")

# TRADE INAYOENDELEA (ACTIVE TRADE)
st.subheader("📡 Live Position Details")
active = load_json(ACTIVE_FILE, None)

if active:
    # Tunatengeneza muonekano mzuri wa trade iliyopo
    color = "lime" if active['side'].lower() == "buy" else "red"
    st.markdown(f"""
    <div style='padding:20px; border-radius:10px; background-color:#1e1e1e; border-left: 10px solid {color};'>
        <h2 style='color:{color}; margin-top:0;'>{active['side'].upper()} POSITION ACTIVE</h2>
        <p style='font-size:20px;'><b>Entry Price:</b> ${active['entry']:,.2f}</p>
        <p style='font-size:20px; color:orange;'><b>Stop Loss (Trailing):</b> ${active['sl']:,.2f}</p>
        <p style='font-size:20px; color:cyan;'><b>Take Profit:</b> ${active['tp']:,.2f}</p>
        <p style='font-size:18px;'><b>Amount:</b> {active['amount']:.4f} BTC</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Searching for new trade opportunities... 🔍")

st.markdown("<br><p style='text-align:center; color:gray;'>Mwisho wa kusasisha: Hivi sasa</p>", unsafe_allow_html=True)