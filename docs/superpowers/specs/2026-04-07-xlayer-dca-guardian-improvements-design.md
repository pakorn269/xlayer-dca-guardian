# XLayer DCA Guardian — Full-Stack Improvement Design Spec
**Date:** 2026-04-07
**Goal:** Polish and extend existing features to reach both demo-ready and production-ready quality.
**Approach:** Feature-by-feature with inline UI polish (Option B). Four areas tackled in order: Portfolio Split → NLP Parser → Simulation → UI/UX Sweep.

---

## Architecture Overview

No new files are introduced. All changes are improvements within existing boundaries.

| Area | Files Touched | Nature of Change |
|------|--------------|-----------------|
| Portfolio Split | `app.py` (tab3), `simulator.py` | Replace hardcoded mock data with dynamic DCASimulator loops |
| NLP Parser | `main.py` | Stronger regex patterns, input validation, UI feedback |
| Simulation | `simulator.py`, `app.py` | ACB tracking, cost basis chart line, edge case guards |
| UI/UX Polish | `app.py` | Consistent error/loading/empty states, layout improvements |

`onchain_utils.py` and `config.py` are untouched unless a bug is found during implementation.

---

## Section 1: Portfolio Split Tab (Tab 3)

### Problem
Tab 3 renders entirely hardcoded data: a static `split_data` dict (BTC/ETH/BNB), a fake benchmark info string, and a `np.random.randn` chart. Nothing responds to user input.

### UI Changes (`app.py` tab3)
- Replace hardcoded asset table with a `st.multiselect` allowing 2–5 assets from `TOKEN_ADDRESSES` keys.
- Add a `st.number_input` for total investment amount and a funding token selector (USDC/USDT).
- Wrap all inputs in `st.form("portfolio_form")` to prevent expensive rerenders on every widget interaction.
- Add a "Run Portfolio Split Simulation" submit button inside the form.
- Remove hardcoded benchmark selectboxes and the fake "+2.45%" info string.
- Results layout: use `st.columns` to show the comparison table (left) and normalized chart (right) side by side, leveraging the existing `layout="wide"` config.

### Logic Changes
- On form submit: loop over selected assets, instantiate `DCASimulator(token_in, asset, amount/N, interval_days, duration_days)` for each asset (equal-weight split: total ÷ N).
- `interval_days` and `duration_days` are taken from `st.session_state.dca_params` if set, otherwise default to 7 days / 30 days with tab3-local inputs.
- Collect per-asset: `total_invested`, `total_accumulated`, `pnl_perc`, `gas_estimate`, and the `prices` list.
- Render a unified `st.dataframe` with columns: Asset | Amount Invested | Units Accumulated | PNL %.

### Chart
- **Normalize** each asset's price series to base-100 indexed returns: `normalized[i] = (price[i] / price[0]) * 100`.
- Plot all normalized series on a single `st.line_chart` so assets with vastly different price scales (BTC vs ETH) are compared fairly on a shared % return axis.
- All lines start at 100 at day 0 and diverge by relative performance.

### Removals
- `mock_chart_data` (random numpy array)
- `df_split` hardcoded dict
- Hardcoded benchmark selectboxes
- `import numpy as np` (no longer needed in tab3)

---

## Section 2: NLP Parser

### Problem
The regex fallback in `parse_nl_query_local()` misses common interval patterns ("biweekly", "every 2 weeks", "daily", "quarterly"), fails on "buy X with Y" word order, doesn't strip `$` from amounts, and silently defaults to USDC/ETH when tokens are missing with no UI feedback.

### Regex Improvements (`main.py`)

**New interval patterns:**
- `daily` → 1 day
- `biweekly` / `every other week` → 14 days
- `every X weeks` → X × 7 days (currently only catches bare "week")
- `quarterly` / `every 3 months` → 90 days

**Token extraction:**
- Add `sol`, `bnb`, `dai`, `matic` to the token regex (align with `TOKEN_ADDRESSES` keys).
- Handle "buy X with Y" word order (Y is `token_in`, X is `token_out`) in addition to existing "Y to X" pattern.
- Strip `$` currency symbol before parsing amount: `$50` → `50.0`.

**Validation before returning:**
- `amount <= 0` → return `{"error": "Amount must be greater than zero."}`.
- `interval_days > duration_days` → auto-swap them silently (user likely transposed; no error shown).
- `token_in == token_out` → return `{"error": "Token In and Token Out cannot be the same asset."}`.

