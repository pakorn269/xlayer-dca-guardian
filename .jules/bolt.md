## 2025-03-05 - Lazy Loading Heavy Packages to Optimize Startup
**Learning:** `matplotlib` is a very heavy package to import. Importing it globally in a frequently imported file like `simulator.py` blocks the main thread and can delay application startup (e.g. `main.py --help`) by over 2.5 seconds on slower environments.
**Action:** Move `import matplotlib.pyplot as plt` locally inside functions that actually require charting (e.g., `render_chart`), thus enabling lazy-loading and instantly speeding up initial application loads, script executions, and module resolution.

## 2026-04-08 - Cache File I/O Operations in Streamlit Render Path
**Learning:** Streamlit re-executes the entire script top-to-bottom on every user interaction. Placing synchronous file I/O (like reading `treasury.json` or `simulation_history.json`) directly in the render path—including inside `st.expander` which evaluates its contents on every rerun—causes hidden performance bottlenecks.
**Action:** Wrap file I/O and synchronous data fetching in `@st.cache_data(ttl=60, show_spinner=False)`. Call `.clear()` on the cache immediately after state-modifying actions (swap execution, simulation save) to keep the UI synchronized.
