
import streamlit as st

from components.access import require_role
from services.order_service import list_orders
from services.api_client import api_request


st.set_page_config(
    page_title="My Orders",
    page_icon="📦",
    layout="wide"
)

require_role("customer")

st.title("📦 My Reward Orders")

try:
    orders = list_orders()

    if orders:

        st.dataframe(
            orders,
            width="stretch",
            hide_index=True
        )

        # Only placed and processing orders can be cancelled
        eligible_orders = [
            order for order in orders
            if order.get("status") in {"placed", "processing"}
        ]

        if eligible_orders:

            st.divider()
            st.subheader("Request Order Cancellation")

            order_options = {
                order["id"]: order
                for order in eligible_orders
            }

            selected_order_id = st.selectbox(
                "Select an order",
                options=list(order_options.keys()),
                format_func=lambda order_id: (
                    f"{order_options[order_id].get('order_number', order_id)} "
                    f"({order_options[order_id].get('status')})"
                )
            )

            selected_order = order_options[selected_order_id]

            reason = st.text_area(
                "Cancellation reason",
                placeholder="Please explain why you want to cancel this order.",
                max_chars=1000
            )

            confirm = st.checkbox(
                f"I confirm that I want to request cancellation of "
                f"{selected_order.get('order_number', selected_order_id)}"
            )

            
            # Temporary debugging information
            st.caption(f"Selected order: {selected_order.get('order_number')}")
            st.caption(f"Confirmation checked: {confirm}")
            st.caption(f"Reason length: {len(reason.strip())}")

            
        if st.button("Submit Cancellation Request", width="stretch"):

            st.info("Sending cancellation request to FastAPI...")

            try:
                result = api_request(
                    "POST",
                    "/cancellations/request",
                    json={
                        "order_number": selected_order["order_number"],
                        "reason": reason.strip()
                    }
                )

                st.success("Cancellation API executed successfully!")

                st.write("API Response:")
                st.json(result)

            except Exception as exc:
                st.error(f"API Request Failed: {exc}")


        else:
            st.info("No orders found.")

except Exception as exc:
    st.error(str(exc))
