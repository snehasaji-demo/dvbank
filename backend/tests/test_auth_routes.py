def test_logout(client, alice):
    resp = client.post("/api/logout", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_profile(client, alice):
    resp = client.get("/api/profile", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fullName" in data

def test_update_profile(client, alice):
    resp = client.put("/api/profile", headers={"Authorization": f"Bearer {alice['token']}"}, json={
        "email": "alice_new@example.com",
        "fullName": "Alice New",
        "phone": "123456789",
        "address": "123 Main St"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Profile updated successfully"
    assert data["profile"]["email"] == "alice_new@example.com"

def test_update_password(client, alice):
    resp = client.post("/api/update-password", headers={"Authorization": f"Bearer {alice['token']}"}, json={
        "user_id": alice["user"]["id"],
        "new_password": "newpassword"
    })
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password updated"

def test_forgot_password(client):
    resp = client.post("/api/forgot-password", json={"username": "alice_t"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reset_link" in data
    assert "debug_token" in data

def test_reset_password(client):
    resp_forgot = client.post("/api/forgot-password", json={"username": "alice_t"})
    token = resp_forgot.get_json()["debug_token"]
    
    resp_reset = client.post("/api/reset-password", json={
        "username": "alice_t",
        "token": token,
        "new_password": "resetpassword"
    })
    assert resp_reset.status_code == 200
    assert resp_reset.get_json()["message"] == "Password has been reset"

def test_import_profile(client, alice):
    resp = client.post("/api/profile/import", headers={"Authorization": f"Bearer {alice['token']}"}, json={
        "profile_yaml": "fullName: Alice Imported\nphone: 987654321\naddress: 456 Oak Rd"
    })
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Profile imported successfully"

def test_import_profile_invalid(client, alice):
    resp = client.post("/api/profile/import", headers={"Authorization": f"Bearer {alice['token']}"}, json={
        "profile_yaml": "[invalid yaml"
    })
    assert resp.status_code == 400
