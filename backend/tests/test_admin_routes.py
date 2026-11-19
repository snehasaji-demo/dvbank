from unittest.mock import patch
import base64
import pickle
from routes import admin_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_download_statement(client, alice):
    with patch('routes.admin_routes.send_file') as mock_send_file:
        mock_send_file.return_value = "dummy_file"
        resp = client.get("/api/admin/download-statement?filename=test.txt", headers=_h(alice["token"]))
        assert resp.status_code == 200
        assert resp.data == b"dummy_file"
        mock_send_file.assert_called_once_with("/app/statements/test.txt")

def test_import_session(client, alice):
    session_data = base64.b64encode(pickle.dumps({"key": "value"})).decode('utf-8')
    resp = client.post("/api/admin/import-session", json={"session_data": session_data}, headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert "key" in resp.get_json()["session"]

def test_export_session(client, alice):
    resp = client.post("/api/admin/export-session", headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert "session_data" in resp.get_json()

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=https://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com"

def test_generate_api_token(client, alice):
    resp = client.post("/api/admin/generate-token", json={"seed": "myseed"}, headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert "api_token" in resp.get_json()

def test_master_login_success(client, alice):
    resp = client.post("/api/admin/master-login", json={"password": "MasterAdmin@2024!"}, headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert resp.get_json()["admin"] is True

def test_master_login_failure(client, alice):
    resp = client.post("/api/admin/master-login", json={"password": "wrong_password"}, headers=_h(alice["token"]))
    assert resp.status_code == 403
