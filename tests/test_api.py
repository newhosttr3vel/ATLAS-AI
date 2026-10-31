from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "ATLAS AI",
        "mode": "foundation",
    }


def test_api_uses_atlas_ai_branding() -> None:
    assert app.title == "ATLAS AI API"
