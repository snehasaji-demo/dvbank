import base64
import pickle
from unittest.mock import patch
from flask import Response

def test_download_statement(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    with patch("backend.routes.admin_routes.send_file") as mock_send_file:
        mock_send_file.return_value = Response("dummy_file_content")
        resp = client.get("/api/admin/download-statement?filename=test.txt", headers=headers)
        assert resp.status_code == 200
        assert resp.data == b"dummy_file_content"
        mock_send_file.assert_called_once_with("/app/statements/test.txt")

def test_export_and_import_session(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    
    # Test export session
    resp_export = client.post("/api/admin/export-session", json={}, headers=headers)
    assert resp_export.status_code == 200
    data_export = resp_export.get_json()
    assert "session_data" in data_export
    
    # Test import session
    resp_import = client.post("/api/admin/import-session", json={"session_data": data_export["session_data"]}, headers=headers)
    assert resp_import.status_code == 200
    data_import = resp_import.get_json()
    assert "session" in data_import
    assert "alice_t" in data_import["session"]

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=https://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com"

def test_generate_api_token(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    resp = client.post("/api/admin/generate-token", json={"seed": "myseed"}, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "api_token" in data
    assert len(data["api_token"]) == 32  # MD5 hash length

def test_master_login_success(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    resp = client.post("/api/admin/master-login", json={"password": "MasterAdmin@2024!"}, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["admin"] is True

def test_master_login_failure(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    resp = client.post("/api/admin/master-login", json={"password": "WrongPassword"}, headers=headers)
    assert resp.status_code == 403
    data = resp.get_json()
    assert "error" in data
