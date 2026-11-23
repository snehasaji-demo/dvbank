import hashlib

def test_logout(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    resp = client.post("/api/logout", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_and_update_profile(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    
    # Get profile initially
    resp = client.get("/api/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fullName" in data
    
    # Update profile
    update_data = {
        "fullName": "Alice Tester",
        "email": "alice_test@example.com",
        "phone": "1234567890",
        "address": "123 Test St"
    }
    resp_update = client.put("/api/profile", json=update_data, headers=headers)
    assert resp_update.status_code == 200
    assert resp_update.get_json()["message"] == "Profile updated successfully"
    
    # Get profile again to verify
    resp_get = client.get("/api/profile", headers=headers)
    assert resp_get.status_code == 200
    data_get = resp_get.get_json()
    assert data_get["fullName"] == "Alice Tester"
    assert data_get["email"] == "alice_test@example.com"
    assert data_get["phone"] == "1234567890"
    assert data_get["address"] == "123 Test St"

def test_update_password(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    user_id = alice["user"]["id"]
    
    resp = client.post("/api/update-password", json={"user_id": user_id, "new_password": "newtestpass"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password updated"

def test_forgot_and_reset_password(client, alice):
    username = alice["user"]["username"]
    
    # Forgot password
    resp_forgot = client.post("/api/forgot-password", json={"username": username})
    assert resp_forgot.status_code == 200
    data_forgot = resp_forgot.get_json()
    assert "debug_token" in data_forgot
    token = data_forgot["debug_token"]
    assert token == hashlib.md5(username.encode()).hexdigest()
    
    # Reset password
    resp_reset = client.post("/api/reset-password", json={
        "username": username,
        "token": token,
        "new_password": "resetpass123"
    })
    assert resp_reset.status_code == 200
    assert resp_reset.get_json()["message"] == "Password has been reset"
