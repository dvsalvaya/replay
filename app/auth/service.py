import secrets
from fastapi import HTTPException, status
from app.auth.schemas import LoginRequest, TokenResponse
from app.config import settings
from app.core.security import create_access_token


def authenticate_admin(login_data: LoginRequest) -> TokenResponse:
    """
    Authenticate administrative credentials against settings.
    Returns a TokenResponse with a valid JWT.
    Raises HTTP 401 if authentication fails.
    """
    username_valid = secrets.compare_digest(login_data.username, settings.ADMIN_USERNAME)
    password_valid = secrets.compare_digest(login_data.password, settings.ADMIN_PASSWORD)

    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    # Sub claim maps to the username
    access_token = create_access_token(data={"sub": login_data.username})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
