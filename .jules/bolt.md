## 2025-03-05 - Lazy Loading Heavy Packages to Optimize Startup
**Learning:** `matplotlib` is a very heavy package to import. Importing it globally in a frequently imported file like `simulator.py` blocks the main thread and can delay application startup (e.g. `main.py --help`) by over 2.5 seconds on slower environments.
**Action:** Move `import matplotlib.pyplot as plt` locally inside functions that actually require charting (e.g., `render_chart`), thus enabling lazy-loading and instantly speeding up initial application loads, script executions, and module resolution.
