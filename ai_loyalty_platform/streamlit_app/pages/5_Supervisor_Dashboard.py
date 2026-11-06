import streamlit as st
from components.access import require_role

st.set_page_config(page_title="Supervisor Dashboard", page_icon="📊", layout="wide")
require_role("supervisor", "admin")
st.title("📊 Supervisor Dashboard")
st.info("Outlet-wise sales, target vs achievement and brand reports will be connected here.")
