import pickle
import base64
import hashlib
from unittest.mock import patch
from flask import Response
import backend.routes.admin_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_download_statement(client, alice):
    with patch('backend.routes.admin_routes.send_file') as mock_send_file:
        mock_send_file.return_value = Response("statement content", status=200)
        resp = client.get(
            "/api/admin/download-statement?filename=statement.pdf",
            headers=_h(alice["token"])
        )
        assert resp.status_code == 200
        mock_send_file.assert_called_once()

def test_import_session(client, alice):
    session_info = {"user_id": 1, "username": "test"}
    serialized = base64.b64encode(pickle.dumps(session_info)).decode('utf-8')
    resp = client.post(
        "/api/admin/import-session",
        json={"session_data": serialized},
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert "session" in resp.get_json()

def test_export_session(client, alice):
    resp = client.post(
        "/api/admin/export-session",
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "session_data" in data
    decoded = base64.b64decode(data["session_data"])
    session = pickle.loads(decoded)
    assert session["username"] == "alice_t"

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=http://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://example.com"

def test_generate_api_token(client, alice):
    resp = client.post(
        "/api/admin/generate-token",
        json={"seed": "myseed"},
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "api_token" in data
    expected = hashlib.md5(f"myseed{alice['user']['id']}".encode()).hexdigest()
    assert data["api_token"] == expected

def test_master_login_success(client, alice):
    resp = client.post(
        "/api/admin/master-login",
        json={"password": "MasterAdmin@2024!"},
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["admin"] is True

def test_master_login_failure(client, alice):
    resp = client.post(
        "/api/admin/master-login",
        json={"password": "wrongpassword"},
        headers=_h(alice["token"])
    )
    assert resp.status_code == 403
