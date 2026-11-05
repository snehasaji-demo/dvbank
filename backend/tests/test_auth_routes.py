import pytest
from datetime import datetime
from models import db, User

@pytest.fixture(autouse=True)
def setup_created_at(app):
    with app.app_context():
        for user in User.query.all():
            if user.created_at is None:
                user.created_at = datetime.utcnow()
        db.session.commit()

def test_logout(client, alice):
    resp = client.post("/api/logout", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Logged out successfully"

def test_get_profile(client, alice):
    resp = client.get("/api/profile", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert "fullName" in resp.get_json()

def test_update_profile(client, alice):
    resp = client.put("/api/profile", json={"email": "alice_new@example.com", "fullName": "Alice New", "phone": "123456", "address": "New Address"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["profile"]["fullName"] == "Alice New"

def test_update_password(client, alice):
    resp = client.post("/api/update-password", json={"user_id": alice["user"]["id"], "new_password": "newpassword"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Password updated"

def test_forgot_password_and_reset_password(client, alice):
    resp = client.post("/api/forgot-password", json={"username": "alice_t"}, headers={"Host": "localhost"})
    assert resp.status_code == 200
    debug_token = resp.get_json()["debug_token"]

    resp2 = client.post("/api/reset-password", json={"username": "alice_t", "token": debug_token, "new_password": "newpassword2"})
    assert resp2.status_code == 200
    assert resp2.get_json()["message"] == "Password has been reset"

def test_import_profile(client, alice):
    profile_yaml = """
    fullName: Alice Imported
    phone: '987654'
    address: Imported Address
    """
    resp = client.post("/api/profile/import", json={"profile_yaml": profile_yaml}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Profile imported successfully"
