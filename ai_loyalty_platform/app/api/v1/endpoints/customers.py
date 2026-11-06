
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    get_current_user,
    require_roles,
    require_password_change_completed,
)
from typing import List
from app.core.security import hash_password
from app.models.customer import Customer
from app.models.user import User
from app.models.loyalty import LoyaltyAccount
from app.schemas.customer import AdminUserCreate, CustomerResponse
from app.models.outlet import Outlet

router = APIRouter()

ALLOWED_ROLES = {
    "admin",
    "customer",
    "outlet_user",
    "supervisor",
    "support",
}


@router.post("/admin/create-user")
def admin_create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    # 1. Validate role
    role = payload.role.lower().strip()

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    # 2. Check duplicate email
    existing_user = db.query(User).filter(
        User.email == payload.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # 3. Validate outlet assignment
    if role in {"customer", "outlet_user", "supervisor"}:
        if payload.outlet_id is None:
            raise HTTPException(
                status_code=400,
                detail="Outlet ID is required for customer, outlet_user and supervisor roles"
            )

        outlet = db.query(Outlet).filter(
            Outlet.id == payload.outlet_id,
            Outlet.is_active.is_(True)
        ).first()

        if not outlet:
            raise HTTPException(
                status_code=404,
                detail="Outlet not found or inactive"
            )

    elif payload.outlet_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Outlet ID is not required for this role"
        )

    # 4. Customer-specific validation
    if role == "customer":
        if not payload.customer_code:
            raise HTTPException(
                status_code=400,
                detail="Customer code is required for customer role"
            )

        if db.query(Customer).filter(
            Customer.customer_code == payload.customer_code
        ).first():
            raise HTTPException(
                status_code=409,
                detail="Customer code already exists"
            )
    else:
        if payload.customer_code or payload.phone:
            raise HTTPException(
                status_code=400,
                detail="Customer code and phone are only allowed for customer role"
            )

    try:
        # 5. Create User account
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.temporary_password),
            role=role,
            is_active=True,
            must_change_password=True,
            outlet_id=(
                payload.outlet_id
                if role in {"outlet_user", "supervisor"}
                else None
            ),
        )

        db.add(user)
        db.flush()

        # 6. Create Customer profile and Loyalty account
        if role == "customer":
            customer = Customer(
                user_id=user.id,
                customer_code=payload.customer_code,
                phone=payload.phone,
                outlet_id=payload.outlet_id,
            )

            db.add(customer)
            db.flush()

            loyalty_account = LoyaltyAccount(
                customer_id=customer.id,
                account_number=f"LOY-{uuid4().hex[:12].upper()}",
                points_balance=0,
                tier="Silver",
                status="active",
            )

            db.add(loyalty_account)

        db.commit()
        db.refresh(user)

        return {
            "message": f"{role.capitalize()} account created successfully",
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "outlet_id": payload.outlet_id,
            "must_change_password": user.must_change_password,
        }

    except Exception:
        db.rollback()
        raise


@router.get("/me", response_model=CustomerResponse)
def get_my_customer(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(
        Customer.user_id == user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )

    return customer
@router.get("/outlet/customers", response_model=List[CustomerResponse])
def get_outlet_customers(
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles("outlet_user", "supervisor")
    ),
    password_check: User = Depends(
        require_password_change_completed
    ),
):
    if user.outlet_id is None:
        raise HTTPException(
            status_code=400,
            detail="No outlet assigned to this user"
        )

    customers = db.query(Customer).filter(
        Customer.outlet_id == user.outlet_id
    ).all()

    return customers
