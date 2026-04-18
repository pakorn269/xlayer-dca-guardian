## 2025-03-05 - Lazy Loading Heavy Packages to Optimize Startup
**Learning:** `matplotlib` is a very heavy package to import. Importing it globally in a frequently imported file like `simulator.py` blocks the main thread and can delay application startup (e.g. `main.py --help`) by over 2.5 seconds on slower environments.
**Action:** Move `import matplotlib.pyplot as plt` locally inside functions that actually require charting (e.g., `render_chart`), thus enabling lazy-loading and instantly speeding up initial application loads, script executions, and module resolution.

## 2025-03-05 - Cache File I/O Operations in Streamlit Render Path
**Learning:** Streamlit re-executes the entire script from top to bottom on every user interaction. Placing synchronous file I/O operations (like reading `treasury.json` or `simulation_history.json`) directly in the main render path—or even inside `st.expander` which evaluates its contents on every rerun regardless of whether it is expanded—causes hidden performance bottlenecks that degrade UI responsiveness.
**Action:** Always wrap file I/O and expensive synchronous data fetching in `@st.cache_data(ttl=..., show_spinner=False)` to memoize the results, and remember to clear the cache (`.clear()`) immediately after a state-modifying action (e.g., executing a swap, saving a new simulation) to ensure the UI stays synchronized.

## 2026-04-15 - Skipping Expensive Unused Chart Generation
**Learning:** In the portfolio split simulation (`app.py`), the `DCASimulator.run()` function was generating a matplotlib chart for every asset in the loop, even though the Streamlit UI only uses the raw price data to render a single consolidated chart and discards the individual PNG files. This blocked the main thread with slow, unused side-effects.
**Action:** When reusing functions that trigger expensive side-effects (like generating visual charts) in loops or contexts where those side-effects are unneeded, add an explicit opt-out parameter (e.g., `render_chart=False`) to bypass the bottleneck.
## 2025-04-12 - Skipping Unused Heavy Side-Effects in Loops
**Learning:** Generating unused charts (like `matplotlib` figures) inside loops creates a blocking performance bottleneck, even if the charts aren't displayed. In the `Multi-Asset DCA Split` feature, generating hidden charts took ~0.5s per asset (~2.8s total).
**Action:** Always add an explicit opt-out parameter (e.g., `render_chart=False`) for expensive side-effects when reusing functions in contexts where those side-effects are unneeded.

## 2025-04-17 - Parallelize Blocking I/O in Streamlit
**Learning:** In Streamlit, executing multiple independent slow I/O-bound operations sequentially (such as subprocess CLI calls for multi-asset simulations) can cause significant UI-blocking delays.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` and `executor.map` to parallelize independent operations, preventing main thread UI blocking and significantly decreasing wait times.
## 2025-04-16 - Concurrent execution for slow synchronous I/O loops
**Learning:** Synchronous iterations that execute slow operations like subprocess calls (e.g. `onchainos` CLI) cause UI-blocking delays proportional to the loop length.
**Action:** Parallelize the iterations utilizing `concurrent.futures.ThreadPoolExecutor` to execute the independent slow operations concurrently, drastically reducing the overall execution time.
