import streamlit as st
import json
import os

# Configuration
st.set_page_config(page_title="Jaston Intelligence Dashboard", layout="wide")

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except:
            return default
    return default

# Load Data
trade_data = load_json("trade_data.json", {"wins": 0, "losses": 0, "profit": 0})
active_trade = load_json("active_trade.json", None)

st.title("🚀 Jaston Triple-TF Intelligence")

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Profit", f"${trade_data.get('profit', 0):.2f}")
col2.metric("Wins ✅", trade_data.get('wins', 0))
col3.metric("Losses ❌", trade_data.get('losses', 0))

wins = trade_data.get('wins', 0)
losses = trade_data.get('losses', 0)
winrate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
col4.metric("Winrate", f"{winrate:.1f}%")

st.divider()

# --- LIVE POSITION ---
st.subheader("📡 Live Market Status")
if active_trade:
    color = "green" if active_trade['side'] == 'buy' else "red"
    st.success(f"ACTIVE {active_trade['side'].upper()} POSITION")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Entry:** ${active_trade['entry']:,}")
    c2.write(f"**Stop Loss:** ${active_trade['sl']:,}")
    c3.write(f"**Take Profit:** ${active_trade['tp']:,}")
    st.info(f"Strategy: {active_trade.get('strategy', 'N/A')}")
else:
    st.info("Bot is active and searching for Triple-TF confirmation... 🔍")

# --- BOT LOGS ---
if os.path.exists("bot_status.txt"):
    with open("bot_status.txt", "r") as f:
        status = f.read()
    st.write(f"**Current Action:** {status}")

st.markdown("<br><p style='text-align:center; color:gray;'>Last Update: Just now</p>", unsafe_allow_html=True)