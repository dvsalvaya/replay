from fastapi import APIRouter
from app.auth.schemas import LoginRequest, TokenResponse
from app.auth.service import authenticate_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest) -> TokenResponse:
    """
    Realiza o login do usuário administrador utilizando credenciais fixas.
    Retorna o token de acesso JWT se bem-sucedido.
    """
    return authenticate_admin(login_data)
