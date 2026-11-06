import streamlit as st
from services.auth_service import logout

def show_logout_button():
    if st.sidebar.button("Log out"):
        logout()
        st.rerun()
