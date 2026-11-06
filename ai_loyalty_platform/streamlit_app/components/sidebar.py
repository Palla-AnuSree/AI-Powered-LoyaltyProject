import streamlit as st

def show_user_context():
    user = st.session_state.get("user", {})
    st.sidebar.caption("Signed-in account")
    st.sidebar.write(user.get("full_name", "User"))
    st.sidebar.caption(user.get("role", "").replace("_", " ").title())
