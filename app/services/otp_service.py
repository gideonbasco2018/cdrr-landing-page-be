import hashlib
import secrets
import time

from app.core.config import settings

# In-memory OTP session store. Same caveat as _pending_states in auth.py —
# swap for Redis if you run multiple replicas.
_otp_sessions: dict[str, dict] = {}

OTP_TTL_SECONDS = 5 * 60  # 5 minutes to enter the code
OTP_LENGTH = 6
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 30


def _hash_code(code: str) -> str:
    return hashlib.sha256(f"{code}{settings.JWT_SECRET_KEY}".encode()).hexdigest()


def _generate_code() -> str:
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def create_otp_session(user_id: int, email: str) -> tuple[str, str]:
    """Creates a new OTP session and returns (session_id, plaintext_code)."""
    session_id = secrets.token_urlsafe(32)
    code = _generate_code()

    _otp_sessions[session_id] = {
        "user_id": user_id,
        "email": email,
        "code_hash": _hash_code(code),
        "created_at": time.time(),
        "last_sent_at": time.time(),
        "attempts": 0,
    }
    return session_id, code


def regenerate_code(session_id: str) -> str | None:
    """For resend. Returns new plaintext code, or None if cooldown/session invalid."""
    session = _otp_sessions.get(session_id)
    if session is None:
        return None

    if time.time() - session["last_sent_at"] < RESEND_COOLDOWN_SECONDS:
        return None

    code = _generate_code()
    session["code_hash"] = _hash_code(code)
    session["last_sent_at"] = time.time()
    session["created_at"] = time.time()
    session["attempts"] = 0
    return code


def verify_otp(session_id: str, code: str) -> int | None:
    """Returns user_id if valid, else None. Consumes the session on success."""
    session = _otp_sessions.get(session_id)
    if session is None:
        return None

    if time.time() - session["created_at"] > OTP_TTL_SECONDS:
        _otp_sessions.pop(session_id, None)
        return None

    if session["attempts"] >= MAX_ATTEMPTS:
        _otp_sessions.pop(session_id, None)
        return None

    session["attempts"] += 1

    if not secrets.compare_digest(session["code_hash"], _hash_code(code)):
        return None

    user_id = session["user_id"]
    _otp_sessions.pop(session_id, None)
    return user_id


def peek_email(session_id: str) -> str | None:
    session = _otp_sessions.get(session_id)
    return session["email"] if session else None
