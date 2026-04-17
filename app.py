import streamlit as st
import json
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="JASTON MASTER TRADE", layout="wide")

st_autorefresh(interval=2000, key="refresh")

DATA_FILE = "trade_data.json"
HISTORY_FILE = "trade_history.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"wins":0, "losses":0, "profit":0}
    with open(DATA_FILE) as f:
        return json.load(f)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)

def get_status():
    if not os.path.exists("bot_status.txt"):
        return "UNKNOWN"
    with open("bot_status.txt") as f:
        return f.read().strip()

st.markdown("<h1 style='text-align:center;color:gold;'>🚀 JASTON MASTER TRADE 🚀</h1>", unsafe_allow_html=True)

status = get_status()

if status == "ACTIVE":
    st.success("🟢 BOT ACTIVE")
elif status == "STOPPED":
    st.error("🔴 BOT STOPPED")
else:
    st.warning("⚠️ UNKNOWN")

data = load_data()
history = load_history()

total = data['wins'] + data['losses']
winrate = (data['wins']/total*100) if total > 0 else 0

col1,col2,col3,col4 = st.columns(4)

col1.metric("Profit", round(data['profit'],4))
col2.metric("Wins", data['wins'])
col3.metric("Losses", data['losses'])
col4.metric("Winrate", round(winrate,2))

st.subheader("Trade History")

for trade in reversed(history[-10:]):
    color = "green" if trade['pnl'] > 0 else "red"
    st.markdown(f"<p style='color:{color};'>{trade}</p>", unsafe_allow_html=True)