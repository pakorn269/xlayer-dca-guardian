# XLayer DCA Guardian — Full-Stack Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish and extend the existing XLayer DCA Guardian Streamlit app across four areas — Portfolio Split (dynamic), NLP Parser (robust), Simulation (ACB + chart), and UI/UX (consistent states) — to be both demo-ready and production-ready.

**Architecture:** All changes are confined to three existing files (`simulator.py`, `main.py`, `app.py`). The order of tasks follows data dependencies: simulator improvements first (since Portfolio Split and the simulation view both consume `DCASimulator`), then NLP parser, then app.py UI work in two passes (Portfolio Split, then Simulation UI and polish). No new modules are introduced.

**Tech Stack:** Python 3.8+, Streamlit, Matplotlib, Pandas, subprocess (onchainos CLI), pytest (new, for tests).

---

## File Map

| File | Changes |
|------|---------|
| `simulator.py` | Add `self.prices`, `self.avg_cost_final`; ACB per trade; token guard; chart horizontal lines; CSV avg_cost column |
| `main.py` | New interval keywords; "buy X with Y" order; `$`-stripping; expanded token list; validation; `"parser"` and `"error"` keys in return |
| `app.py` | Tab 3 full rewrite (form, multiselect, sim loop, normalized chart); NLP feedback; avg_cost metric; token pre-check; empty states; sidebar labels; history polish |
| `tests/test_simulator.py` | New — unit tests for ACB logic and token guard |
| `tests/test_main.py` | New — unit tests for NLP regex edge cases |

---

## Task 1: simulator.py — Token Guard, Expose prices, ACB Tracking

**Files:**
- Modify: `simulator.py`
- Test: `tests/test_simulator.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_simulator.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

# Patch subprocess so onchainos CLI calls don't run
@pytest.fixture(autouse=True)
def mock_subprocess(monkeypatch):
    mock_result = MagicMock()
    mock_result.stdout = '{"ok": false}'
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

from simulator import DCASimulator


def test_same_token_guard_returns_zero():
    sim = DCASimulator("USDC", "USDC", 50, 7, 30)
    result = sim.run()
    assert result == 0.0


def test_prices_exposed_after_run():
    sim = DCASimulator("USDC", "ETH", 50, 7, 30)
    sim.run()
    assert hasattr(sim, "prices")
    assert len(sim.prices) > 0


def test_avg_cost_final_is_positive():
    sim = DCASimulator("USDC", "ETH", 50, 7, 30)
    sim.run()
    assert sim.avg_cost_final > 0


def test_avg_cost_in_trades():
    sim = DCASimulator("USDC", "ETH", 50, 7, 30)
    sim.run()
    assert "avg_cost" in sim.trades[0]
    assert sim.trades[0]["avg_cost"] > 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd C:/VSCODE/xlayer-dca-guardian
python -m pytest tests/test_simulator.py -v
```

