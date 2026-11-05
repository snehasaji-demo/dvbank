import pytest
import json

def test_logout(client, alice):
    # Test logout endpoint
    resp = client.post("/api/logout", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_profile(client, alice):
    # Test get profile endpoint
    resp = client.get("/api/profile", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fullName" in data
    assert "email" in data

def test_update_profile(client, alice):
    # Test update profile endpoint
    payload = {
        "email": "alice_new@example.com",
        "fullName": "Alice Tester",
        "phone": "1234567890",
        "address": "123 Test St"
    }
    resp = client.put("/api/profile", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Profile updated successfully"
    assert data["profile"]["email"] == "alice_new@example.com"
    assert data["profile"]["fullName"] == "Alice Tester"

def test_update_password(client, alice):
    # Test update password endpoint
    payload = {
        "user_id": alice["user"]["id"],
        "new_password": "newtestpass"
    }
    resp = client.post("/api/update-password", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password updated"

def test_update_password_not_found(client, alice):
    # Test update password with non-existent user
    payload = {
        "user_id": 99999,
        "new_password": "newtestpass"
    }
    resp = client.post("/api/update-password", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 404

def test_forgot_password(client):
    # Test forgot password endpoint
    payload = {"username": "alice_t"}
    resp = client.post("/api/forgot-password", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reset_link" in data
    assert "debug_token" in data

def test_reset_password(client):
    # Test reset password endpoint
    # First trigger forgot password to set reset_token
    client.post("/api/forgot-password", json={"username": "alice_t"})
    
    # Now reset password
    import hashlib
    token = hashlib.md5("alice_t".encode()).hexdigest()
    payload = {
        "username": "alice_t",
        "token": token,
        "new_password": "resettestpass"
    }
    resp = client.post("/api/reset-password", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password has been reset"

def test_reset_password_invalid_token(client):
    payload = {
        "username": "alice_t",
        "token": "invalid_token",
        "new_password": "resettestpass"
    }
    resp = client.post("/api/reset-password", json=payload)
    assert resp.status_code == 403

def test_reset_password_user_not_found(client):
    payload = {
        "username": "non_existent_user",
        "token": "some_token",
        "new_password": "resettestpass"
    }
    resp = client.post("/api/reset-password", json=payload)
    assert resp.status_code == 404

def test_import_profile(client, alice):
    # Test import profile endpoint with valid YAML
    yaml_data = "fullName: Alice Imported\nphone: 9876543210\naddress: 456 Import Rd"
    payload = {"profile_yaml": yaml_data}
    resp = client.post("/api/profile/import", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Profile imported successfully"

def test_import_profile_invalid_format(client, alice):
    # Test import profile endpoint with invalid format (not a dict)
    yaml_data = "- item1\n- item2"
    payload = {"profile_yaml": yaml_data}
    resp = client.post("/api/profile/import", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()
