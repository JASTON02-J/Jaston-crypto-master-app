import streamlit as st
import json
import os
from streamlit_autorefresh import st_autorefresh

# ================= KWEKEA Mipangilio ya Ukurasa =================
st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")
# Inajisafisha kila baada ya sekunde 5 ili kuona mabadiliko ya bot
st_autorefresh(interval=5000, key="statuscheck")

# ================= MAFAILI YA DATA =================
DATA_FILE = "trade_data.json"
HISTORY_FILE = "trade_history.json"
ACTIVE_FILE = "active_trade.json"
STATUS_FILE = "bot_status.txt"

# ================= KAZI ZA KUPAKIA DATA (LOAD FUNCTIONS) =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"wins": 0, "losses": 0, "profit": 0}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"wins": 0, "losses": 0, "profit": 0}

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def load_active_trade():
    if not os.path.exists(ACTIVE_FILE):
        return None
    try:
        with open(ACTIVE_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def get_bot_status():
    if not os.path.exists(STATUS_FILE):
        return "UNKNOWN"
    try:
        with open(STATUS_FILE, "r") as f:
            return f.read().strip().upper()
    except:
        return "UNKNOWN"

# ================= KICHWA CHA HABARI (HEADER) =================
st.markdown("""
<h1 style='text-align:center; color:gold; font-family:sans-serif;'>🚀 JASTON MASTER TRADE 🚀</h1>
""", unsafe_allow_html=True)

# ================= HALI YA BOT (STATUS INDICATOR) =================
status = get_bot_status()

if status == "ACTIVE":
    st.markdown("<div style='padding:10px; border-radius:5px; background-color:rgba(0,255,0,0.1); border:1px solid lime;'><h3 style='color:lime; text-align:center; margin:0;'>🟢 BOT IS RUNNING</h3></div>", unsafe_allow_html=True)
elif status == "STOPPED":
    st.markdown("<div style='padding:10px; border-radius:5px; background-color:rgba(255,0,0,0.1); border:1px solid red;'><h3 style='color:red; text-align:center; margin:0;'>🔴 BOT IS STOPPED</h3></div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='padding:10px; border-radius:5px; background-color:gray;'><h3 style='color:white; text-align:center; margin:0;'>⚪ STATUS UNKNOWN</h3></div>", unsafe_allow_html=True)

st.write("") # Nafasi kidogo

# ================= VIPIMO (METRICS) =================
data = load_data()
total_trades = data['wins'] + data['losses']
winrate = (data['wins'] / total_trades * 100) if total_trades > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Profit", f"${data['profit']:.2f}")
col2.metric("✅ Wins", data['wins'])
col3.metric("❌ Losses", data['losses'])
col4.metric("🎯 Winrate", f"{winrate:.1f}%")

st.markdown("---")

# ================= TRADE INAYOENDELEA (LIVE TRADE) =================
st.subheader("📡 Live Position Details")
active = load_active_trade()

if active:
    color = "lime" if active['side'].lower() == "buy" else "red"
    st.markdown(f"""
    <div style='padding:20px; border-radius:10px; background-color:#1e1e1e; border-left: 5px solid {color};'>
        <h3 style='color:{color}; margin-top:0;'>{active['side'].upper()} POSITION</h3>
        <table style='width:100%; color:white;'>
            <tr><td><b>Entry Price:</b></td><td>{active['entry']:.2f}</td></tr>
            <tr><td><b>Stop Loss:</b></td><td>{active['sl']:.2f}</td></tr>
            <tr><td><b>Take Profit:</b></td><td>{active['tp']:.2f}</td></tr>
            <tr><td><b>Size:</b></td><td>{active['amount']:.4f}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No active trade at the moment.")

st.markdown("---")

# ================= HISTORIA YA TRADE =================
st.subheader("📜 Recent Trade History")
history = load_history()

if not history:
    st.write("No trades recorded yet.")
else:
    # Inaonyesha trade 10 za mwisho
    for trade in reversed(history[-10:]):
        pnl_color = "lime" if trade.get('pnl', 0) > 0 else "red"
        st.markdown(f"""
        <div style='padding:10px; border-radius:5px; background-color:#111; margin-bottom:5px; border: 1px solid #333;'>
            <span style='color:gold;'>{trade.get('side', 'N/A').upper()}</span> | 
            Entry: {trade.get('entry', 0):.2f} | 
            Exit: {trade.get('exit', 0):.2f} | 
            PnL: <span style='color:{pnl_color};'>${trade.get('pnl', 0):.2f}</span>
        </div>
        """, unsafe_allow_html=True)

# ================= MKIA (FOOTER) =================
st.markdown("<br><p style='text-align:center; color:gray;'>⚡ JASTON MASTER TRADE SYSTEM ⚡</p>", unsafe_allow_html=True)