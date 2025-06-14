from __future__ import annotations

import os
import secrets
from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "15"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    READ_ONLY = "read_only"


class Permission(str, Enum):
    ANALYTICS_READ = "analytics:read"
    METRICS_READ = "metrics:read"
    TRADING_EXECUTE = "trading:execute"
    ADMIN_MANAGE = "admin:manage"


ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.ANALYTICS_READ,
        Permission.METRICS_READ,
        Permission.ADMIN_MANAGE,
    ],
    UserRole.TRADER: [Permission.ANALYTICS_READ, Permission.TRADING_EXECUTE],
    UserRole.READ_ONLY: [Permission.ANALYTICS_READ],
}


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=UserRole(role))
    except JWTError as exc:  # noqa: BLE001
        raise credentials_exception from exc
    return token_data


def require_permission(permission: Permission):
    def permission_checker(current_user: TokenData = Depends(verify_token)) -> TokenData:
        user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {permission.value} required",
            )
        return current_user

    return permission_checker
