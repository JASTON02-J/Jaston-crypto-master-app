import streamlit as st
import json
import time
from datetime import datetime

st.set_page_config(layout="wide")

# ================= LOAD DATA =================
def load_data():
    try:
        with open("dashboard.json", "r") as f:
            return json.load(f)
    except:
        return None

# ================= HEADER =================
st.markdown(
    "<h1 style='text-align:center; color:#00ffcc;'>🚀 JASTON MASTER TRADE</h1>",
    unsafe_allow_html=True
)

st.markdown("---")

# ================= AUTO REFRESH =================
placeholder = st.empty()

while True:
    data = load_data()

    with placeholder.container():

        if data is None:
            st.warning("Waiting for bot data...")
        else:
            col1, col2, col3, col4 = st.columns(4)

            # ================= STATUS =================
            col1.metric("🤖 BOT STATUS", data["status"])

            # ================= BALANCE =================
            col2.metric("💰 WALLET (USDT)", f"${data['balance']}")

            # ================= PNL =================
            col3.metric("📈 PnL", f"${data['pnl']}")

            # ================= TIME =================
            col4.metric("⏰ TIME", data["time"])

            st.markdown("---")

            # ================= BEST MARKET =================
            st.subheader("🔥 BEST MARKET")

            best = data["best"]

            st.success(f"""
            SYMBOL: {best['symbol']}
            SIGNAL: {best['signal']}
            CONFIDENCE: {best['confidence']:.1f}%
            """)

            st.markdown("---")

            # ================= MARKET TABLE =================
            st.subheader("📊 MARKET SCANNER")

            for r in data["results"]:
                st.write(
                    f"{r['symbol']} | {r['signal']} | Conf: {r['confidence']:.1f}% | RSI {r['rsi']:.1f} | ADX {r['adx']:.1f}"
                )

            st.markdown("---")

            # ================= TRADE HISTORY =================
            st.subheader("📜 TRADE HISTORY")

            st.info("No trades yet (connect trading logic)")

    time.sleep(5)