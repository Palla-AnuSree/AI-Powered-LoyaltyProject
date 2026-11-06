
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from sqlalchemy import select

from app.ai.graph.state import LoyaltyAgentState
from app.core.database import SessionLocal
from app.models.order import Order
from app.models.customer import Customer
from app.models.cancellation import CancellationRequest
from langchain_core.runnables import RunnableConfig


def create_cancellation_request(
    state: LoyaltyAgentState,
    config: RunnableConfig
):
    # Get thread ID from LangGraph execution configuration
    thread_id = config["configurable"]["thread_id"]

    if not thread_id:
        raise ValueError("LangGraph thread_id is missing.")

    if state.get("role") != "customer":
        return {
            "response": "Only customers can request order cancellation."
        }

    db = SessionLocal()

    try:
        # Find the customer's account
        customer = db.execute(
            select(Customer).where(
                Customer.user_id == state["user_id"]
            )
        ).scalar_one_or_none()

        if not customer:
            return {
                "response": "Customer account not found."
            }

        # Verify order ownership
        order = db.execute(
            select(Order).where(
                Order.id == state["order_id"],
                Order.customer_id == customer.id
            )
        ).scalar_one_or_none()

        if not order:
            return {
                "response": "Order not found in your account."
            }

        # Check cancellation eligibility
        if order.status.lower() not in ["placed", "processing"]:
            return {
                "response": (
                    f"Order {order.order_number} cannot be cancelled "
                    f"because its current status is {order.status}."
                )
            }

        # Check for an existing pending request
        existing_request = db.execute(
            select(CancellationRequest).where(
                CancellationRequest.order_id == order.id,
                CancellationRequest.status == "pending"
            )
        ).scalar_one_or_none()

        if existing_request is not None:
            return {
                "response": (
                    "A cancellation request is already pending "
                    "for this order."
                )
            }

        # Create a new cancellation request
        cancellation_request = CancellationRequest(
            order_id=order.id,
            customer_id=customer.id,
            requested_by=state["user_id"],
            cancellation_reason=state.get(
                "cancellation_reason",
                "Customer requested cancellation."
            ),
            status="pending",
            thread_id=thread_id,
        )

        db.add(cancellation_request)
        db.commit()
        db.refresh(cancellation_request)

        return {
            "cancellation_request_id": cancellation_request.id,
            "order_id": order.id,
            "order_number": order.order_number,
            "response": (
                "Your cancellation request has been submitted "
                "and is awaiting admin approval."
            )
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
def human_approval_node(state: LoyaltyAgentState):

    decision = interrupt({
        "message": "Cancellation request requires human approval.",
        "cancellation_request_id": state["cancellation_request_id"],
        "order_id": state["order_id"],
        "order_number": state["order_number"],
        "reason": state.get("cancellation_reason"),
        "requested_by": state["user_id"],
    })

    return {
        "approval_status": decision.get("decision"),
        "approval_by": decision.get("reviewed_by"),
        "approval_feedback": decision.get("feedback", ""),
        "approval_role": decision.get("reviewer_role"),
    }

def process_cancellation_node(state: LoyaltyAgentState):

    db = SessionLocal()

    try:
        decision = state.get("approval_status")
        request_id = state["cancellation_request_id"]
        reviewer_id = state.get("approval_by")

        # Validate the approval decision
        if decision not in ["approved", "rejected"]:
            raise ValueError(
                "Invalid cancellation approval decision."
            )

        if not reviewer_id:
            raise ValueError(
                "Reviewer information is missing."
            )

        # Only admin and supervisor can approve or reject
        if state.get("approval_role") not in ["admin", "supervisor"]:
            raise ValueError(
                "Only admin or supervisor can review cancellation requests."
            )

        # Lock the cancellation request while processing
        cancellation_request = db.execute(
            select(CancellationRequest)
            .where(CancellationRequest.id == request_id)
            .with_for_update()
        ).scalar_one_or_none()

        if not cancellation_request:
            raise ValueError(
                "Cancellation request not found."
            )

        # Prevent processing an already reviewed request
        if cancellation_request.status != "pending":
            raise ValueError(
                "This cancellation request has already been reviewed."
            )

        # Prevent customers from approving their own requests
        if cancellation_request.requested_by == reviewer_id:
            raise ValueError(
                "Customers cannot approve their own cancellation requests."
            )

        # Verify and lock the associated order
        order = db.execute(
            select(Order)
            .where(
                Order.id == cancellation_request.order_id
            )
            .with_for_update()
        ).scalar_one_or_none()

        if not order:
            raise ValueError(
                "Associated order not found."
            )

        # Save reviewer information
        cancellation_request.reviewed_by = reviewer_id
        cancellation_request.reviewed_at = datetime.now(timezone.utc)

        if decision == "approved":

            # Verify that the order is still eligible
            if order.status.lower() not in [
                "placed",
                "processing"
            ]:
                raise ValueError(
                    f"Order cannot be cancelled because "
                    f"its current status is {order.status}."
                )

            # Cancel the order
            order.status = "cancelled"

            cancellation_request.status = "approved"

            response = (
                f"Cancellation approved. Order "
                f"{order.order_number} has been cancelled successfully."
            )

        else:

            # Reject the cancellation request
            cancellation_request.status = "rejected"

            response = (
                f"Cancellation request for order "
                f"{order.order_number} was rejected. "
                "Your order remains unchanged."
            )

        # Save all changes together
        db.commit()

        return {
            "approval_status": decision,
            "approval_by": reviewer_id,
            "response": response,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def route_after_request(state: LoyaltyAgentState):
    """
    Continue to human approval only when a cancellation
    request was successfully created or an existing
    pending request was found.
    """

    if state.get("cancellation_request_id"):
        return "human_approval"

    return END


def build_cancellation_graph(checkpointer):

    builder = StateGraph(LoyaltyAgentState)

    # Register workflow nodes
    builder.add_node(
        "create_request",
        create_cancellation_request
    )

    builder.add_node(
        "human_approval",
        human_approval_node
    )

    builder.add_node(
        "process_cancellation",
        process_cancellation_node
    )

    # Define workflow connections
    builder.add_edge(START, "create_request")

    builder.add_conditional_edges(
        "create_request",
        route_after_request,
        {
            "human_approval": "human_approval",
            END: END,
        }
    )

    builder.add_edge(
        "human_approval",
        "process_cancellation"
    )

    builder.add_edge(
        "process_cancellation",
        END
    )

    return builder.compile(checkpointer=checkpointer)
