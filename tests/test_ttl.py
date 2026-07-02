from datetime import datetime, timedelta
import os
from app.config import settings
from app.videos.models import Video


def test_ttl_endpoints_unauthorized(client):
    response = client.get("/admin/ttl/status")
    assert response.status_code == 401

    response = client.post("/admin/ttl/run")
    assert response.status_code == 401


def test_ttl_status_authorized(client):
    login_response = client.post(
        "/auth/login",
        json={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/admin/ttl/status", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["scheduler_running"] is True


def test_ttl_run_cleans_expired(client, db_session):
    login_response = client.post(
        "/auth/login",
        json={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create an expired video and a dummy file
    dummy_path = os.path.join(settings.VIDEOS_DIR, "expired_test.mp4")
    os.makedirs(settings.VIDEOS_DIR, exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"dummy mp4 data")

    expired_video = Video(
        filename="expired_test.mp4",
        title="Expired Test",
        duration_seconds=10.0,
        file_size_bytes=14,
        file_path=dummy_path,
        expires_at=datetime.utcnow() - timedelta(minutes=5),
        is_deleted=False,
    )
    db_session.add(expired_video)
    db_session.commit()

    # Verify db has it
    assert db_session.query(Video).filter(Video.filename == "expired_test.mp4").count() == 1
    assert os.path.exists(dummy_path) is True

    # Patch SessionLocal in use_cases to use our db_session
    from app.application.ttl import use_cases
    original_session_local = use_cases.SessionLocal

    class MockSession:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            return getattr(db_session, name)
        def close(self):
            # Don't close session transaction in test
            pass

    use_cases.SessionLocal = MockSession

    try:
        # Run cleanup
        response = client.post("/admin/ttl/run", headers=headers)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["videos_deleted"] >= 1
        assert res_data["files_deleted"] >= 1

        # Verify file is deleted and record is removed
        assert os.path.exists(dummy_path) is False
        assert db_session.query(Video).filter(Video.filename == "expired_test.mp4").count() == 0
    finally:
        use_cases.SessionLocal = original_session_local
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
