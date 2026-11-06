import streamlit as st
from components.access import require_role
from services.loyalty_service import get_my_points
from services.order_service import list_orders

st.set_page_config(page_title="Customer Dashboard", page_icon="🎁", layout="wide")
user = require_role("customer")
st.title("🎁 Customer Dashboard")
st.write(f"Welcome, {user.get('full_name', 'Customer')}.")
try:
    points = get_my_points()
    orders = list_orders()
    a, b = st.columns(2)
    a.metric("Available points", points.get("available_points", 0))
    b.metric("Reward orders", len(orders))
    st.subheader("Recent orders")
    st.dataframe(orders, use_container_width=True, hide_index=True)
except Exception as exc:
    st.warning(f"Could not load dashboard: {exc}")
