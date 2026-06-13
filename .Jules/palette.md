## 2026-06-13 - [Streamlit Native Accessibility Tooltips]
**Learning:** In Streamlit, native tooltips and ARIA labels for accessibility can be automatically generated for input widgets simply by providing a string to the `help` parameter. This acts as a straightforward path for accessibility improvement on elements like `st.button`, `st.text_input`, etc.
**Action:** Routinely append the `help` argument containing descriptive context whenever modifying or adding interactive elements in Streamlit, ensuring screen readers get equivalent information to visual tooltips.
