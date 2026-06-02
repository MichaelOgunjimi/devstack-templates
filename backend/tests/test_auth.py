from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_admin_user
from core.config import settings
from core.security import create_password_reset_token, create_verification_token, hash_password
from models.user import User
from services import auth as auth_svc
from services.integrations.email.client import EmailNotConfiguredError

_PASSWORD = "TestPass123!"


async def _register(client: AsyncClient, email: str, role: str | None = None) -> dict:
    payload = {
        "email": email,
        "password": _PASSWORD,
        "full_name": "Test User",
    }
    if role is not None:
        payload["role"] = role

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_register_defaults_to_user_role(client: AsyncClient) -> None:
    tokens = await _register(client, "register-default-role@test.com")

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "register-default-role@test.com"
    assert body["role"] == "user"
    assert body["is_verified"] is False


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    await _register(client, "duplicate@test.com")

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@test.com",
            "password": _PASSWORD,
            "full_name": "Second User",
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_returns_tokens_for_valid_credentials(client: AsyncClient) -> None:
    await _register(client, "login-success@test.com")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-success@test.com", "password": _PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_forgot_password_uses_generic_response(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "missing@test.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If an account exists with this email, a reset link has been sent"
    }


@pytest.mark.asyncio
async def test_reset_password_changes_login_password(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = User(
        email="reset-password@test.com",
        hashed_password=hash_password(_PASSWORD),
        full_name="Reset User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_password_reset_token(str(user.id))
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewPass123!"},
    )

    assert response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset-password@test.com", "password": "NewPass123!"},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_verify_email_marks_user_verified(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = User(
        email="verify-email@test.com",
        hashed_password=hash_password(_PASSWORD),
        full_name="Verify User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_verification_token(str(user.id))
    response = await client.post("/api/v1/auth/verify-email", json={"token": token})

    assert response.status_code == 200
    assert response.json() == {"message": "Email verified successfully"}
    await db_session.refresh(user)
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_verify_email_delivery_uses_smtp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = AsyncMock()
    monkeypatch.setattr(auth_svc, "send_email", sent)

    await auth_svc.send_verify_email(
        email="verify-delivery@test.com",
        name="Verify Delivery",
        user_id="0af7a5f0-98f6-4e83-a333-cf0d740dfabc",
    )

    sent.assert_awaited_once()
    kwargs = sent.await_args.kwargs
    assert kwargs["to"] == "verify-delivery@test.com"
    assert kwargs["subject"] == "Verify your email"
    assert "/verify-email?token=" in kwargs["html_body"]


@pytest.mark.asyncio
async def test_auth_email_falls_back_to_logs_when_smtp_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def missing_smtp(**_: object) -> None:
        raise EmailNotConfiguredError("Missing SMTP settings")

    monkeypatch.setattr(auth_svc, "send_email", missing_smtp)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    await auth_svc.send_reset_email(
        email="reset-delivery@test.com",
        name="Reset Delivery",
        user_id="0af7a5f0-98f6-4e83-a333-cf0d740dfabc",
    )


@pytest.mark.asyncio
async def test_admin_dependency_rejects_normal_user() -> None:
    user = User(email="normal@test.com", hashed_password="hash", role="user")

    with pytest.raises(Exception) as exc_info:
        await get_current_admin_user(user)

    assert getattr(exc_info.value, "status_code", None) == 403


@pytest.mark.asyncio
async def test_admin_dependency_accepts_admin_user() -> None:
    admin = User(email="admin@test.com", hashed_password="hash", role="admin")

    result = await get_current_admin_user(admin)

    assert result is admin
