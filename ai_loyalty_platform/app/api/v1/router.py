
from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    auth,
    customers,
    loyalty,
    orders,
    chatbot,
    outlets,
    cancellations,
)
from app.core.dependencies import require_password_change_completed

api_router = APIRouter()

# Authentication routes: login and change password remain accessible
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Other features require the user to change their temporary password first
password_check = [Depends(require_password_change_completed)]

api_router.include_router(
    customers.router,
    prefix="/customers",
    tags=["customers"],
    dependencies=password_check
)

api_router.include_router(
    loyalty.router,
    prefix="/loyalty",
    tags=["loyalty"],
    dependencies=password_check
)

api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["orders"],
    dependencies=password_check
)

api_router.include_router(
    chatbot.router,
    prefix="/chatbot",
    tags=["AI chatbot"],
    dependencies=password_check
)

api_router.include_router(
    outlets.router,
    prefix="/outlets",
    tags=["outlets"],
    dependencies=password_check
)
api_router.include_router(
    cancellations.router,
    prefix="/cancellations",
    tags=["Order cancellations"],
    dependencies=password_check
)
