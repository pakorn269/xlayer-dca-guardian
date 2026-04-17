import streamlit as st
import os

# Import our backend modules securely
from main import parse_nl_query_local
from simulator import DCASimulator, TOKEN_ADDRESSES
from onchain_utils import check_wallet_status, execute_swap, collect_fee, get_treasury, get_wallet_balance_usd
from config import IS_TESTNET, ACTIVE_CHAIN_ID, REQUIRE_TESTNET, PROTOCOL_FEE_PERCENT

# ⚡ Bolt Optimization: Cache the synchronous CLI subprocess call to avoid blocking
# the main thread during Streamlit's frequent UI reruns.
@st.cache_data(ttl=60, show_spinner=False)
def cached_get_wallet_balance(cid):
    return get_wallet_balance_usd(cid)

# ⚡ Bolt Optimization: Cache synchronous disk I/O to avoid blocking the main thread
# on every interaction.
@st.cache_data(ttl=60, show_spinner=False)
def cached_get_treasury():
    return get_treasury()

@st.cache_data(ttl=60, show_spinner=False)
def cached_load_simulation_history():
    import json
    if os.path.exists("simulation_history.json"):
        try:
            with open("simulation_history.json", "r") as f:
                return {"data": json.load(f)}
        except Exception:
            return {"error": "Error reading simulation history."}
    return None

