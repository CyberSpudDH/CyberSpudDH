from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelcase.auth.deps import get_current_user
from sentinelcase.auth.security import create_access_token, verify_password
from sentinelcase.db import get_db
from sentinelcase.models.core import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login_at = datetime.utcnow()
    db.commit()
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "org_id": str(user.org_id), "email": user.email, "display_name": user.display_name}


@router.post("/logout")
def logout():
    return {"ok": True}
