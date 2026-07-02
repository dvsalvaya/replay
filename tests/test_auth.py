from app.config import settings


def test_login_success(client):
    """Test successful login with correct admin credentials."""
    response = client.post(
        "/auth/login",
        json={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES


def test_login_wrong_password(client):
    """Test login failure with incorrect password."""
    response = client.post(
        "/auth/login",
        json={
            "username": settings.ADMIN_USERNAME,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


def test_login_wrong_username(client):
    """Test login failure with incorrect username."""
    response = client.post(
        "/auth/login",
        json={
            "username": "wronguser",
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


def test_access_with_invalid_token(client):
    """Test accessing protected route with an invalid token."""
    response = client.get(
        "/videos", headers={"Authorization": "Bearer invalidtoken123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido ou expirado"


def test_access_with_missing_token(client):
    """Test accessing protected route without a token."""
    response = client.get("/videos")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token não fornecido"
