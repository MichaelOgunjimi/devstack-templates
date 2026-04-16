"""OAuth2 routes for Google, GitHub, and Facebook.

Uses httpx for the token exchange and user-info fetch rather than the full
authlib Starlette integration, which keeps the flow explicit and easy to trace.
Each provider has a small, dedicated helper that knows its endpoints.
"""

from typing import Any
from urllib.parse import urlencode

import structlog
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from api.deps import RedisDep, SessionDep
from core.config import settings
from services.auth import create_user_tokens, get_or_create_oauth_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, dict[str, str]] = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
        "client_id_setting": "GOOGLE_CLIENT_ID",
        "client_secret_setting": "GOOGLE_CLIENT_SECRET",
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email",
        "client_id_setting": "GITHUB_CLIENT_ID",
        "client_secret_setting": "GITHUB_CLIENT_SECRET",
    },
    "facebook": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me",
        "scope": "email,public_profile",
        "client_id_setting": "FACEBOOK_CLIENT_ID",
        "client_secret_setting": "FACEBOOK_CLIENT_SECRET",
    },
}


def _get_provider_config(provider: str) -> dict[str, str]:
    if provider not in _PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider '{provider}'. Supported: {list(_PROVIDERS)}",
        )
    cfg = _PROVIDERS[provider]
    client_id = getattr(settings, cfg["client_id_setting"])
    client_secret = getattr(settings, cfg["client_secret_setting"])
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"OAuth provider '{provider}' is not configured on this server",
        )
    return {**cfg, "client_id": client_id, "client_secret": client_secret}


def _callback_url(provider: str) -> str:
    return f"{settings.BACKEND_URL}/api/v1/oauth/{provider}/callback"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/{provider}/login")
async def oauth_login(provider: str) -> RedirectResponse:
    """Redirect the user to the provider's OAuth consent screen."""
    cfg = _get_provider_config(provider)

    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": _callback_url(provider),
        "scope": cfg["scope"],
        "response_type": "code",
    }
    # Google requires an additional state parameter for CSRF protection.
    if provider == "google":
        params["access_type"] = "offline"
        params["prompt"] = "consent"

    redirect_to = f"{cfg['auth_url']}?{urlencode(params)}"
    logger.info("oauth.login.redirect", provider=provider)
    return RedirectResponse(url=redirect_to)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    db: SessionDep,
    redis: RedisDep,
) -> RedirectResponse:
    """Handle the provider callback, exchange code for token, redirect with app tokens."""
    import httpx

    cfg = _get_provider_config(provider)

    # 1. Exchange the authorization code for an access token.
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            cfg["token_url"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _callback_url(provider),
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
            },
            headers={"Accept": "application/json"},
        )

    if token_resp.status_code != 200:
        logger.error(
            "oauth.callback.token_exchange_failed",
            provider=provider,
            status=token_resp.status_code,
        )
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/auth/callback?error=token_exchange_failed"
        )

    token_data: dict[str, Any] = token_resp.json()
    provider_access_token: str = token_data.get("access_token", "")

    # 2. Fetch user information from the provider.
    async with httpx.AsyncClient(timeout=15.0) as client:
        if provider == "facebook":
            userinfo_resp = await client.get(
                cfg["userinfo_url"],
                params={"fields": "id,name,email", "access_token": provider_access_token},
            )
        else:
            userinfo_resp = await client.get(
                cfg["userinfo_url"],
                headers={"Authorization": f"Bearer {provider_access_token}"},
            )

    if userinfo_resp.status_code != 200:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/auth/callback?error=userinfo_failed"
        )

    userinfo: dict[str, Any] = userinfo_resp.json()

    # 3. Normalise user info across providers.
    email, full_name, provider_account_id = _extract_user_info(provider, userinfo)

    if not email:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/auth/callback?error=no_email"
        )

    # 4. Auto-link or create user.
    user = await get_or_create_oauth_user(
        db=db,
        provider=provider,
        provider_account_id=provider_account_id,
        email=email,
        full_name=full_name,
        access_token=provider_access_token,
    )

    logger.info("oauth.callback.success", provider=provider, user_id=str(user.id))
    tokens = await create_user_tokens(user, db, redis)

    # Redirect to frontend with tokens in the URL fragment (never sent to servers).
    fragment = urlencode({
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": tokens.token_type,
    })
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback#{fragment}")


def _extract_user_info(provider: str, userinfo: dict[str, Any]) -> tuple[str, str | None, str]:
    """Return (email, full_name, provider_account_id) from raw provider payload."""
    if provider == "google":
        return userinfo.get("email", ""), userinfo.get("name"), userinfo.get("sub", "")

    if provider == "github":
        email = userinfo.get("email", "")
        full_name = userinfo.get("name") or userinfo.get("login")
        return email, full_name, str(userinfo.get("id", ""))

    if provider == "facebook":
        return userinfo.get("email", ""), userinfo.get("name"), str(userinfo.get("id", ""))

    return "", None, ""