st.set_page_config(
    page_title="XLayer DCA Guardian",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for Premium Production Look
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

# Network Selection - Users can toggle environments
is_testnet = st.sidebar.radio(
    "🌐 Network Selection:", 
    ("X Layer Testnet (195)", "X Layer Mainnet (196)"),
    index=0 if IS_TESTNET else 1,
    help="Select the blockchain network to operate on. Testnet uses simulated funds, while Mainnet uses real funds."
) == "X Layer Testnet (195)"

chain_id = ACTIVE_CHAIN_ID
# Security: REQUIRE_TESTNET must override any UI selection to prevent accidental mainnet swaps.
# Without this guard, a user selecting "Mainnet" in the sidebar would bypass the safe-mode flag
# and execute real on-chain transactions with real funds.
if REQUIRE_TESTNET:
    chain_id = 195
    is_testnet = True
    st.sidebar.info("🛡️ Safe Mode ACTIVE (REQUIRE_TESTNET=true). Mainnet is locked out.")
elif is_testnet:
    chain_id = 195
else:
    chain_id = 196
    st.sidebar.error("⚠️ WARNING: You are operating on MAINNET! Real funds will be used.")

st.sidebar.markdown("---")
st.sidebar.subheader("🔒 Security & Wallet")
if "wallet_verified" not in st.session_state:
    st.session_state.wallet_verified = check_wallet_status()

if not st.session_state.wallet_verified:
    if st.sidebar.button("Verify TEE Enclave Status", help="Checks if your TEE wallet is currently authorized via OnchainOS.", use_container_width=True):
        with st.spinner("Checking OnchainOS Signer..."):
            if check_wallet_status():
                st.session_state.wallet_verified = True
                st.rerun()
            else:
                st.sidebar.error("❌ Not Logged In. Run `onchainos wallet login` locally.")

if st.session_state.wallet_verified:
    st.sidebar.success("✅ Wallet Connected (TEE Enabled)")
    
    st.sidebar.markdown(f"🔹 **Testnet Portfolio:** ${cached_get_wallet_balance(195)} (est.)")
    st.sidebar.markdown(f"🔸 **Mainnet Portfolio:** ${cached_get_wallet_balance(196)}")

st.sidebar.markdown("---")
st.sidebar.subheader("💸 Economy Loop")
st.sidebar.info(f"The agent collects a {PROTOCOL_FEE_PERCENT}% protocol fee upon successful swap. When Treasury > 5, an NFT is minted!")

treasury = cached_get_treasury()
if treasury["balance"] == 0.0:
    st.sidebar.info("No fees collected yet. Execute a real swap to start building the treasury!")
else:
    st.sidebar.metric("Treasury Balance:", f"{treasury['balance']:.4f} {treasury['currency']}")

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
    preset_sel = st.selectbox(
        "✨ Ready-made Strategy Prompts:",
        ["✏️ Custom (Type below)"] + presets,
        help="Select a template strategy to auto-fill the prompt area"
    )
    
    default_text = preset_sel if preset_sel != "✏️ Custom (Type below)" else presets[0]
    query = st.text_area(
        "Strategy Prompt:", 
        default_text, 
        height=68,
        help="Describe your DCA strategy in plain English. e.g. 'Buy 50 USDC of ETH every 7 days for 1 month'"
    )
    
    if st.button("✨ Parse Neural Prompt", type="primary", use_container_width=True, help="Processes your natural language text into executable parameters"):
        with st.spinner("Calling Local LLM/NLP Pipeline..."):
            result = parse_nl_query_local(query)

        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state.dca_params = result
            parser = result.get("parser", "regex")
            if parser == "ollama":
                st.success("✓ Parsed via Gemma 4 (Ollama)")
            else:
                st.warning("⚠️ Ollama unavailable — used regex parser. Please review the parameters below.")

with tab2:
    st.markdown("### 🎛️ Exact Parameters")
    tokens = list(TOKEN_ADDRESSES.keys())
    
    col1, col2 = st.columns(2)
    with col1:
        mi_token_in = st.selectbox("Funding Token (Token In)", tokens, index=tokens.index("USDC"), help="The stablecoin or token you are spending")
        mi_token_out = st.selectbox("Asset (Token Out)", tokens, index=tokens.index("ETH"), help="The target asset you want to accumulate")
    with col2:
        mi_amount = st.number_input("Amount per Interval", min_value=1.0, value=50.0, help="Amount of funding token to spend per trade")
        mi_interval = st.number_input("Interval (Days)", min_value=1, value=7, help="Wait time in days between each purchase")
        mi_duration = st.number_input("Duration (Days)", min_value=1, value=30, help="Total length of the strategy in days")
        
    if st.button("Set Manual Strategy", type="primary", use_container_width=True, help="Saves your manual parameters for simulation or execution"):
        st.session_state.dca_params = {
            "token_in": mi_token_in,
            "token_out": mi_token_out,
            "amount": mi_amount,
            "interval": mi_interval,
            "duration": mi_duration
        }

with tab3:
    st.markdown("### 💼 Multi-Asset DCA Split")
    st.markdown("Split a single investment equally across multiple assets and compare normalized performance.")

    import pandas as pd
    available_out_tokens = [t for t in TOKEN_ADDRESSES.keys() if t not in ["USDC", "USDT"]]

    with st.form("portfolio_form"):
        selected_assets = st.multiselect(
            "Select Assets to DCA Into (2–5):",
            options=available_out_tokens,
            default=["ETH", "BTC"],
            max_selections=5,
            help="Choose the assets you want to allocate your funding token towards"
        )
        col_pf1, col_pf2 = st.columns(2)
        with col_pf1:
            pf_token_in = st.selectbox("Funding Token:", ["USDC", "USDT"], help="The stablecoin you will use to fund the investments.")
            pf_total_amount = st.number_input("Total Amount per Interval", min_value=1.0, value=100.0, help="The total amount to invest per interval. This will be divided equally among your selected assets (e.g., $100 across 2 assets = $50 each).")
        with col_pf2:
            default_interval = st.session_state.dca_params["interval"] if st.session_state.dca_params else 7
            default_duration = st.session_state.dca_params["duration"] if st.session_state.dca_params else 30
            pf_interval = st.number_input("Interval (Days)", min_value=1, value=default_interval, help="The number of days between each investment.")
            pf_duration = st.number_input("Duration (Days)", min_value=1, value=default_duration, help="The total duration of the DCA strategy in days.")

        submit_portfolio = st.form_submit_button("🚀 Run Portfolio Split Simulation", use_container_width=True)

    if not selected_assets:
        st.info("Select at least 2 assets to run a portfolio comparison.")
    elif len(selected_assets) < 2:
        st.warning("Please select at least 2 assets.")
    elif submit_portfolio:
        n = len(selected_assets)
        amount_per_asset = pf_total_amount / n
        pf_results = []
        all_normalized = {}

        with st.spinner(f"Running simulations for {n} assets..."):
            for asset in selected_assets:
                pf_sim = DCASimulator(
                    token_in=pf_token_in,
                    token_out=asset,
                    dca_amount=amount_per_asset,
                    interval_days=int(pf_interval),
                    duration_days=int(pf_duration),
                    is_testnet=is_testnet,
                )
                # ⚡ Bolt Optimization: Skip expensive matplotlib chart generation for each asset
                # saving ~0.5s per asset since the split view uses native Streamlit charts
                pf_pnl = pf_sim.run(render_chart=False)
                pf_results.append({
                    "Asset": asset,
                    "Amount Invested": f"{pf_sim.total_invested:.2f} {pf_token_in}",
                    "Units Accumulated": f"{pf_sim.total_accumulated:.6f}",
                    "PNL %": f"{pf_pnl:.2f}%",
                })
                if pf_sim.prices and pf_sim.prices[0] != 0:
                    base = pf_sim.prices[0]
                    all_normalized[asset] = [(p / base) * 100 for p in pf_sim.prices]

        col_table, col_chart = st.columns(2)
        with col_table:
            st.markdown("#### ⚖️ Split Results")
            st.dataframe(pd.DataFrame(pf_results), use_container_width=True)
        with col_chart:
            st.markdown("#### 📈 Normalized Returns (Base 100)")
            if all_normalized:
                st.line_chart(pd.DataFrame(all_normalized))

if not st.session_state.dca_params:
    st.info("Parse a strategy above to see simulation options.")

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
        btn_clicked = st.button("🔮 Run Simulation (Dry-Run)", use_container_width=True, help="Simulates the strategy against historical data without spending funds")
        if btn_clicked or st.session_state.pop('trigger_sim', False):
            if dca_params["token_in"] == dca_params["token_out"]:
                st.error("Token In and Token Out cannot be the same asset.")
            else:
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
                    cached_load_simulation_history.clear()

                    st.session_state.sim_result = {
                        "total_invested": sim.total_invested,
                        "gas_estimate": sim.gas_estimate,
                        "avg_cost_final": sim.avg_cost_final,
                        "token_in": sim.token_in,
                        "token_out": sim.token_out,
                        "pnl_perc": pnl_perc,
                        "csv_data": sim.get_trades_csv(),
                        "dca_params": dca_params
                    }
                    
    with col_exec:
        btn_help = "Signs and executes the transaction on the selected network" if st.session_state.get('wallet_verified', False) else "⚠️ Please authorize the TEE wallet via sidebar to enable execution"
        if st.button("⚡ Execute Real On-Chain Swap", type="primary", use_container_width=True, help=btn_help, disabled=not st.session_state.get('wallet_verified', False)):
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
                        collect_fee(amount=dca_params["amount"], currency=dca_params["token_in"], is_testnet=is_testnet)
                        cached_get_treasury.clear()
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
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Total Invested", f"{res['total_invested']:.2f} {res['token_in']}")
        mcol2.metric("Est. Gas", f"{res['gas_estimate']:.5f} OKB")
        mcol3.metric("PNL %", f"{res['pnl_perc']:.2f}%", delta=f"{res['pnl_perc']:.2f}%")
        mcol4.metric("Avg Cost Basis", f"{res.get('avg_cost_final', 0):.4f} {res['token_in']}/{res.get('token_out', '')}")
        
        st.download_button(
            label="📥 Export Report (CSV)",
            data=res["csv_data"],
            file_name=f"dca_report_{dca_params['token_in']}_{dca_params['token_out']}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        if os.path.exists("dca_simulation_chart.png"):
            st.image("dca_simulation_chart.png")

st.markdown("---")
with st.expander("📜 Past Simulations"):
    hist_result = cached_load_simulation_history()
    if hist_result is None:
        if st.session_state.dca_params:
            st.info("No simulations run yet.")
            if st.button("🔮 Run your first Dry-Run Simulation", use_container_width=True):
                st.session_state.trigger_sim = True
                st.rerun()
        else:
            st.info("No simulations run yet. Parse a strategy above to see your history.")
    elif "error" in hist_result:
        st.error(hist_result["error"])
    else:
        hist_data = hist_result["data"]
        if hist_data:
            st.caption(f"{len(hist_data)} simulation(s) recorded.")
            st.dataframe(list(reversed(hist_data)), use_container_width=True)
        else:
            st.info("No simulations run yet. Try running a dry-run simulation above to see your history.")
