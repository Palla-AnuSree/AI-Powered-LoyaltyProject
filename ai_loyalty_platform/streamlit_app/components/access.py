import streamlit as st

def require_login():
    if not st.session_state.get("access_token") or "user" not in st.session_state:
        st.warning("Please sign in from the Home page first.")
        st.stop()
    return st.session_state["user"]

def require_role(*allowed_roles):
    user = require_login()
    if user.get("role") not in allowed_roles:
        st.error("You do not have access to this page.")
        st.stop()
    return user