Expected: 4 FAILs (AttributeError or AssertionError — `prices`, `avg_cost_final`, `avg_cost` don't exist yet).

- [ ] **Step 3: Add token guard and expose self.prices in run()**

In `simulator.py`, modify `__init__` to initialize new attributes, and `run()` to add the guard and expose prices:

```python
class DCASimulator:
    def __init__(self, token_in: str, token_out: str, dca_amount: float, interval_days: int, duration_days: int, is_testnet: bool = False):
        self.token_in = token_in.upper()
        self.token_out = token_out.upper()
        self.dca_amount = dca_amount
        self.interval_days = interval_days
        self.duration_days = duration_days
        self.is_testnet = is_testnet
        from config import CHAIN_ID_TESTNET, CHAIN_ID_MAINNET
        self.chain_id = CHAIN_ID_TESTNET if is_testnet else CHAIN_ID_MAINNET
        self.trades = []
        self.total_invested = 0.0
        self.total_accumulated = 0.0
        self.gas_estimate = 0.0
        self.prices = []          # NEW: exposed for Portfolio Split chart
        self.avg_cost_final = 0.0  # NEW: exposed after run()
```

In `run()`, add the guard at the top and store prices:

```python
    def run(self) -> float:
        from onchain_utils import get_swap_quote, get_treasury

        # Guard: same token in and out is a no-op
        if self.token_in == self.token_out:
            print(f"[WARN] token_in and token_out are both {self.token_in}. Aborting simulation.")
            return 0.0

        print(f"\n======================================")
        # ... (keep existing print block unchanged) ...

        prices = self.fetch_historical_prices()
        self.prices = prices   # NEW: store for external access
        _, est_gas, _ = get_swap_quote(self.token_in, self.token_out, self.dca_amount, self.chain_id)
```

- [ ] **Step 4: Add ACB tracking inside the trade loop**

Replace the existing trade loop in `run()`:

```python
        for day_num, price in enumerate(prices):
            tokens_bought = self.dca_amount / price
            gas_cost_okb = est_gas

            self.total_invested += self.dca_amount
            self.total_accumulated += tokens_bought
            avg_cost = self.total_invested / self.total_accumulated  # running ACB

            self.trades.append({
                "day": day_num * self.interval_days,
                "price": price,
                "amount_in": self.dca_amount,
                "amount_out": tokens_bought,
                "gas_okb": gas_cost_okb,
                "avg_cost": avg_cost,   # NEW
            })
            self.gas_estimate += gas_cost_okb

        self.avg_cost_final = self.total_invested / self.total_accumulated if self.total_accumulated else 0.0  # NEW
```

- [ ] **Step 5: Run tests — confirm all 4 pass**

```bash
python -m pytest tests/test_simulator.py -v
```

Expected: 4 PASS.

- [ ] **Step 6: Commit**

```bash
git add simulator.py tests/test_simulator.py
git commit -m "feat: add ACB tracking, expose prices, token guard to DCASimulator"
```

---

## Task 2: simulator.py — Chart Horizontal Lines + CSV avg_cost Column

**Files:**
- Modify: `simulator.py`

- [ ] **Step 1: Add avg_cost and current price horizontal lines to render_chart()**

Replace `render_chart` in `simulator.py`:

```python
    def render_chart(self, prices: List[float]):
        """Render a Matplotlib line chart summarizing the strategy."""
        days = [i * self.interval_days for i in range(len(prices))]

        plt.figure(figsize=(10, 5))
        plt.plot(days, prices, color='royalblue', label=f'{self.token_out} Price', linewidth=2)
        plt.scatter(days, prices, color='limegreen', s=50, label='DCA Purchase Point', zorder=5)

        if self.avg_cost_final > 0:
            plt.axhline(
                y=self.avg_cost_final,
                color='orange',
                linestyle='-',
                linewidth=1.5,
                label=f'Avg Cost Basis ({self.avg_cost_final:.4f})'
            )
        if prices:
            plt.axhline(
                y=prices[-1],
                color='gray',
                linestyle='--',
                linewidth=1.5,
                label=f'Current Price ({prices[-1]:.4f})'
            )

        net_str = "Testnet" if self.is_testnet else "Mainnet"
        plt.title(f"XLayer ({net_str}) Auto-DCA Simulator: {self.token_in} to {self.token_out}\nEvery {self.interval_days} Days")
        plt.xlabel("Days")
        plt.ylabel(f"Price ({self.token_in})")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()

        out_path = "dca_simulation_chart.png"
        plt.savefig(out_path, dpi=120)
        plt.close()
        print(f"\n📈 Visual Chart Generated: {os.path.abspath(out_path)}")
```

- [ ] **Step 2: Add avg_cost column to get_trades_csv()**

Replace `get_trades_csv` in `simulator.py`:

```python
    def get_trades_csv(self) -> str:
        """Returns the trades list as a CSV string."""
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["day", "price", "amount_in", "amount_out", "gas_okb", "avg_cost"])
        writer.writeheader()
        for trade in self.trades:
            writer.writerow(trade)
        return output.getvalue()
```

- [ ] **Step 3: Run existing simulator tests to confirm nothing broke**

```bash
python -m pytest tests/test_simulator.py -v
```

Expected: 4 PASS.

- [ ] **Step 4: Commit**

```bash
git add simulator.py
git commit -m "feat: add avg cost basis + current price lines to chart, avg_cost to CSV"
```

---

## Task 3: main.py — NLP Regex Hardening

**Files:**
- Modify: `main.py`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write failing NLP tests**

Create `tests/test_main.py`:

```python
import pytest

# Patch ollama so tests always use regex fallback
import sys
from unittest.mock import MagicMock
sys.modules["ollama"] = MagicMock(side_effect=Exception("no ollama"))

from main import parse_nl_query_local


def test_dollar_sign_stripped():
    result = parse_nl_query_local("DCA $50 USDC to ETH every week for 30 days")
    assert result["amount"] == 50.0


def test_daily_interval():
    result = parse_nl_query_local("DCA 10 USDC to ETH daily for 30 days")
    assert result["interval"] == 1


def test_biweekly_interval():
    result = parse_nl_query_local("DCA 50 USDC to ETH biweekly for 60 days")
    assert result["interval"] == 14


def test_every_other_week_interval():
    result = parse_nl_query_local("DCA 50 USDC to ETH every other week for 60 days")
    assert result["interval"] == 14


def test_quarterly_interval():
    result = parse_nl_query_local("DCA 100 USDC to ETH quarterly for 365 days")
    assert result["interval"] == 90


def test_every_x_weeks_interval():
    result = parse_nl_query_local("DCA 50 USDC to ETH every 3 weeks for 90 days")
    assert result["interval"] == 21


def test_buy_x_with_y_word_order():
    result = parse_nl_query_local("buy BTC with 100 USDC every week for 30 days")
    assert result["token_out"] == "BTC"
    assert result["token_in"] == "USDC"


def test_same_token_returns_error():
    result = parse_nl_query_local("DCA 50 USDC to USDC every 7 days for 30 days")
    assert "error" in result


def test_interval_greater_than_duration_auto_swapped():
    result = parse_nl_query_local("DCA 50 USDC to ETH every 30 days for 7 days")
    assert result["interval"] < result["duration"]


def test_zero_amount_returns_error():
    result = parse_nl_query_local("DCA 0 USDC to ETH every 7 days for 30 days")
    assert "error" in result


def test_parser_key_present():
    result = parse_nl_query_local("DCA 50 USDC to ETH every 7 days for 30 days")
    assert "parser" in result
    assert result["parser"] in ("ollama", "regex")


def test_bnb_token_recognized():
    result = parse_nl_query_local("DCA 50 USDC to BNB every week for 30 days")
    assert result["token_out"] == "BNB"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_main.py -v
```

Expected: most tests FAIL — new patterns and keys don't exist yet.

- [ ] **Step 3: Rewrite the regex fallback block in parse_nl_query_local()**

In `main.py`, inside the `except Exception` block (regex fallback), replace the existing content with:

```python
    except Exception as e:
        print(f"    -> Gemma 4 API failed ({e}). Falling back to Regex Parser...")
        parser_used = "regex"

        # Strip $ currency symbol before amount extraction
        query_stripped = re.sub(r'\$(\d+(?:\.\d+)?)', r'\1', query_lower)

        # Extract amount
        amt_match = re.search(r'(\d+(?:\.\d+)?)', query_stripped)
        amount = float(amt_match.group(1)) if amt_match else 10.0

        # Token extraction: handle "buy X with Y" word order first
        buy_with_match = re.search(r'buy\s+(\w+)\s+with\s+(\w+)', query_lower)
        if buy_with_match:
            token_out = buy_with_match.group(1).upper()
            token_in = buy_with_match.group(2).upper()
        else:
            nlp_tokens = re.findall(r'\b(usdc|usdt|okb|eth|btc|weth|sol|bnb|dai|matic)\b', query_lower)
            token_in = nlp_tokens[0].upper() if len(nlp_tokens) > 0 else None
            token_out = nlp_tokens[1].upper() if len(nlp_tokens) > 1 else None

        # Extract interval — order matters: specific patterns before generic
        if re.search(r'\bdaily\b', query_lower):
            interval_days = 1
        elif re.search(r'\bbiweekly\b|\bevery other week\b', query_lower):
            interval_days = 14
        elif re.search(r'\bquarterly\b', query_lower):
            interval_days = 90
        elif re.search(r'every\s*(\d+)\s*weeks?', query_lower):
            m = re.search(r'every\s*(\d+)\s*weeks?', query_lower)
            if m: interval_days = int(m.group(1)) * 7
        elif re.search(r'ทุก\s*(\d+)\s*วัน|every\s*(\d+)\s*day', query_lower):
            m = re.search(r'(?:ทุก|every)\s*(\d+)\s*(?:วัน|day)', query_lower)
            if m: interval_days = int(m.group(1))
        elif 'week' in query_lower or 'สัปดาห์' in query_lower:
            interval_days = 7
        elif 'month' in query_lower or 'เดือน' in query_lower:
            interval_days = 30

        # Extract duration
        if re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(days?|วัน)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:days?|วัน)', query_lower)
            if m: duration_days = int(m.group(1))
        elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(week|สัปดาห์)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:week|สัปดาห์)', query_lower)
            if m: duration_days = int(m.group(1)) * 7
        elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(month|เดือน)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:month|เดือน)', query_lower)
            if m: duration_days = int(m.group(1)) * 30
        elif re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(years?|ปี)', query_lower):
            m = re.search(r'(?:for|เป็นเวลา)\s*(\d+)\s*(?:years?|ปี)', query_lower)
            if m: duration_days = int(m.group(1)) * 365
```

- [ ] **Step 4: Add parser_used = "ollama" in the success path**

Inside the `try` block, after `print("    -> Successfully parsed via Gemma 4!")`, add:

```python
        parser_used = "ollama"
```

Also add `parser_used = "regex"` at the top of the function (before the try block) as the default so it is always defined:

```python
    parser_used = "regex"  # default; overridden to "ollama" on success
```

- [ ] **Step 5: Add validation and update the return statement**

After the `except` block (after CLI overrides and interactive menu logic), replace the final `return` with:

```python
    # Validation
    if amount <= 0:
        return {"error": "Amount must be greater than zero.", "parser": parser_used}

    if token_in and token_out and token_in.upper() == token_out.upper():
        return {"error": "Token In and Token Out cannot be the same asset.", "parser": parser_used}

    if interval_days > duration_days:
        interval_days, duration_days = duration_days, interval_days
        print(f"[*] Auto-corrected: interval and duration were transposed ({interval_days}d interval, {duration_days}d duration).")

    return {
        "token_in": token_in.upper() if token_in else "USDC",
        "token_out": token_out.upper() if token_out else "ETH",
        "amount": amount,
        "interval": interval_days,
        "duration": duration_days,
        "parser": parser_used,
    }
```

- [ ] **Step 6: Run tests — confirm all pass**

```bash
python -m pytest tests/test_main.py -v
```

Expected: 12 PASS.

- [ ] **Step 7: Smoke test via CLI**

```bash
python main.py --query "buy BTC with \$50 USDC every 2 weeks for 3 months"
```

Expected console output includes:
- `Falling back to Regex Parser...`
- `Selected Pair: USDC -> BTC`
- Interval ~14 days, duration ~90 days.

- [ ] **Step 8: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: harden NLP regex — biweekly/quarterly/daily, buy-X-with-Y, dollar sign, validation"
```

---

## Task 4: app.py — Portfolio Split Tab (Tab 3) Full Rewrite

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the entire tab3 block**

Find the `with tab3:` block in `app.py` (lines ~137–177) and replace it entirely with:

```python
with tab3:
    st.markdown("### 💼 Multi-Asset DCA Split")
    st.markdown("Split a single investment equally across multiple assets and compare normalized performance.")

    available_out_tokens = [t for t in TOKEN_ADDRESSES.keys() if t not in ["USDC", "USDT"]]

    with st.form("portfolio_form"):
        selected_assets = st.multiselect(
            "Select Assets to DCA Into (2–5):",
            options=available_out_tokens,
            default=["ETH", "BTC"],
            max_selections=5,
        )
        col_pf1, col_pf2 = st.columns(2)
        with col_pf1:
            pf_token_in = st.selectbox("Funding Token:", ["USDC", "USDT"])
            pf_total_amount = st.number_input("Total Amount per Interval", min_value=1.0, value=100.0)
        with col_pf2:
            default_interval = st.session_state.dca_params["interval"] if st.session_state.dca_params else 7
            default_duration = st.session_state.dca_params["duration"] if st.session_state.dca_params else 30
            pf_interval = st.number_input("Interval (Days)", min_value=1, value=default_interval)
            pf_duration = st.number_input("Duration (Days)", min_value=1, value=default_duration)

        submit_portfolio = st.form_submit_button("🚀 Run Portfolio Split Simulation")

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
                pf_pnl = pf_sim.run()
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
```

- [ ] **Step 2: Run the Streamlit app and verify Tab 3**

```bash
streamlit run app.py
```

Navigate to Tab 3. Verify:
- Multiselect shows ETH, BTC, OKB, WETH, DAI (not USDC/USDT).
- Changing selections does NOT trigger a rerun (form prevents it).
- Clicking "Run Portfolio Split Simulation" with 2+ assets shows a results table and a normalized line chart.
- Selecting 0 or 1 asset shows the info/warning message.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: rewrite Portfolio Split tab with dynamic DCASimulator loops and normalized chart"
```

---

## Task 5: app.py — NLP Feedback + Simulation UI Improvements

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update the NLP parse button handler (tab1)**

Find the `if st.button("✨ Parse Neural Prompt", type="primary"):` block in `app.py` and replace its contents:

```python
    if st.button("✨ Parse Neural Prompt", type="primary"):
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
```

- [ ] **Step 2: Add token pre-check before simulation runs**

Find the `with col_sim:` block and add the guard before creating `DCASimulator`:

```python
    with col_sim:
        if st.button("🔮 Run Simulation (Dry-Run)", width="stretch"):
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
```

- [ ] **Step 3: Add the 4th metric card (Avg Cost Basis)**

Find the simulation results metrics section:

```python
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Total Invested", f"{res['total_invested']:.2f} {res['token_in']}")
        mcol2.metric("Est. Gas", f"{res['gas_estimate']:.5f} OKB")
        mcol3.metric("PNL %", f"{res['pnl_perc']:.2f}%", delta=f"{res['pnl_perc']:.2f}%")
```

Replace with:

```python
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Total Invested", f"{res['total_invested']:.2f} {res['token_in']}")
        mcol2.metric("Est. Gas", f"{res['gas_estimate']:.5f} OKB")
        mcol3.metric("PNL %", f"{res['pnl_perc']:.2f}%", delta=f"{res['pnl_perc']:.2f}%")
        mcol4.metric("Avg Cost Basis", f"{res.get('avg_cost_final', 0):.4f} {res['token_in']}/{res.get('token_out', '')}")
```

- [ ] **Step 4: Run the app and test simulation flow**

```bash
streamlit run app.py
```

Verify in Tab 1:
- Parse "DCA 0 USDC to USDC every 7 days for 30 days" → two errors shown (zero amount OR same token, whichever fires first in NLP).
- Parse "DCA 50 USDC to ETH every week for 30 days" → warning about regex parser.
- Run simulation → 4 metric cards appear including "Avg Cost Basis".

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: NLP parser feedback, avg cost basis metric, token pre-check in simulation UI"
```

---

## Task 6: app.py — UI/UX Polish Pass

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add empty state to Tab 1 (after strategy params section)**

Find the block that starts `if st.session_state.dca_params:` (around line 179). Directly above it, add:

```python
if not st.session_state.dca_params:
    st.info("Parse a strategy above to see simulation options.")
```

- [ ] **Step 2: Update the sidebar testnet balance label**

Find:

```python
        st.sidebar.markdown(f"🔹 **Testnet Portfolio:** ${get_wallet_balance_usd(195)}")
```

Replace with:

```python
        st.sidebar.markdown(f"🔹 **Testnet Portfolio:** ${get_wallet_balance_usd(195)} (est.)")
```

- [ ] **Step 3: Add treasury zero state in sidebar**

Find:

```python
treasury = get_treasury()
st.sidebar.metric(f"Treasury Balance:", f"{treasury['balance']:.4f} {treasury['currency']}")
```

Replace with:

```python
treasury = get_treasury()
if treasury["balance"] == 0.0:
    st.sidebar.info("No fees collected yet.")
else:
    st.sidebar.metric("Treasury Balance:", f"{treasury['balance']:.4f} {treasury['currency']}")
```

- [ ] **Step 4: Polish the simulation history expander**

Find the expander at the bottom of `app.py`:

```python
with st.expander("📜 View Simulation History"):
    import json
    if os.path.exists("simulation_history.json"):
        with open("simulation_history.json", "r") as f:
            try:
                hist_data = json.load(f)
                if hist_data:
                    st.dataframe(list(reversed(hist_data)), width='stretch')
                else:
                    st.write("No history found.")
            except:
                st.write("Error reading history.")
    else:
        st.write("No simulation history available yet.")
```

Replace with:

```python
with st.expander("📜 Past Simulations"):
    import json
    if os.path.exists("simulation_history.json"):
        with open("simulation_history.json", "r") as f:
            try:
                hist_data = json.load(f)
                if hist_data:
                    st.caption(f"{len(hist_data)} simulation(s) recorded.")
                    st.dataframe(list(reversed(hist_data)), use_container_width=True)
                else:
                    st.info("No simulations run yet.")
            except Exception:
                st.error("Error reading simulation history.")
    else:
        st.info("No simulations run yet.")
```

- [ ] **Step 5: Final end-to-end smoke test**

```bash
streamlit run app.py
```

Checklist:
- [ ] Tab 1 shows info message when no strategy is parsed yet.
- [ ] Sidebar testnet balance shows "(est.)".
- [ ] Sidebar shows "No fees collected yet." when treasury is empty.
- [ ] Parsing a valid strategy shows parser feedback (warning for regex).
- [ ] Simulation runs and shows 4 metric cards including Avg Cost Basis.
- [ ] Chart shows orange "Avg Cost Basis" horizontal line and gray "Current Price" dashed line.
- [ ] Tab 2 manual builder sets strategy correctly.
- [ ] Tab 3 multiselect, form submit, results table + normalized chart all work.
- [ ] History expander shows "Past Simulations" with row count.

- [ ] **Step 6: Commit**

```bash
git add app.py
git commit -m "feat: UI/UX polish — empty states, sidebar labels, treasury zero state, history polish"
```

---

## Self-Review Against Spec

**Spec coverage check:**

| Spec Requirement | Task |
|-----------------|------|
| Portfolio Split: st.form, multiselect, equal-weight | Task 4 |
| Portfolio Split: DCASimulator loop per asset | Task 4 |
| Portfolio Split: normalized base-100 chart | Task 4 |
| Portfolio Split: remove mock data | Task 4 |
| NLP: daily/biweekly/quarterly/every X weeks | Task 3 |
| NLP: "buy X with Y" word order | Task 3 |
| NLP: $ stripping | Task 3 |
| NLP: SOL/BNB/DAI/MATIC tokens | Task 3 |
| NLP: interval > duration auto-swap | Task 3 |
| NLP: error dict return | Task 3 |
| NLP: "parser" key in return | Task 3 |
| Simulation: ACB tracking per trade | Task 1 |
| Simulation: avg_cost_final attribute | Task 1 |
| Simulation: token_in == token_out guard | Task 1 |
| Simulation: chart — avg cost basis line | Task 2 |
| Simulation: chart — current price line | Task 2 |
| Simulation: avg_cost in CSV | Task 2 |
| App: NLP parser feedback (ollama vs regex) | Task 5 |
| App: avg_cost_final 4th metric card | Task 5 |
| App: token pre-check before simulation | Task 5 |
| App: Tab 1 empty state | Task 6 |
| App: Tab 3 empty state (in Task 4 form block) | Task 4 |
| App: Tab 3 spinner | Task 4 |
| App: sidebar (est.) testnet label | Task 6 |
| App: treasury zero state | Task 6 |
| App: history rename + row count | Task 6 |

All spec requirements covered. ✓
