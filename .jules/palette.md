## 2024-05-24 - Mathematical Clarifications in Multi-Asset Splits
**Learning:** Users can easily become confused when distributing a single budget across multiple selections (e.g., a multi-asset portfolio split). When an input simply says "Total Amount", it may not be immediately clear whether that amount will be applied *per asset* or *divided among* the assets.
**Action:** Always use the `help` parameter to provide explicit mathematical clarifications (e.g., "This total is split equally (e.g., $100 split across 2 assets = $50 each)") when building Streamlit interfaces that distribute values across multiple selections.
## 2024-04-17 - Empty State Call-To-Action
**Learning:** Users can feel stuck when presented with a purely descriptive empty state (e.g., "No simulations run yet"). Providing an actionable CTA button that directly triggers the core workflow resolves this friction.
**Action:** When designing empty states for data views, use Streamlit's `st.session_state` with `st.rerun()` to bridge the CTA button to the primary execution logic, avoiding duplicated code while immediately engaging the user.
