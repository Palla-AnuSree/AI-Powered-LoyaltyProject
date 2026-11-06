import streamlit as st
from components.access import require_role
from services.loyalty_service import get_my_points

st.set_page_config(page_title="Loyalty Points", page_icon="⭐", layout="wide")
require_role("customer")
st.title("⭐ My Loyalty Points")
try:
    data = get_my_points()
    st.metric("Available points", data.get("available_points", 0))
    st.info("Points history, expiry and tier benefits will be added in a later phase.")
except Exception as exc:
    st.error(str(exc))
