import pytest


@pytest.mark.asyncio
async def test_register_login_refresh_logout_flow(client):
    register_payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Str0ngPass!",
        "preferences": {"theme": "dark"},
    }
    response = await client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == register_payload["email"]
    assert data["username"] == register_payload["username"]

    login_payload = {"email": register_payload["email"], "password": register_payload["password"]}
    response = await client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    refresh_payload = {"refresh_token": tokens["refresh_token"]}
    response = await client.post("/api/auth/refresh", json=refresh_payload)
    assert response.status_code == 200
    refreshed = response.json()
    assert "access_token" in refreshed
    assert "refresh_token" in refreshed

    logout_payload = {"refresh_token": refreshed["refresh_token"]}
    response = await client.post("/api/auth/logout", json=logout_payload)
    assert response.status_code == 204

