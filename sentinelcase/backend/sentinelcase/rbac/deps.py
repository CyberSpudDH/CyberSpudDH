from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelcase.db import get_db
from sentinelcase.models.core import Permission, RolePermission, UserRole
from sentinelcase.auth.deps import get_current_user


def require_permission(permission_key: str):
    def checker(user=Depends(get_current_user), db: Session = Depends(get_db)):
        perm = db.scalar(select(Permission).where(Permission.key == permission_key))
        if not perm:
            raise HTTPException(status_code=500, detail="Permission not seeded")
        role_ids = db.scalars(select(UserRole.role_id).where(UserRole.user_id == user.id)).all()
        if not role_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        has_perm = db.scalar(
            select(RolePermission).where(
                RolePermission.role_id.in_(role_ids),
                RolePermission.permission_id == perm.id,
            )
        )
        if not has_perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return checker
