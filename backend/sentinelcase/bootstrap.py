from sqlalchemy import select

from sentinelcase.auth.security import hash_password
from sentinelcase.db import SessionLocal
from sentinelcase.models.core import Org, Permission, Role, RolePermission, User, UserRole
from sentinelcase.rbac.constants import DEFAULT_ROLES, PERMISSIONS


def run_bootstrap(org_name: str = "Acme", admin_email: str = "admin@acme.com", admin_password: str = "changeme"):
    db = SessionLocal()
    try:
        org = db.scalar(select(Org).where(Org.name == org_name))
        if not org:
            org = Org(name=org_name)
            db.add(org)
            db.flush()

        perm_map = {}
        for p in PERMISSIONS:
            perm = db.scalar(select(Permission).where(Permission.key == p))
            if not perm:
                perm = Permission(key=p)
                db.add(perm)
                db.flush()
            perm_map[p] = perm

        role_map = {}
        for role_name, keys in DEFAULT_ROLES.items():
            role = db.scalar(select(Role).where(Role.org_id == org.id, Role.name == role_name))
            if not role:
                role = Role(org_id=org.id, name=role_name, description=f"{role_name} role", is_builtin=True)
                db.add(role)
                db.flush()
            role_map[role_name] = role
            for key in keys:
                exists = db.scalar(select(RolePermission).where(RolePermission.role_id == role.id, RolePermission.permission_id == perm_map[key].id))
                if not exists:
                    db.add(RolePermission(role_id=role.id, permission_id=perm_map[key].id))

        user = db.scalar(select(User).where(User.org_id == org.id, User.email == admin_email))
        if not user:
            user = User(org_id=org.id, email=admin_email, display_name="Administrator", password_hash=hash_password(admin_password))
            db.add(user)
            db.flush()
            db.add(UserRole(user_id=user.id, role_id=role_map["Admin"].id))

        db.commit()
        print(f"Bootstrapped org={org.name} admin={admin_email}")
    finally:
        db.close()


if __name__ == "__main__":
    run_bootstrap()