### Return Contract Change
The function now returns either the normal params dict or `{"error": "<message>"}`. Callers must check for the `"error"` key.

### UI Feedback (`app.py`)
- After calling `parse_nl_query_local()`, check for `"error"` key: show `st.error(result["error"])` and do not set `st.session_state.dca_params`.
- If Ollama succeeded: show `st.info("✓ Parsed via Gemma 4 (Ollama)")`.
- If regex fallback was used: show `st.warning("⚠️ Ollama unavailable — used regex parser. Please review the parameters below.")`.
- Add a `"parser"` key to the return dict (`"ollama"` or `"regex"`) to enable this UI distinction.

### Preserved
- Ollama/Gemma 4 path is untouched.
- Thai language regex patterns preserved.
- CLI `--token-in` / `--token-out` override logic unchanged.

---

## Section 3: Simulation Improvements

### Problem
The simulator lacks Average Cost Basis (ACB) tracking, the chart has no cost basis reference line, and there is no guard against `token_in == token_out`.

### Logic Changes (`simulator.py`)

**ACB tracking:**
- After each trade, compute running average cost: `avg_cost = total_invested_so_far / total_accumulated_so_far`.
- Store `avg_cost` per trade entry in `self.trades`.
- After all trades, expose `self.avg_cost_final` as a public attribute.

**Edge case guard:**
- At the top of `run()`: if `self.token_in == self.token_out`, immediately `return 0.0` with a printed warning. Prevents divide-by-zero in price calculations.

**`get_trades_csv()` update:**
- Add `avg_cost` as a column in the CSV fieldnames and rows. Backward-compatible (new column appended).

### Chart Improvements (`render_chart`)
- Add a horizontal line at `avg_cost_final` in orange/amber, labeled "Avg Cost Basis".
- Add a dashed horizontal line at `prices[-1]` (final price), labeled "Current Price".
- These two references let the user instantly see whether the strategy is above or below breakeven.

### UI Changes (`app.py`)
- Add a 4th metric card in the simulation results row: `"Avg Cost Basis"` showing `self.avg_cost_final` formatted as `X.XXXX token_in per token_out`.
- Before instantiating `DCASimulator`, check `dca_params["token_in"] == dca_params["token_out"]` and show `st.error("Token In and Token Out cannot be the same asset.")` — block the simulation.

### Preserved
- Mock price generation (seeded random from live anchor) — correct behavior.
- Chart save path (`dca_simulation_chart.png`).
- `save_history()` JSON format — no changes to existing keys.

---

## Section 4: UI/UX Polish

### Problem
The UI has inconsistent empty states, missing loading spinners in tab3, a misleading hardcoded testnet balance, and missed opportunities to use the existing wide layout.

### Empty States (`app.py`)
- **Tab 1:** When `st.session_state.dca_params` is None, show `st.info("Parse a strategy above to see simulation options.")` instead of nothing.
- **Tab 3:** When no assets are selected (before form submit), show `st.info("Select at least 2 assets to run a portfolio comparison.")`.
- **Simulation history:** Replace bare `st.write("No history found.")` with a styled `st.info("No simulations run yet.")`.

### Loading States
- Tab 3 "Run Portfolio Split Simulation": wrap the simulator loop in `st.spinner(f"Running simulations for {len(selected_assets)} assets...")`.
- Tab 1 and Tab 2 already have spinners — no changes needed.

### Error State Consistency
- All non-sidebar errors use `st.error()`. Sidebar errors use `st.sidebar.error()`. The mainnet warning intentionally uses `st.sidebar.error()` — keep it alarming.

### Layout
- Add `st.markdown("<br>", unsafe_allow_html=True)` separator between the strategy metrics row and the simulation/execution action buttons for visual breathing room (already exists in one place; make consistent).

### Sidebar Improvements
- Testnet balance: append `(est.)` → `🔹 **Testnet Portfolio:** $15,000.00 (est.)` to clarify it is mocked.
- Treasury metric zero state: if `treasury["balance"] == 0.0`, show `st.sidebar.info("No fees collected yet.")` instead of `0.0000 USDC`.

### Simulation History
- Rename expander label from `"📜 View Simulation History"` to `"📜 Past Simulations"`.
- Add `st.caption(f"{len(hist_data)} simulation(s) recorded.")` inside the expander above the dataframe.

### Preserved
- Gradient CSS header (polished, intentional).
- `st.balloons()` on successful swap.
- 3-tab structure — no restructuring.
- `layout="wide"` — already set, just better utilized in tab3.
