from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="Nome de usuário do administrador")
    password: str = Field(..., description="Senha do administrador")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 480
