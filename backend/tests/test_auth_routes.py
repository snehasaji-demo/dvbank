import hashlib
import pytest
from routes import auth_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_logout(client, alice):
    headers = _h(alice["token"])
    resp = client.post("/api/logout", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_profile(client, alice):
    headers = _h(alice["token"])
    resp = client.get("/api/profile", headers=headers)
    assert resp.status_code == 200
    assert "fullName" in resp.get_json()

def test_update_profile(client, alice):
    headers = _h(alice["token"])
    resp = client.put("/api/profile", json={
        "email": "alice@example.com",
        "fullName": "Alice Tester",
        "phone": "123456",
        "address": "123 Main St"
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["profile"]["email"] == "alice@example.com"

def test_update_password(client, alice):
    headers = _h(alice["token"])
    resp = client.post("/api/update-password", json={
        "user_id": alice["user"]["id"],
        "new_password": "newpassword"
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password updated"

def test_forgot_password(client):
    resp = client.post("/api/forgot-password", json={"username": "alice_t"})
    assert resp.status_code == 200
    assert "reset_link" in resp.get_json()

def test_reset_password(client):
    token = hashlib.md5("alice_t".encode()).hexdigest()
    resp = client.post("/api/reset-password", json={
        "username": "alice_t",
        "token": token,
        "new_password": "anotherpassword"
    })
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password has been reset"
