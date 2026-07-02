from app.config import settings


def test_get_videos_unauthorized(client):
    """Test that requesting videos endpoint without authorization returns 401."""
    response = client.get("/videos")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token não fornecido"


def test_get_videos_authorized(client):
    """Test that requesting videos endpoint with a valid token returns 200 and an empty list."""
    login_response = client.post(
        "/auth/login",
        json={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get("/videos", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_health_check(client):
    """Test public health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
