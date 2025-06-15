from __future__ import annotations

"""Asynchronous OAuth2 bearer authentication utilities."""

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "trading": "Trading operations",
        "high_value": "High value operations",
        "admin": "Administrative operations",
    },
)


class TokenData(BaseModel):
    """Data stored in the JWT token."""

    username: Optional[str] = None
    scopes: list[str] = []


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    """Validate JWT ``token`` and ensure required scopes are present."""

    if security_scopes.scopes:
        auth_header = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        auth_header = "Bearer"
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": auth_header},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        if username is None:
            raise credentials_error
        if isinstance(token_scopes, str):
            token_scopes = token_scopes.split()
    except JWTError as exc:  # noqa: BLE001
        raise credentials_error from exc
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": auth_header},
            )
    return TokenData(username=username, scopes=token_scopes)


__all__ = ["get_current_user", "TokenData"]
