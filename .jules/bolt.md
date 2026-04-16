## 2025-03-05 - Lazy Loading Heavy Packages to Optimize Startup
**Learning:** `matplotlib` is a very heavy package to import. Importing it globally in a frequently imported file like `simulator.py` blocks the main thread and can delay application startup (e.g. `main.py --help`) by over 2.5 seconds on slower environments.
**Action:** Move `import matplotlib.pyplot as plt` locally inside functions that actually require charting (e.g., `render_chart`), thus enabling lazy-loading and instantly speeding up initial application loads, script executions, and module resolution.

## 2025-03-05 - Cache File I/O Operations in Streamlit Render Path
**Learning:** Streamlit re-executes the entire script from top to bottom on every user interaction. Placing synchronous file I/O operations (like reading `treasury.json` or `simulation_history.json`) directly in the main render path—or even inside `st.expander` which evaluates its contents on every rerun regardless of whether it is expanded—causes hidden performance bottlenecks that degrade UI responsiveness.
**Action:** Always wrap file I/O and expensive synchronous data fetching in `@st.cache_data(ttl=..., show_spinner=False)` to memoize the results, and remember to clear the cache (`.clear()`) immediately after a state-modifying action (e.g., executing a swap, saving a new simulation) to ensure the UI stays synchronized.

## 2025-04-12 - Skipping Unused Heavy Side-Effects in Loops
**Learning:** Generating unused charts (like `matplotlib` figures) inside loops creates a blocking performance bottleneck, even if the charts aren't displayed. In the `Multi-Asset DCA Split` feature, generating hidden charts took ~0.5s per asset (~2.8s total).
**Action:** Always add an explicit opt-out parameter (e.g., `render_chart=False`) for expensive side-effects when reusing functions in contexts where those side-effects are unneeded.
