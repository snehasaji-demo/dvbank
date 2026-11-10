import hashlib
import backend.routes.auth_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_logout(client, alice):
    resp = client.post(
        "/api/logout",
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_profile(client, alice):
    resp = client.get(
        "/api/profile",
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fullName" in data
    assert "email" in data

def test_update_profile(client, alice):
    resp = client.put(
        "/api/profile",
        json={
            "email": "alice_new@example.com",
            "fullName": "Alice Tester",
            "phone": "123456789",
            "address": "123 Test St"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["profile"]["fullName"] == "Alice Tester"
    assert data["profile"]["phone"] == "123456789"

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
    # First trigger forgot password to set the token
    client.post(
        "/api/forgot-password",
        json={"username": "alice_t"}
    )
    token = hashlib.md5(b"alice_t").hexdigest()
    resp = client.post(
        "/api/reset-password",
        json={
            "username": "alice_t",
            "token": token,
            "new_password": "testpass"  # reset back to testpass so other tests don't break
        }
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password has been reset"
