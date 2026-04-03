import os

from fastapi import HTTPException, Request, Response, status

from app.core.ssm import get_admin_password

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_PARAMETER_NAME = os.getenv("ADMIN_PASSWORD_PARAMETER_NAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")
ADMIN_SESSION_COOKIE = "family_meal_planner_admin_session"
ADMIN_SESSION_TOKEN = "authenticated"


def resolve_admin_password() -> str:
    if ADMIN_PASSWORD_PARAMETER_NAME:
        return get_admin_password(ADMIN_PASSWORD_PARAMETER_NAME)
    return ADMIN_PASSWORD


def get_current_admin(request: Request) -> str:
    cookie_value = request.cookies.get(ADMIN_SESSION_COOKIE)
    if cookie_value != ADMIN_SESSION_TOKEN:
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

    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=ADMIN_SESSION_TOKEN,
        httponly=True,
        samesite="lax",
    )


def logout_admin(response: Response) -> None:
    response.delete_cookie(key=ADMIN_SESSION_COOKIE)


def is_admin_authenticated(request: Request) -> bool:
    return request.cookies.get(ADMIN_SESSION_COOKIE) == ADMIN_SESSION_TOKEN
