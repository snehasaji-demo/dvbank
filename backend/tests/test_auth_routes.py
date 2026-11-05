import pytest

def test_auth_routes_flow(client):
    # 1. Register a new user specifically for this test flow to avoid side effects
    username = "auth_route_user"
    password = "testpass"
    reg_resp = client.post("/api/register", json={"username": username, "password": password})
    assert reg_resp.status_code == 201
    user_id = reg_resp.get_json()["id"]

    # 2. Login to get token
    login_resp = client.post("/api/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get profile
    profile_resp = client.get("/api/profile", headers=headers)
    assert profile_resp.status_code == 200
    profile_data = profile_resp.get_json()
    assert "fullName" in profile_data
    assert "email" in profile_data

    # 4. Update profile
    update_resp = client.put("/api/profile", json={
        "email": "new_email@example.com",
        "fullName": "New Full Name",
        "phone": "123456789",
        "address": "123 Test Lane"
    }, headers=headers)
    assert update_resp.status_code == 200
    assert "Profile updated successfully" in update_resp.get_json()["message"]

    # Verify profile was updated
    profile_resp2 = client.get("/api/profile", headers=headers)
    assert profile_resp2.get_json()["email"] == "new_email@example.com"
    assert profile_resp2.get_json()["fullName"] == "New Full Name"

    # 5. Update password
    update_pwd_resp = client.post("/api/update-password", json={
        "user_id": user_id,
        "new_password": "newpassword123"
    }, headers=headers)
    assert update_pwd_resp.status_code == 200
    assert "Password updated" in update_pwd_resp.get_json()["message"]

    # Verify login with new password
    login_resp2 = client.post("/api/login", json={"username": username, "password": "newpassword123"})
    assert login_resp2.status_code == 200
    token2 = login_resp2.get_json()["token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 6. Forgot password
    forgot_resp = client.post("/api/forgot-password", json={"username": username})
    assert forgot_resp.status_code == 200
    forgot_data = forgot_resp.get_json()
    assert "reset_link" in forgot_data
    debug_token = forgot_data["debug_token"]

    # 7. Reset password
    reset_resp = client.post("/api/reset-password", json={
        "username": username,
        "token": debug_token,
        "new_password": "finalpassword"
    })
    assert reset_resp.status_code == 200
    assert "Password has been reset" in reset_resp.get_json()["message"]

    # Verify login with reset password
    login_resp3 = client.post("/api/login", json={"username": username, "password": "finalpassword"})
    assert login_resp3.status_code == 200
    token3 = login_resp3.get_json()["token"]
    headers3 = {"Authorization": f"Bearer {token3}"}

    # 8. Import profile (YAML)
    import_resp = client.post("/api/profile/import", json={
        "profile_yaml": "fullName: Imported Name\nphone: '555-1234'\naddress: 456 Imported Rd"
    }, headers=headers3)
    assert import_resp.status_code == 200
    assert "Profile imported successfully" in import_resp.get_json()["message"]

    # Verify imported profile
    profile_resp3 = client.get("/api/profile", headers=headers3)
    assert profile_resp3.get_json()["fullName"] == "Imported Name"

    # 9. Logout
    logout_resp = client.post("/api/logout", headers=headers3)
    assert logout_resp.status_code == 200
    assert "Logged out successfully" in logout_resp.get_json()["message"]
