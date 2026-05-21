import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.deps import CurrentActiveUserDep, RedisDep, SessionDep
from core.security import decode_token
from models.user import User
from schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from schemas.user import UserRead, UserUpdate
from services import auth as auth_svc
from services.auth import authenticate_user, create_user_tokens, revoke_refresh_token

logger = structlog.get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: SessionDep,
    redis: RedisDep,
    background_tasks: BackgroundTasks,
) -> TokenResponse:
    """Create a new user account and return tokens."""
    user = await auth_svc.register_user(body, db)
    background_tasks.add_task(
        auth_svc.send_verify_email,
        email=user.email,
        name=user.full_name or "",
        user_id=str(user.id),
    )
    return await create_user_tokens(user, db, redis)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: SessionDep,
    redis: RedisDep,
) -> TokenResponse:
    """Authenticate with email + password and return tokens."""
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("auth.login.success", user_id=str(user.id))
    return await create_user_tokens(user, db, redis)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: SessionDep,
    redis: RedisDep,
) -> TokenResponse:
    return await auth_svc.refresh_access_token(body.refresh_token, db, redis)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    db: SessionDep,
    redis: RedisDep,
) -> None:
    """Revoke the supplied refresh token."""
    try:
        payload = decode_token(body.refresh_token)
        jti: str | None = payload.get("jti")
        if jti:
            await revoke_refresh_token(jti, db, redis)
    except HTTPException:
        # Token already invalid; treat as successful logout.
        pass


@router.get("/me", response_model=UserRead)
async def get_me(
    user: CurrentActiveUserDep,
) -> User:
    return user


@router.put("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    user: CurrentActiveUserDep,
    db: SessionDep,
) -> User:
    return await auth_svc.update_user(user, body, db)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(body: VerifyEmailRequest, db: SessionDep) -> MessageResponse:
    user, newly_verified = await auth_svc.verify_user_email(body.token, db)
    if newly_verified:
        logger.info("auth.verify_email.completed", user_id=str(user.id))
        return MessageResponse(message="Email verified successfully")
    return MessageResponse(message="Email already verified")


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    user: CurrentActiveUserDep,
    background_tasks: BackgroundTasks,
) -> MessageResponse:
    if user.is_verified:
        return MessageResponse(message="Email already verified")
    background_tasks.add_task(
        auth_svc.send_verify_email,
        email=user.email,
        name=user.full_name or "",
        user_id=str(user.id),
    )
    return MessageResponse(message="Verification email sent")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: SessionDep,
    background_tasks: BackgroundTasks,
) -> MessageResponse:
    user = await auth_svc.initiate_password_reset(body.email, db)
    if user:
        background_tasks.add_task(
            auth_svc.send_reset_email,
            email=user.email,
            name=user.full_name or "",
            user_id=str(user.id),
        )
    return MessageResponse(
        message="If an account exists with this email, a reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: SessionDep,
    background_tasks: BackgroundTasks,
) -> MessageResponse:
    user = await auth_svc.reset_user_password(body, db)
    background_tasks.add_task(
        auth_svc.send_password_changed_email,
        email=user.email,
        name=user.full_name or "",
        user_id=str(user.id),
    )
    return MessageResponse(message="Password has been reset successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    user: CurrentActiveUserDep,
    db: SessionDep,
    background_tasks: BackgroundTasks,
) -> MessageResponse:
    await auth_svc.change_user_password(user, body, db)
    background_tasks.add_task(
        auth_svc.send_password_changed_email,
        email=user.email,
        name=user.full_name or "",
        user_id=str(user.id),
    )
    return MessageResponse(message="Password changed successfully")
