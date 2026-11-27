def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_logout(client, alice):
    resp = client.post("/api/logout", headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_profile(client, alice):
    resp = client.get("/api/profile", headers=_h(alice["token"]))
    assert resp.status_code == 200
    data = resp.get_json()
    assert "email" in data

def test_update_profile(client, alice):
    resp = client.put(
        "/api/profile",
        json={
            "email": "new_email@example.com",
            "fullName": "Alice New",
            "phone": "123456",
            "address": "123 St"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["profile"]["fullName"] == "Alice New"
    assert data["profile"]["email"] == "new_email@example.com"

def test_update_password(client, alice):
    resp = client.post(
        "/api/update-password",
        json={
            "user_id": alice["user"]["id"],
            "new_password": "new_secure_password"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password updated"

def test_forgot_password(client):
    resp = client.post(
        "/api/forgot-password",
        json={"username": "alice_t"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reset_link" in data
    assert "debug_token" in data

def test_reset_password(client):
    # First request forgot password to set reset_token
    resp = client.post(
        "/api/forgot-password",
        json={"username": "alice_t"}
    )
    assert resp.status_code == 200
    token = resp.get_json()["debug_token"]

    # Now reset password
    resp = client.post(
        "/api/reset-password",
        json={
            "username": "alice_t",
            "token": token,
            "new_password": "reset_password_123"
        }
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password has been reset"
