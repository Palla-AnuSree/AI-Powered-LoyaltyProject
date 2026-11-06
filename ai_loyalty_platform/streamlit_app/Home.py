import streamlit as st
from config import APP_TITLE
from services.auth_service import login, get_current_user, logout

st.set_page_config(page_title=APP_TITLE, page_icon="🎁", layout="wide")

def login_view():
    st.title("🎁 AI Loyalty Platform")
    st.caption("Sign in to manage loyalty points, rewards and orders.")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        try:
            result = login(email.strip(), password)
            st.session_state["access_token"] = result["access_token"]
            st.session_state["user"] = get_current_user()
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

if not st.session_state.get("access_token"):
    login_view()
else:
    user = st.session_state.get("user", {})
    left, right = st.columns([4, 1])
    with left:
        st.title(f"Welcome, {user.get('full_name', 'User')} 👋")
        st.caption(f"Role: {user.get('role', 'unknown').replace('_', ' ').title()}")
    with right:
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()
    st.divider()
    st.subheader("Your loyalty workspace")
    st.write("Use the navigation menu to open the pages available to your role.")
