from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_password_change_completed
from app.models.customer import Customer
from app.models.order import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, CancelOrderRequest

router = APIRouter()
CANCELLABLE_STATUSES = {"placed", "processing"}


def get_customer_or_404(db: Session, user: User) -> Customer:
    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    return customer


@router.post("", response_model=OrderResponse)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_password_change_completed),
):
    customer = get_customer_or_404(db, user)
    if db.query(Order).filter(Order.order_number == payload.order_number).first():
        raise HTTPException(status_code=409, detail="Order number already exists")
    order = Order(customer_id=customer.id, **payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderResponse])
def list_my_orders(db: Session = Depends(get_db), user: User = Depends(require_password_change_completed)):
    customer = get_customer_or_404(db, user)
    return db.query(Order).filter(Order.customer_id == customer.id).order_by(Order.id.desc()).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_my_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_password_change_completed)):
    customer = get_customer_or_404(db, user)
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == customer.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_my_order(
    order_id: int,
    payload: CancelOrderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_password_change_completed),
):
    customer = get_customer_or_404(db, user)
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == customer.id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required")
    if order.status not in CANCELLABLE_STATUSES:
        raise HTTPException(status_code=409, detail=f"Order cannot be cancelled from status: {order.status}")
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order
