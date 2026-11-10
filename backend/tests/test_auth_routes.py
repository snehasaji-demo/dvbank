import backend.routes.auth_routes

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
    assert "email" in data

def test_update_profile(client, alice):
    resp = client.put(
        "/api/profile",
        json={
            "email": "alice_new@example.com",
            "fullName": "Alice Tester",
            "phone": "123456",
            "address": "123 Main St"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["profile"]["email"] == "alice_new@example.com"
    assert data["profile"]["fullName"] == "Alice Tester"

def test_update_password(client, alice):
    resp = client.post(
        "/api/update-password",
        json={
            "user_id": alice["user"]["id"],
            "new_password": "newpassword123"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert "Password updated" in resp.get_json()["message"]

def test_update_password_not_found(client, alice):
    resp = client.post(
        "/api/update-password",
        json={
            "user_id": 999999,
            "new_password": "newpassword123"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 404

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
    client.post(
        "/api/forgot-password",
        json={"username": "alice_t"}
    )
    import hashlib
    token = hashlib.md5("alice_t".encode()).hexdigest()
    resp = client.post(
        "/api/reset-password",
        json={
            "username": "alice_t",
            "token": token,
            "new_password": "resetpassword123"
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
            "new_password": "resetpassword123"
        }
    )
    assert resp.status_code == 403

def test_reset_password_user_not_found(client):
    resp = client.post(
        "/api/reset-password",
        json={
            "username": "nonexistent_user",
            "token": "some_token",
            "new_password": "resetpassword123"
        }
    )
    assert resp.status_code == 404
