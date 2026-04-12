# Bolt's Journal — XLayer DCA Guardian

## 2026-04-07 - Duplicate get_swap_quote subprocess call in DCASimulator
**Learning:** `fetch_historical_prices()` and `run()` both called `get_swap_quote()` with identical arguments — one used only `estimated_out`, the other only `est_gas`. Each call spawns an `onchainos` subprocess (~1–3 s round-trip). In Portfolio Split mode with 5 assets this doubled to 10 subprocess calls instead of 5.
**Action:** Cache the full return tuple on `self._cached_gas_estimate` during the first call in `fetch_historical_prices()`, then reuse it in `run()`. Works because `run()` always calls `fetch_historical_prices()` first — the ordering guarantee is structural.

## 2026-04-07 - Streamlit UI blocked by synchronous subprocess
**Learning:** Streamlit reruns the entire script top-to-bottom on almost every UI interaction (e.g. typing in a text area, switching tabs). The application was synchronously calling `get_wallet_balance_usd()` which spawned an `onchainos` subprocess in the main thread for Mainnet (196). This blocked the UI thread by 1-3 seconds per interaction.
**Action:** Use `@st.cache_data(ttl=60)` on slow or blocking external I/O functions that are rendered in Streamlit (like sidebar balances) to drastically speed up UI responsiveness without making architecture changes.

## 2026-04-07 - Synchronous file I/O blocking UI thread on Streamlit reruns
**Learning:** Streamlit re-evaluates closed `st.expander` blocks on every script rerun. A synchronous file read (`json.load(open("simulation_history.json"))`) placed inside the "Past Simulations" expander was executed on every single UI interaction, causing severe UI thread blocking as the file grew linearly (O(N) reads for every state change).
**Action:** Extract the file I/O logic into a standalone function decorated with `@st.cache_data(ttl=60, show_spinner=False)`, and return structured data (e.g., `{"data": data}`) to handle potential read errors gracefully. Explicitly clear the cache using `.clear()` whenever the underlying file is modified (e.g., after saving a new simulation result) to ensure the UI updates correctly without sacrificing performance.
