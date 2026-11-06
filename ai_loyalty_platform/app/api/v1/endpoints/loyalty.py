from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.core.database import get_db
from app.core.dependencies import require_password_change_completed
from app.models.customer import Customer
from app.models.loyalty import PointsTransaction
from app.models.user import User
from app.core.dependencies import (
    require_password_change_completed,
    require_roles,
)

router = APIRouter()


@router.get("/me/points")
def get_my_points(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("customer")),
    password_check: User = Depends(require_password_change_completed),
):
    customer = db.query(Customer).filter(
        Customer.user_id == user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    balance = db.query(
        func.coalesce(
            func.sum(
                case(
                    (
                        PointsTransaction.transaction_type == "earn",
                        PointsTransaction.points
                    ),
                    (
                        PointsTransaction.transaction_type == "adjustment",
                        PointsTransaction.points
                    ),
                    (
                        PointsTransaction.transaction_type == "redeem",
                        -PointsTransaction.points
                    ),
                    else_=0,
                )
            ),
            0
        )
    ).filter(
        PointsTransaction.customer_id == customer.id
    ).scalar()

    return {
        "customer_id": customer.id,
        "available_points": int(balance or 0)
    }