
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserResponse,
    TokenResponse,
    ChangePasswordRequest,
)

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form.username).first()

    if not user or not verify_password(
        form.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User is inactive"
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role)
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(
        payload.current_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    if verify_password(
        payload.new_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the current password"
        )

    current_user.hashed_password = hash_password(payload.new_password)
    current_user.must_change_password = False

    db.commit()
    db.refresh(current_user)

    return {"message": "Password changed successfully"}
