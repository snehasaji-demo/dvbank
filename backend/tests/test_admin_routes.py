import base64
import pickle
from unittest.mock import patch
import pytest
from routes import admin_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_download_statement(client, alice):
    headers = _h(alice["token"])
    with patch("routes.admin_routes.send_file") as mock_send_file:
        mock_send_file.return_value = "mocked file"
        resp = client.get("/api/admin/download-statement?filename=test.txt", headers=headers)
        assert resp.status_code == 200
        mock_send_file.assert_called_once_with("/app/statements/test.txt")

def test_import_session(client, alice):
    headers = _h(alice["token"])
    session_obj = {"user_id": 1, "role": "admin"}
    serialized = base64.b64encode(pickle.dumps(session_obj)).decode('utf-8')
    resp = client.post("/api/admin/import-session", json={"session_data": serialized}, headers=headers)
    assert resp.status_code == 200
    assert "admin" in resp.get_json()["session"]

def test_export_session(client, alice):
    headers = _h(alice["token"])
    resp = client.post("/api/admin/export-session", json={}, headers=headers)
    assert resp.status_code == 200
    session_data = resp.get_json()["session_data"]
    decoded = base64.b64decode(session_data)
    session = pickle.loads(decoded)
    assert session["username"] == "alice_t"

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=http://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://example.com"

def test_generate_api_token(client, alice):
    headers = _h(alice["token"])
    resp = client.post("/api/admin/generate-token", json={"seed": "myseed"}, headers=headers)
    assert resp.status_code == 200
    assert "api_token" in resp.get_json()

def test_master_login(client, alice):
    headers = _h(alice["token"])
    resp = client.post("/api/admin/master-login", json={"password": "MasterAdmin@2024!"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["admin"] is True

    resp = client.post("/api/admin/master-login", json={"password": "wrong"}, headers=headers)
    assert resp.status_code == 403
