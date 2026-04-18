## 2024-05-24 - Mathematical Clarifications in Multi-Asset Splits
**Learning:** Users can easily become confused when distributing a single budget across multiple selections (e.g., a multi-asset portfolio split). When an input simply says "Total Amount", it may not be immediately clear whether that amount will be applied *per asset* or *divided among* the assets.
**Action:** Always use the `help` parameter to provide explicit mathematical clarifications (e.g., "This total is split equally (e.g., $100 split across 2 assets = $50 each)") when building Streamlit interfaces that distribute values across multiple selections.

## 2026-04-16 - Actionable Empty States
**Learning:** A static empty state text message (like "No simulations run yet") leaves the user at a dead end. Empty states should always provide an actionable call-to-action guiding users on exactly how to populate the area or perform a related task.
**Action:** Replace static `st.info` descriptive empty states with actionable ones that include an immediate `st.button` CTA (e.g., "Load Example Strategy" or "Run Simulation") to improve flow and engagement.
