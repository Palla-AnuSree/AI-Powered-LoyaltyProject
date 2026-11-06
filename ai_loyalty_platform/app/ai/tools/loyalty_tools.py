
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy import select
from app.models.order import Order

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.loyalty import LoyaltyAccount, PointsTransaction



@tool
def get_customer_points_balance(
    user_id: Annotated[int, InjectedState("user_id")],
    role: Annotated[str, InjectedState("role")],
) -> dict:
    """
    Retrieve the current loyalty points balance, tier and account
    status of the authenticated customer.

    Use this tool when a customer asks about their points balance,
    loyalty tier or account status.
    """

    # Only customers can access this tool
    if role != "customer":
        return {
            "success": False,
            "message": "You are not authorized to access customer loyalty details."
        }

    db = SessionLocal()

    try:
        customer = db.execute(
            select(Customer).where(
                Customer.user_id == user_id
            )
        ).scalar_one_or_none()

        if not customer:
            return {
                "success": False,
                "message": "Customer account not found."
            }

        account = db.execute(
            select(LoyaltyAccount).where(
                LoyaltyAccount.customer_id == customer.id
            )
        ).scalar_one_or_none()

        if not account:
            return {
                "success": False,
                "message": "Loyalty account not found."
            }

        return {
            "success": True,
            "points_balance": account.points_balance,
            "tier": account.tier,
            "status": account.status
        }

    finally:
        db.close()

    
@tool
def get_customer_transaction_history(
    limit: int,
    user_id: Annotated[int, InjectedState("user_id")],
    role: Annotated[str, InjectedState("role")],
) -> dict:
    """
    Retrieve the recent points transaction history of the
    authenticated customer.

    Use this tool when a customer asks about:
    - Recent points earned
    - Recent points redeemed
    - Points deductions or adjustments
    - Previous points transactions

    The limit specifies how many recent transactions to retrieve.
    """

    if role != "customer":
        return {
            "success": False,
            "message": "You are not authorized to access customer transaction history."
        }

    if limit < 1 or limit > 10:
        limit = 5

    db = SessionLocal()

    try:
        customer = db.execute(
            select(Customer).where(
                Customer.user_id == user_id
            )
        ).scalar_one_or_none()

        if not customer:
            return {
                "success": False,
                "message": "Customer account not found."
            }

        transactions = db.execute(
            select(PointsTransaction)
            .where(
                PointsTransaction.customer_id == customer.id
            )
            .order_by(PointsTransaction.id.desc())
            .limit(limit)
        ).scalars().all()

        if not transactions:
            return {
                "success": True,
                "count": 0,
                "transactions": [],
                "message": "No points transactions found."
            }

        return {
            "success": True,
            "count": len(transactions),
            "transactions": [
                {
                    "transaction_id": transaction.id,
                    "points": transaction.points,
                    "transaction_type": transaction.transaction_type,
                    "description": transaction.description,
                }
                for transaction in transactions
            ]
        }

    finally:
        db.close()

    
@tool
def get_customer_redemption_history(
    limit: int,
    user_id: Annotated[int, InjectedState("user_id")],
    role: Annotated[str, InjectedState("role")],
) -> dict:
    """
    Retrieve the recent reward redemption history of the
    authenticated customer.

    Use this tool when a customer asks about:
    - Redeemed rewards
    - Previous reward orders
    - Redemption status
    - Points spent on rewards
    """
    if role != "customer":
        return {
            "success": False,
            "message": "You are not authorized to access reward redemption history."
        }

    if limit < 1 or limit > 10:
        limit = 5

    db = SessionLocal()

    try:
        customer = db.execute(
            select(Customer).where(Customer.user_id == user_id)
        ).scalar_one_or_none()

        if not customer:
            return {
                "success": False,
                "message": "Customer account not found."
            }

        orders = db.execute(
            select(Order)
            .where(Order.customer_id == customer.id)
            .order_by(Order.id.desc())
            .limit(limit)
        ).scalars().all()

        if not orders:
            return {
                "success": True,
                "count": 0,
                "redemptions": [],
                "message": "No reward redemption records found."
            }

        return {
            "success": True,
            "count": len(orders),
            "redemptions": [
                {
                    "order_number": order.order_number,
                    "reward_name": order.reward_name,
                    "points_used": order.points_used,
                    "status": order.status,
                }
                for order in orders
            ]
        }

    finally:
        db.close()


@tool
def get_customer_order_status(
    order_number: str,
    user_id: Annotated[int, InjectedState("user_id")],
    role: Annotated[str, InjectedState("role")],
) -> dict:
    """
    Retrieve the status and details of a reward order
    belonging to the authenticated customer.

    Use this tool when a customer asks:
    - Where is my reward order?
    - What is my order status?
    - Has my voucher been delivered?
    - When was my order last updated?

    The customer can only access their own orders.
    """

    if role != "customer":
        return {
            "success": False,
            "message": "You are not authorized to access order details."
        }

    db = SessionLocal()

    try:
        customer = db.execute(
            select(Customer).where(
                Customer.user_id == user_id
            )
        ).scalar_one_or_none()

        if not customer:
            return {
                "success": False,
                "message": "Customer account not found."
            }

        order = db.execute(
            select(Order).where(
                Order.order_number == order_number,
                Order.customer_id == customer.id
            )
        ).scalar_one_or_none()

        if not order:
            return {
                "success": False,
                "message": "Order not found in your account."
            }

        return {
            "success": True,
            "order_number": order.order_number,
            "reward_name": order.reward_name,
            "points_used": order.points_used,
            "status": order.status,
            "created_at": (
                order.created_at.isoformat()
                if order.created_at else None
            ),
            "updated_at": (
                order.updated_at.isoformat()
                if order.updated_at else None
            ),
        }

    finally:
        db.close()


@tool
def check_order_cancellation_eligibility(
    order_number: str,
    user_id: Annotated[int, InjectedState("user_id")],
    role: Annotated[str, InjectedState("role")],
) -> dict:
    """
    Check whether the authenticated customer can request
    cancellation of their reward order.

    Only orders with placed or processing status are eligible.
    This tool does not cancel the order.
    """

    if role != "customer":
        return {
            "success": False,
            "eligible": False,
            "message": "Only customers can request order cancellation."
        }

    db = SessionLocal()

    try:
        customer = db.execute(
            select(Customer).where(
                Customer.user_id == user_id
            )
        ).scalar_one_or_none()

        if not customer:
            return {
                "success": False,
                "eligible": False,
                "message": "Customer account not found."
            }

        order = db.execute(
            select(Order).where(
                Order.order_number == order_number,
                Order.customer_id == customer.id
            )
        ).scalar_one_or_none()

        if not order:
            return {
                "success": False,
                "eligible": False,
                "message": "Order not found in your account."
            }

        if order.status.lower() not in ["placed", "processing"]:
            return {
                "success": True,
                "eligible": False,
                "order_number": order.order_number,
                "status": order.status,
                "message": (
                    "This order cannot be cancelled because "
                    f"its current status is {order.status}."
                )
            }

        return {
            "success": True,
            "eligible": True,
            "order_id": order.id,
            "order_number": order.order_number,
            "reward_name": order.reward_name,
            "points_used": order.points_used,
            "status": order.status,
            "message": (
                "This order is eligible for cancellation. "
                "Human approval is required before cancellation."
            )
        }

    finally:
        db.close()
