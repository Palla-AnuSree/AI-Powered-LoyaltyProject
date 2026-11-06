
from typing import TypedDict
from langgraph.graph import MessagesState


class LoyaltyAgentState(MessagesState, total=False):
    user_id: int
    role: str
    message: str
    intent: str
    retrieved_context: list[dict]
    tool_results: list[dict]
    requires_confirmation: bool
    confirmed: bool
    response: str
    errors: list[str]
    outlet_id: int | None

    # Order cancellation
    order_id: int
    order_number: str
    cancellation_reason: str
    cancellation_request_id: int

    # Human approval
    approval_status: str
    approval_by: int
    approval_feedback: str
    approval_role: str
