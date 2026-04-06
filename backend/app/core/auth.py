import os
import secrets

from fastapi import HTTPException, Request, Response, status

from app.core.ssm import get_admin_password
from app.services import store

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_PARAMETER_NAME = os.getenv("ADMIN_PASSWORD_PARAMETER_NAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")
ADMIN_SESSION_COOKIE = "family_meal_planner_admin_session"
_USE_SECURE_COOKIE = os.getenv("SECURE_COOKIE", "").lower() in ("1", "true", "yes")
_COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax").lower()

_active_sessions: set[str] = set()


def _is_session_valid(token: str) -> bool:
    """Check local cache first, then DynamoDB if available."""
    if token in _active_sessions:
        return True
    if store.session_exists(token):
        _active_sessions.add(token)
        return True
    return False


def resolve_admin_password() -> str:
    if ADMIN_PASSWORD_PARAMETER_NAME:
        ssm_password = get_admin_password(ADMIN_PASSWORD_PARAMETER_NAME)
        if ssm_password is not None:
            return ssm_password
    return ADMIN_PASSWORD


def get_current_admin(request: Request) -> str:
    cookie_value = request.cookies.get(ADMIN_SESSION_COOKIE)
    if not cookie_value or not _is_session_valid(cookie_value):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Accès administrateur requis",
        )
    return ADMIN_USERNAME


def login_admin(response: Response, username: str, password: str) -> None:
    if username != ADMIN_USERNAME or password != resolve_admin_password():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe invalide",
        )

    token = secrets.token_urlsafe(32)
    _active_sessions.add(token)
    store.save_session(token)

    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite=_COOKIE_SAMESITE,
        secure=_USE_SECURE_COOKIE,
    )


def logout_admin(response: Response) -> None:
    response.delete_cookie(key=ADMIN_SESSION_COOKIE)


def invalidate_session(token: str) -> None:
    _active_sessions.discard(token)
    store.delete_session(token)


def is_admin_authenticated(request: Request) -> bool:
    cookie_value = request.cookies.get(ADMIN_SESSION_COOKIE)
    return bool(cookie_value and _is_session_valid(cookie_value))
