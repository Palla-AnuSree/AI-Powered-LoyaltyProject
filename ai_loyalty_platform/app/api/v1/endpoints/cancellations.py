
from uuid import uuid4
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from langgraph.types import Command

from app.core.dependencies import (
    get_db,
    require_password_change_completed,
    require_roles,
)
from app.models.user import User
from app.models.customer import Customer
from app.models.order import Order
from app.models.cancellation import CancellationRequest


router = APIRouter()


class CancellationRequestSchema(BaseModel):
    order_number: str
    reason: str = Field(
        min_length=5,
        max_length=1000
    )


class CancellationReviewSchema(BaseModel):
    decision: Literal["approved", "rejected"]
    feedback: str = Field(
        default="",
        max_length=1000
    )


@router.post("/request")
async def request_cancellation(
    payload: CancellationRequestSchema,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_password_change_completed),
):

    # Only customers can request cancellation
    if user.role != "customer":
        raise HTTPException(
            status_code=403,
            detail="Only customers can request cancellation."
        )

    customer = db.execute(
        select(Customer).where(
            Customer.user_id == user.id
        )
    ).scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer account not found."
        )

    order = db.execute(
        select(Order).where(
            Order.order_number == payload.order_number,
            Order.customer_id == customer.id
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found in your account."
        )

    session_id = str(uuid4())
    thread_id = f"cancellation-{user.id}-{session_id}"

    try:
        cancellation_graph = request.app.state.cancellation_graph

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        result = await cancellation_graph.ainvoke(
            {
                "user_id": user.id,
                "role": user.role,
                "order_id": order.id,
                "order_number": order.order_number,
                "cancellation_reason": payload.reason,
                "thread_id": thread_id,
            },
            config=config,
        )

        interrupts = result.get("__interrupt__", [])

        if interrupts:
            return {
                "session_id": session_id,
                "order_number": order.order_number,
                "cancellation_request_id": result.get(
                    "cancellation_request_id"
                ),
                "status": "pending_approval",
                "message": (
                    "Your cancellation request has been submitted "
                    "and is awaiting admin approval."
                ),
                "approval_details": interrupts[0].value,
            }

        return {
            "session_id": session_id,
            "order_number": order.order_number,
            "status": "not_submitted",
            "message": result.get(
                "response",
                "Cancellation request could not be submitted."
            ),
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to submit cancellation request."
        )


# Admin/supervisor: view pending cancellation requests
@router.get("/pending")
def get_pending_cancellations(
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles("admin", "supervisor")
    ),
):

    results = db.execute(
        select(
            CancellationRequest,
            Order.order_number
        )
        .join(
            Order,
            Order.id == CancellationRequest.order_id
        )
        .where(
            CancellationRequest.status == "pending"
        )
        .order_by(
            CancellationRequest.created_at.asc()
        )
    ).all()

    return {
        "total": len(results),
        "requests": [
            {
                "request_id": cancellation.id,
                "order_number": order_number,
                "customer_id": cancellation.customer_id,
                "reason": cancellation.cancellation_reason,
                "status": cancellation.status,
                "created_at": cancellation.created_at,
                "workflow_available": bool(cancellation.thread_id),
            }
            for cancellation, order_number in results
        ]
    }


# Admin/supervisor: approve or reject a cancellation
@router.post("/{request_id}/review")
async def review_cancellation(
    request_id: int,
    payload: CancellationReviewSchema,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles("admin", "supervisor")
    ),
):

    # Find the cancellation request
    cancellation = db.execute(
        select(CancellationRequest).where(
            CancellationRequest.id == request_id
        )
    ).scalar_one_or_none()

    if not cancellation:
        raise HTTPException(
            status_code=404,
            detail="Cancellation request not found."
        )

    if cancellation.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="This cancellation request has already been reviewed."
        )

    # Legacy requests without a LangGraph thread cannot be resumed
    if not cancellation.thread_id:
        raise HTTPException(
            status_code=409,
            detail="This request has no associated workflow thread and requires manual review."
        )

    # Prevent self-approval
    if cancellation.requested_by == user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot review your own cancellation request."
        )

    try:
        cancellation_graph = request.app.state.cancellation_graph

        config = {
            "configurable": {
                "thread_id": cancellation.thread_id
            }
        }

        # Resume the exact paused LangGraph workflow
        result = await cancellation_graph.ainvoke(
            Command(
                resume={
                    "decision": payload.decision,
                    "reviewed_by": user.id,
                    "reviewer_role": user.role,
                    "feedback": payload.feedback,
                }
            ),
            config=config,
        )

        return {
            "request_id": request_id,
            "decision": payload.decision,
            "reviewed_by": user.id,
            "status": (
                "approved"
                if payload.decision == "approved"
                else "rejected"
            ),
            "message": result.get(
                "response",
                "Cancellation review completed."
            ),
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process cancellation review."
        )
