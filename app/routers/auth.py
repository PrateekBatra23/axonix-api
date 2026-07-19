from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, RefreshToken
from app.schemas import LoginRequest, TokenResponse, RefreshRequest
from app.auth_admin import (
    verify_password, create_access_token, create_refresh_token,
    verify_refresh_token, get_current_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active == True).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(db, user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    db_token = verify_refresh_token(db, payload.refresh_token)
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == db_token.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Rotation — revoke the old refresh token, issue a brand new one
    db_token.revoked = True
    db.commit()
    new_refresh_token = create_refresh_token(db, user.id)

    access_token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    db_token = verify_refresh_token(db, payload.refresh_token)
    if db_token:
        db_token.revoked = True
        db.commit()
    return {"status": "logged out"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "role": current_user.role}