import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_current_user
from app.crud import user as user_crud
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserRead
from app.services import google_oauth_service

from app.services import google_oauth_service, otp_service, email_service
from app.schemas.user import OTPVerifyRequest, OTPResendRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Short-lived in-memory store for OAuth "state" CSRF tokens.
# Fine for a single-instance dev/staging deployment; swap for Redis if you
# ever run multiple backend replicas behind a load balancer.
_pending_states: dict[str, float] = {}
_STATE_TTL_SECONDS = 300


def _issue_state() -> str:
    state = secrets.token_urlsafe(24)
    _pending_states[state] = time.time()
    return state


def _consume_state(state: str) -> bool:
    issued_at = _pending_states.pop(state, None)
    if issued_at is None:
        return False
    return (time.time() - issued_at) <= _STATE_TTL_SECONDS


@router.get("/google/login")
def google_login():
    """Redirect the browser to Google's SSO consent screen."""
    state = _issue_state()
    auth_url = google_oauth_service.build_google_auth_url(state)
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Google redirects here after the user approves SSO login."""
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/login?error={error}")

    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state or not _consume_state(state):
        return RedirectResponse(
            f"{settings.FRONTEND_BASE_URL}/login?error=invalid_state"
        )

    try:
        tokens = await google_oauth_service.exchange_code_for_token(code)
        profile = await google_oauth_service.fetch_google_userinfo(
            tokens["access_token"]
        )
    except Exception:
        return RedirectResponse(
            f"{settings.FRONTEND_BASE_URL}/login?error=google_auth_failed"
        )

    if not profile.get("email_verified", True):
        return RedirectResponse(
            f"{settings.FRONTEND_BASE_URL}/login?error=email_not_verified"
        )

    user = user_crud.get_or_create_from_google(
        db,
        google_id=profile["sub"],
        email=profile["email"],
        name=profile.get("name", profile["email"]),
        avatar_url=profile.get("picture"),
    )

    # --- NEW: don't issue a JWT yet, require OTP first ---
    otp_session_id, otp_code = otp_service.create_otp_session(user.id, user.email)
    await email_service.send_otp_email(user.email, otp_code)

    redirect_url = f"{settings.FRONTEND_BASE_URL}/verify-otp?session={otp_session_id}"
    return RedirectResponse(redirect_url)


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user_id = otp_service.verify_otp(payload.session, payload.code)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code.",
        )

    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    jwt_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=jwt_token, user=user)


@router.post("/otp/resend")
async def resend_otp(payload: OTPResendRequest):
    email = otp_service.peek_email(payload.session)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Session expired."
        )

    new_code = otp_service.regenerate_code(payload.session)
    if new_code is None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another code.",
        )

    await email_service.send_otp_email(email, new_code)
    return {"detail": "Code resent."}


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout():
    # Stateless JWT: logout is handled client-side by discarding the token.
    return {"detail": "Logged out"}
