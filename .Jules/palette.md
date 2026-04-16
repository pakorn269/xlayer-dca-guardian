# Palette's Journal

## 2026-04-07 - Streamlit Help Tooltips
**Learning:** In Streamlit apps, it can be difficult to implement exact ARIA labels compared to raw React/HTML. However, leveraging Streamlit's built-in `help="text"` attribute on form inputs (like `st.selectbox`, `st.number_input`, `st.text_area`) provides a native, accessible tooltip that improves the user experience without requiring custom HTML injection.
**Action:** When working on Streamlit UIs in the future, always include `help=` parameters for configuration inputs, especially when dealing with domain-specific terms (like "Token In", "Interval", "Duration") to clarify expectations for the user.

## 2026-04-07 - Actionable Empty States
**Learning:** Empty states with mere descriptive text (e.g., "No data found") can lead to user friction or confusion about next steps.
**Action:** Always provide an actionable call-to-action in empty states, guiding users on exactly how to populate the area or perform a related task.
