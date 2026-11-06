
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.outlet import Outlet
from app.schemas.outlet import OutletCreate, OutletResponse

router = APIRouter()


@router.post(
    "/admin/create-outlet",
    response_model=OutletResponse
)
def create_outlet(
    payload: OutletCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("admin")),
):
    # Check whether outlet code already exists
    existing_outlet = db.query(Outlet).filter(
        Outlet.outlet_code == payload.outlet_code
    ).first()

    if existing_outlet:
        raise HTTPException(
            status_code=409,
            detail="Outlet code already exists"
        )

    outlet = Outlet(
        outlet_code=payload.outlet_code,
        outlet_name=payload.outlet_name,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        is_active=True,
    )

    try:
        db.add(outlet)
        db.commit()
        db.refresh(outlet)
        return outlet

    except Exception:
        db.rollback()
        raise
