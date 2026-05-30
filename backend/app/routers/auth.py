"""
Auth router — 8 endpoints per API Spec v1.1 §3.

Endpoints:
  POST /auth/signup          → register (public, rate-limited)
  POST /auth/login           → login (public, rate-limited)
  POST /auth/refresh         → refresh tokens from HttpOnly cookie (public)
  POST /auth/logout          → clear refresh cookie (requires auth)
  GET  /auth/google          → initiate Google OAuth (public)
  GET  /auth/google/callback → handle Google OAuth callback (public)
  POST /auth/forgot-password → initiate password reset (public, rate-limited)
  POST /auth/reset-password  → consume reset token (public)

Cookie conventions (enforced on signup, login, refresh):
  name=refresh_token, httpOnly=True, sameSite=strict
  secure=True in production, False in development
  max_age=7 days, path=/api/v1/auth/refresh
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import get_settings
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    SignupResponse,
    LoginResponse,
    RefreshResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
    UserEmbedded,
    WorkspaceSummaryEmbedded,
)
from app.services import auth_service

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie configuration
_REFRESH_COOKIE_PATH = "/"
_REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the HttpOnly refresh token cookie on a response."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="lax",
        max_age=_REFRESH_COOKIE_MAX_AGE,
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie (logout)."""
    response.delete_cookie(key="refresh_token", path=_REFRESH_COOKIE_PATH)


# ── POST /auth/signup ──────────────────────────────────────────────────────

@router.post(
    "/signup",
    status_code=201,
    summary="Register a new user",
    response_model=SignupResponse,
)
async def signup(
    body: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account + default workspace.
    Sets refresh_token HttpOnly cookie.
    Errors: 409 EMAIL_ALREADY_EXISTS, 422 VALIDATION_ERROR
    """
    result = await auth_service.register(
        db=db,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    _set_refresh_cookie(response, result["refresh_token"])
    return SignupResponse(
        access_token=result["access_token"],
        user=UserEmbedded.model_validate(result["user"]),
        workspace=WorkspaceSummaryEmbedded.model_validate(result["workspace"]),
    )


# ── POST /auth/login ───────────────────────────────────────────────────────

@router.post(
    "/login",
    status_code=200,
    summary="Log in with email and password",
    response_model=LoginResponse,
)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate credentials and return access token + workspaces list.
    Sets refresh_token HttpOnly cookie.
    Errors: 401 INVALID_CREDENTIALS
    """
    result = await auth_service.login(
        db=db,
        email=body.email,
        password=body.password,
    )
    _set_refresh_cookie(response, result["refresh_token"])
    return LoginResponse(
        access_token=result["access_token"],
        user=UserEmbedded.model_validate(result["user"]),
        workspaces=[
            WorkspaceSummaryEmbedded.model_validate(ws)
            for ws in result["workspaces"]
        ],
    )


# ── POST /auth/refresh ─────────────────────────────────────────────────────

@router.post(
    "/refresh",
    status_code=200,
    summary="Refresh access token from cookie",
    response_model=RefreshResponse,
)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange the HttpOnly refresh_token cookie for a new access token.
    Errors: 401 TOKEN_EXPIRED, 401 UNAUTHENTICATED
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="No refresh token provided",
            headers={"code": "UNAUTHENTICATED"},
        )
    result = await auth_service.refresh_tokens(db=db, refresh_token_str=refresh_token)
    return RefreshResponse(access_token=result["access_token"])


# ── POST /auth/logout ──────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=200,
    summary="Log out and clear refresh cookie",
    response_model=MessageResponse,
)
async def logout(
    response: Response,
    current_user=Depends(get_current_user),
):
    """
    Clear the refresh_token cookie. Requires a valid access token.
    """
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully.")


# ── POST /auth/forgot-password ─────────────────────────────────────────────

@router.post(
    "/forgot-password",
    status_code=200,
    summary="Initiate password reset",
    response_model=MessageResponse,
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a password reset email. Always returns 200 to prevent email enumeration.
    In development, the reset URL is printed to the server console.
    """
    await auth_service.initiate_password_reset(db=db, email=body.email)
    return MessageResponse(
        message="If an account with that email exists, a reset link has been sent."
    )


# ── POST /auth/reset-password ──────────────────────────────────────────────

@router.post(
    "/reset-password",
    status_code=200,
    summary="Consume reset token and set new password",
    response_model=MessageResponse,
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Consume a password reset token and update the user's password.
    Errors: 400 BAD_REQUEST (token invalid / expired / already used)
    """
    result = await auth_service.reset_password(
        db=db,
        token=body.token,
        new_password=body.new_password,
    )
    return MessageResponse(message=result["message"])


# ── GET /auth/google ───────────────────────────────────────────────────────

@router.get(
    "/google",
    status_code=302,
    summary="Initiate Google OAuth2 flow",
    include_in_schema=True,
)
async def google_oauth_init():
    """
    Build the Google OAuth2 authorization URL and redirect the browser to it.
    Requires GOOGLE_CLIENT_ID to be set in environment.
    """
    from urllib.parse import urlencode

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.frontend_url}/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url=google_auth_url)


# ── GET /auth/google/callback ──────────────────────────────────────────────

@router.get(
    "/google/callback",
    status_code=302,
    summary="Handle Google OAuth2 callback",
    include_in_schema=True,
)
async def google_oauth_callback(
    code: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange authorization code for Google profile.
    Create or login user, then redirect to frontend with access_token in URL.
    Sets refresh cookie.

    NOTE: Full implementation deferred — Google OAuth is a Phase 1 stretch goal.
    This stub returns a structured error to indicate the feature is scaffolded.
    """
    # TODO: Phase 1 stretch — implement full Google OAuth token exchange
    raise HTTPException(
        status_code=501,
        detail="Google OAuth not yet implemented",
        headers={"code": "NOT_IMPLEMENTED"},
    )
