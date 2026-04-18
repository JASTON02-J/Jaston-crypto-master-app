import streamlit as st
import json
import os
import time

# ================= CONFIGURATION =================
st.set_page_config(
    page_title="Jaston Master Trade Dashboard",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS kurembesha muonekano
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

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

# ================= HEADER =================
st.title("🚀 JASTON MASTER TRADE")
st.markdown("---")

# ================= TOP METRICS (Statistics) =================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Profit", f"${trade_data.get('profit', 0):.2f}")

with col2:
    st.metric("Wins ✅", trade_data.get('wins', 0))

with col3:
    st.metric("Losses ❌", trade_data.get('losses', 0))

with col4:
    wins = trade_data.get('wins', 0)
    losses = trade_data.get('losses', 0)
    total = wins + losses
    winrate = (wins / total * 100) if total > 0 else 0
    st.metric("Winrate %", f"{winrate:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ================= MAIN CONTENT =================
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("📡 Live Market Monitor")
    
    # Sehemu ya kuonyesha kitendo kinachoendelea (Bot Status)
    if os.path.exists("bot_status.txt"):
        with open("bot_status.txt", "r") as f:
            status = f.read()
        
        # Rangi inabadilika kulingana na neno lililoandikwa
        if "ENTERED" in status:
            st.success(f"**Current Action:** {status}")
        elif "CLOSED" in status:
            st.warning(f"**Current Action:** {status}")
        elif "Side-way" in status:
            st.info(f"**Current Action:** {status} 😴")
        else:
            st.info(f"**Current Action:** {status} 🔍")
    else:
        st.write("Waiting for bot to start sending status...")

    st.divider()
    
    # Kuonyesha Trade iliyo wazi (Active Trade)
    if active_trade:
        st.subheader("📝 Open Position Details")
        side = active_trade['side'].upper()
        color = "green" if side == "BUY" else "red"
        
        st.markdown(f"### <span style='color:{color}'>{side} Position Active</span>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entry Price", f"${active_trade['entry']:,}")
        c2.metric("Stop Loss", f"${active_trade['sl']:,}")
        c3.metric("Take Profit", f"${active_trade['tp']:,}")
        
        st.write(f"**Strategy Used:** {active_trade.get('strategy', 'Triple-TF Sniper')}")
    else:
        st.info("No active trades at the moment. The bot is scanning the market.")

with right_col:
    st.subheader("⚙️ Bot Configuration")
    st.write("**Symbol:** BTC/USDT")
    st.write("**Risk Per Trade:** 1%")
    st.write("**Strategy:** Triple Timeframe (15m, 5m, 1m)")
    st.write("**Indicators:** EMA, ADX, Stoch RSI, Candle Patterns")
    
    if st.button("Refresh Dashboard"):
        st.rerun()

# Auto-refresh kila baada ya sekunde 5
time.sleep(5)
st.rerun()