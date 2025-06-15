import pytest
from fastapi import HTTPException
from fastapi.security import SecurityScopes
from jose import jwt

from security.async_auth import ALGORITHM, SECRET_KEY, get_current_user


@pytest.mark.asyncio
async def test_get_current_user_valid():
    token = jwt.encode(
        {"sub": "alice", "scopes": ["trading", "high_value"]},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    scopes = SecurityScopes(scopes=["trading"])
    user = await get_current_user(scopes, token)
    assert user.username == "alice"
    assert "trading" in user.scopes


@pytest.mark.asyncio
async def test_get_current_user_missing_scope():
    token = jwt.encode(
        {"sub": "alice", "scopes": ["trading"]},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    scopes = SecurityScopes(scopes=["admin"])
    with pytest.raises(HTTPException) as exc:
        await get_current_user(scopes, token)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(SecurityScopes(), "badtoken")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_multi_scope_success():
    token = jwt.encode(
        {"sub": "bob", "scopes": ["trading", "admin"]},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    scopes = SecurityScopes(scopes=["trading", "admin"])
    user = await get_current_user(scopes, token)
    assert user.username == "bob"
    assert set(scopes.scopes).issubset(set(user.scopes))
