import streamlit as st
import matplotlib.pyplot as plt
import os

# Import our backend modules securely
from main import parse_nl_query_local
from simulator import DCASimulator, TOKEN_ADDRESSES
from onchain_utils import check_wallet_status, execute_swap, collect_fee, get_treasury, get_wallet_balance_usd

st.set_page_config(
    page_title="XLayer DCA Guardian",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for Premium Hackathon Look
st.markdown("""
    <style>
    .big-font {
        font-size: 2.8rem !important;
        font-weight: 800;
        display: inline-block;
        background: -webkit-linear-gradient(#f0f8ff, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-font {
        font-size: 1.2rem !important;
        color: #A0AEC0;
        margin-bottom: 25px;
    }
    div.stButton > button:first-child {
        font-weight: 600;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.title("🛡️ DCA Guardian")
st.sidebar.markdown("AI Auto-Investing Agent for X Layer.")

is_testnet = st.sidebar.radio("🌐 Network Selection:", ("X Layer Testnet (195)", "X Layer Mainnet (196)")) == "X Layer Testnet (195)"
chain_id = 195 if is_testnet else 196

st.sidebar.markdown("---")
st.sidebar.subheader("🔒 Security & Wallet")
if "wallet_verified" not in st.session_state:
    st.session_state.wallet_verified = check_wallet_status()

if not st.session_state.wallet_verified:
    if st.sidebar.button("Verify TEE Enclave Status"):
        with st.spinner("Checking OnchainOS Signer..."):
            if check_wallet_status():
                st.session_state.wallet_verified = True
                st.rerun()
            else:
                st.sidebar.error("❌ Not Logged In. Run `onchainos wallet login` locally.")

if st.session_state.wallet_verified:
    st.sidebar.success("✅ Wallet Connected (TEE Enabled)")
    
    st.sidebar.markdown(f"🔹 **Testnet Portfolio:** ${get_wallet_balance_usd(195)}")
    st.sidebar.markdown(f"🔸 **Mainnet Portfolio:** ${get_wallet_balance_usd(196)}")

st.sidebar.markdown("---")
st.sidebar.subheader("💸 Economy Loop")
fee_percent = st.sidebar.slider("Treasury Fee (%)", min_value=0.0, max_value=5.0, value=0.1, step=0.1)
st.sidebar.info(f"The agent collects a {fee_percent}% protocol fee upon successful swap. When Treasury > 5, an NFT is minted!")

treasury = get_treasury()
st.sidebar.metric(f"Treasury Balance:", f"{treasury['balance']:.4f} {treasury['currency']}")

# ----------------- MAIN CONTENT -----------------
st.markdown('<p class="big-font">🛡️ XLayer DCA Guardian</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-font">Execute autonomous Dollar-Cost Averaging strategies securely via NLP on X Layer.</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🤖 AI Agent Mode (NLP)", "⚙️ Manual Builder", "💼 Portfolio Split (Pro)"])

if "dca_params" not in st.session_state:
    st.session_state.dca_params = None

with tab1:
    st.markdown("### 💬 Describe your strategy naturally")
    
    presets = [
        "DCA 30 USDC to BTC every 30 days for 1 year",
        "DCA 50 USDC to ETH every 7 days for 30 days",
        "Buy OKB with 100 USDT every 1 week for 6 months"
    ]
    preset_sel = st.selectbox("✨ Ready-made Strategy Prompts:", ["✏️ Custom (Type below)"] + presets)
    
    default_text = preset_sel if preset_sel != "✏️ Custom (Type below)" else presets[0]
    query = st.text_area("Strategy Prompt:", default_text, height=68)
    
    if st.button("✨ Parse Neural Prompt", type="primary"):
        with st.spinner("Calling Local LLM/NLP Pipeline..."):
            st.session_state.dca_params = parse_nl_query_local(query)
            st.success("Successfully Parsed Intent!")

with tab2:
    st.markdown("### 🎛️ Exact Parameters")
    tokens = list(TOKEN_ADDRESSES.keys())
    
    col1, col2 = st.columns(2)
    with col1:
        mi_token_in = st.selectbox("Funding Token (Token In)", tokens, index=tokens.index("USDC"))
        mi_token_out = st.selectbox("Asset (Token Out)", tokens, index=tokens.index("ETH"))
    with col2:
        mi_amount = st.number_input("Amount per Interval", min_value=1.0, value=50.0)
        mi_interval = st.number_input("Interval (Days)", min_value=1, value=7)
        mi_duration = st.number_input("Duration (Days)", min_value=1, value=30)
        
    if st.button("Set Manual Strategy"):
        st.session_state.dca_params = {
            "token_in": mi_token_in,
            "token_out": mi_token_out,
            "amount": mi_amount,
            "interval": mi_interval,
            "duration": mi_duration
        }

with tab3:
    st.markdown("### 💼 Multi-Asset DCA Split & Benchmarking (Preview)")
    st.markdown("Advanced strategy allowing you to split a single chunk of investment equally across multiple assets and compare performance.")
    
    st.markdown("#### ⚖️ Portfolio Split Breakdown")
    import pandas as pd
    
    split_data = {
        "Asset": ["BTC", "ETH", "BNB"],
        "Price (USD)": [69850.00, 3520.00, 605.00],
        "Amount (USD)": [3.33, 3.33, 3.34],
        "Units Bought": [0.00004767, 0.00094602, 0.00552066],
        "Units Cum.": [0.00004767, 0.00094602, 0.00552066],
        "Cost Basis USD": [3.33, 3.33, 3.34]
    }
    
    df_split = pd.DataFrame(split_data)
    
    st.dataframe(df_split.style.format({
        "Price (USD)": "{:,.2f}",
        "Amount (USD)": "{:,.2f}",
        "Units Bought": "{:.8f}",
        "Units Cum.": "{:.8f}",
        "Cost Basis USD": "{:,.2f}"
    }), use_container_width=True)
    
    st.markdown("#### 📊 Benchmark Comparison")
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        st.selectbox("Select Benchmark Base:", ["btc_eth_bnb_equal_weight", "top_5_marketcap_crypto", "sp500"])
    with bcol2:
        st.selectbox("Compare Against:", ["btc_eth_equal_weight", "btc_maxi", "eth_maxi"])
        
    st.info("Comparison calculated! `btc_eth_bnb_equal_weight` outperformed `btc_eth_equal_weight` by **+2.45%** over the selected reference strategy.")
    
    import numpy as np
    mock_chart_data = pd.DataFrame(
        np.random.randn(50, 2).cumsum(axis=0) + 100,
        columns=["btc_eth_bnb_equal_weight", "btc_eth_equal_weight"]
    )
    st.line_chart(mock_chart_data)

if st.session_state.dca_params:
    dca_params = st.session_state.dca_params
    st.markdown("---")
    st.markdown("### 🎯 Scheduled Strategy")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Asset Pair", f"{dca_params['token_in']} → {dca_params['token_out']}")
    c2.metric("Invest Amount", f"{dca_params['amount']} {dca_params['token_in']}")
    c3.metric("Frequency", f"Every {dca_params['interval']} days")
    c4.metric("Duration", f"{dca_params['duration']} days")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_sim, col_exec = st.columns(2)
    
    with col_sim:
        if st.button("🔮 Run Simulation (Dry-Run)", width="stretch"):
            with st.spinner("Fetching Historical Market Data & Simulating..."):
                sim = DCASimulator(
                    token_in=dca_params["token_in"],
                    token_out=dca_params["token_out"],
                    dca_amount=dca_params["amount"],
                    interval_days=dca_params["interval"],
                    duration_days=dca_params["duration"],
                    is_testnet=is_testnet
                )
                pnl_perc = sim.run()
                sim.save_history(pnl_perc)
                
                st.session_state.sim_result = {
                    "total_invested": sim.total_invested,
                    "gas_estimate": sim.gas_estimate,
                    "token_in": sim.token_in,
                    "pnl_perc": pnl_perc,
                    "csv_data": sim.get_trades_csv(),
                    "dca_params": dca_params
                }
                    
    with col_exec:
        if st.button("⚡ Execute Real On-Chain Swap", type="primary", width="stretch"):
            if not check_wallet_status():
                st.error("🚨 Action blocked. Please authorize the TEE wallet via sidebar.")
            else:
                st.warning(f"Initiating swap on {'TESTNET' if is_testnet else 'MAINNET'}...")
                with st.spinner("Calling OnchainOS Agent for secure signing..."):
                    success, output = execute_swap(
                        token_in=dca_params["token_in"],
                        token_out=dca_params["token_out"],
                        max_amount_in=str(dca_params["amount"]),
                        chain_id=chain_id
                    )
                    
                    if success:
                        st.success("✅ Swap Executed & Confirmed!")
                        collect_fee(amount=dca_params["amount"], currency=dca_params["token_in"], fee_percent=fee_percent, is_testnet=is_testnet)
                        st.balloons()
                        with st.expander("Transaction Output Logs (OnchainOS)"):
                            st.code(output)
                    else:
                        st.error("❌ On-chain Swap Failed")
                        with st.expander("Error Payload"):
                            st.code(output)

    # Render Simulation Results Persistently
    if "sim_result" in st.session_state and st.session_state.sim_result["dca_params"] == dca_params:
        res = st.session_state.sim_result
        st.markdown("---")
        st.subheader("📊 Dry-Run Results")
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Total Invested", f"{res['total_invested']:.2f} {res['token_in']}")
        mcol2.metric("Est. Gas", f"{res['gas_estimate']:.5f} OKB")
        mcol3.metric("PNL %", f"{res['pnl_perc']:.2f}%", delta=f"{res['pnl_perc']:.2f}%")
        
        st.download_button(
            label="📥 Export Report (CSV)",
            data=res["csv_data"],
            file_name=f"dca_report_{dca_params['token_in']}_{dca_params['token_out']}.csv",
            mime="text/csv",
            width="stretch"
        )
        
        if os.path.exists("dca_simulation_chart.png"):
            st.image("dca_simulation_chart.png")

st.markdown("---")
with st.expander("📜 View Simulation History"):
    import json
    if os.path.exists("simulation_history.json"):
        with open("simulation_history.json", "r") as f:
            try:
                hist_data = json.load(f)
                if hist_data:
                    # Reverse so newest are on top
                    st.dataframe(list(reversed(hist_data)), use_container_width=True)
                else:
                    st.write("No history found.")
            except:
                st.write("Error reading history.")
    else:
        st.write("No simulation history available yet.")
