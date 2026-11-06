
import streamlit as st

from components.access import require_role
from services.api_client import api_request


st.set_page_config(
    page_title="Admin Panel",
    page_icon="⚙️",
    layout="wide"
)

require_role("admin")

st.title("⚙️ Admin Panel")
st.divider()

st.subheader("📦 Order Cancellation Management")
st.caption("Review customer cancellation requests and approve or reject them.")

# Refresh requests
col1, col2 = st.columns([1, 5])

with col1:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    data = api_request("GET", "/cancellations/pending")

    cancellation_requests = data.get("requests", [])

    st.metric("Pending Requests", data.get("total", 0))

    if not cancellation_requests:
        st.success("There are no pending cancellation requests.")

    for item in cancellation_requests:

        request_id = item["request_id"]

        with st.container(border=True):

            st.markdown(
                f"### Request #{request_id} — {item['order_number']}"
            )

            st.write(f"**Customer ID:** {item['customer_id']}")
            st.write(f"**Reason:** {item['reason']}")
            st.caption(f"Requested at: {item['created_at']}")

            if not item.get("workflow_available", False):

                st.warning(
                    "This is a legacy request without a workflow thread. "
                    "Manual review is required."
                )

            else:

                feedback = st.text_area(
                    "Review feedback",
                    placeholder="Enter approval or rejection reason...",
                    key=f"feedback_{request_id}"
                )

                approve_col, reject_col = st.columns(2)

                with approve_col:

                    if st.button(
                        "✅ Approve",
                        key=f"approve_{request_id}",
                        width="stretch"
                    ):
                        try:
                            result = api_request(
                                "POST",
                                f"/cancellations/{request_id}/review",
                                json={
                                    "decision": "approved",
                                    "feedback": feedback
                                }
                            )

                            st.success(result.get("message", "Request approved."))
                            st.rerun()

                        except Exception as exc:
                            st.error(str(exc))

                with reject_col:

                    if st.button(
                        "❌ Reject",
                        key=f"reject_{request_id}",
                        width="stretch"
                    ):
                        try:
                            result = api_request(
                                "POST",
                                f"/cancellations/{request_id}/review",
                                json={
                                    "decision": "rejected",
                                    "feedback": feedback
                                }
                            )

                            st.success(result.get("message", "Request rejected."))
                            st.rerun()

                        except Exception as exc:
                            st.error(str(exc))

except Exception as exc:
    st.error(f"Unable to load cancellation requests: {exc}")
