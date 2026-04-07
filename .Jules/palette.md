# Palette's Journal

## 2026-04-07 - Streamlit Help Tooltips
**Learning:** In Streamlit apps, it can be difficult to implement exact ARIA labels compared to raw React/HTML. However, leveraging Streamlit's built-in `help="text"` attribute on form inputs (like `st.selectbox`, `st.number_input`, `st.text_area`) provides a native, accessible tooltip that improves the user experience without requiring custom HTML injection.
**Action:** When working on Streamlit UIs in the future, always include `help=` parameters for configuration inputs, especially when dealing with domain-specific terms (like "Token In", "Interval", "Duration") to clarify expectations for the user.
