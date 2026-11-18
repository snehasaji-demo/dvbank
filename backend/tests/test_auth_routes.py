import hashlib

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_logout(client, alice):
    resp = client.post("/api/logout", headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert "Logged out successfully" in resp.get_json()["message"]

def test_get_profile(client, alice):
    resp = client.get("/api/profile", headers=_h(alice["token"]))
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fullName" in data
    assert "email" in data

def test_update_profile(client, alice):
    payload = {
        "email": "alice_new@example.com",
        "fullName": "Alice Tester",
        "phone": "123456789",
        "address": "123 Test St"
    }
    resp = client.put("/api/profile", json=payload, headers=_h(alice["token"]))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["profile"]["fullName"] == "Alice Tester"
    assert data["profile"]["email"] == "alice_new@example.com"

def test_update_password(client, alice):
    user_id = alice["user"]["id"]
    resp = client.post(
        "/api/update-password",
        json={"user_id": user_id, "new_password": "new_testpass"},
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert "Password updated" in resp.get_json()["message"]

def test_forgot_password(client):
    resp = client.post(
        "/api/forgot-password",
        json={"username": "alice_t"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reset_link" in data
    assert "debug_token" in data
    expected_token = hashlib.md5("alice_t".encode()).hexdigest()
    assert data["debug_token"] == expected_token

def test_reset_password_success(client):
    # First trigger forgot password to set reset_token
    client.post("/api/forgot-password", json={"username": "alice_t"})
    
    token = hashlib.md5("alice_t".encode()).hexdigest()
    resp = client.post(
        "/api/reset-password",
        json={
            "username": "alice_t",
            "token": token,
            "new_password": "reset_testpass"
        }
    )
    assert resp.status_code == 200
    assert "Password has been reset" in resp.get_json()["message"]

def test_reset_password_invalid_token(client):
    resp = client.post(
        "/api/reset-password",
        json={
            "username": "alice_t",
            "token": "invalid_token",
            "new_password": "reset_testpass"
        }
    )
    assert resp.status_code == 403
    assert "Invalid reset token" in resp.get_json()["error"]

def test_reset_password_user_not_found(client):
    resp = client.post(
        "/api/reset-password",
        json={
            "username": "nonexistent_user",
            "token": "some_token",
            "new_password": "reset_testpass"
        }
    )
    assert resp.status_code == 404
    assert "User not found" in resp.get_json()["error"]
