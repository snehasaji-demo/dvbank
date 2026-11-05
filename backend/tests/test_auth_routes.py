import pytest
import json

def test_logout(client, alice):
    resp = client.post("/api/logout", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_profile(client, alice):
    resp = client.get("/api/profile", headers={"Authorization": f"Bearer {alice['token']}"})
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
    resp = client.put("/api/profile", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Profile updated successfully"
    assert data["profile"]["email"] == "alice_new@example.com"

def test_update_password(client, alice):
    payload = {
        "user_id": alice["user"]["id"],
        "new_password": "newpassword123"
    }
    resp = client.post("/api/update-password", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password updated"

def test_update_password_not_found(client, alice):
    payload = {
        "user_id": 99999,
        "new_password": "newpassword123"
    }
    resp = client.post("/api/update-password", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 404

def test_forgot_password(client):
    payload = {"username": "alice_t"}
    resp = client.post("/api/forgot-password", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reset_link" in data
    assert "debug_token" in data

def test_reset_password(client):
    # First trigger forgot password to set reset token
    client.post("/api/forgot-password", json={"username": "alice_t"})
    import hashlib
    token = hashlib.md5("alice_t".encode()).hexdigest()
    
    payload = {
        "username": "alice_t",
        "token": token,
        "new_password": "resetpassword123"
    }
    resp = client.post("/api/reset-password", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password has been reset"

def test_reset_password_invalid_token(client):
    payload = {
        "username": "alice_t",
        "token": "invalid_token",
        "new_password": "resetpassword123"
    }
    resp = client.post("/api/reset-password", json=payload)
    assert resp.status_code == 403

def test_reset_password_user_not_found(client):
    payload = {
        "username": "nonexistent_user",
        "token": "some_token",
        "new_password": "resetpassword123"
    }
    resp = client.post("/api/reset-password", json=payload)
    assert resp.status_code == 404

def test_import_profile(client, alice):
    yaml_content = """
    fullName: Alice Imported
    phone: '987654321'
    address: '456 Imported Rd'
    """
    payload = {"profile_yaml": yaml_content}
    resp = client.post("/api/profile/import", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Profile imported successfully"

def test_import_profile_invalid_format(client, alice):
    yaml_content = """
    - item1
    - item2
    """
    payload = {"profile_yaml": yaml_content}
    resp = client.post("/api/profile/import", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()
