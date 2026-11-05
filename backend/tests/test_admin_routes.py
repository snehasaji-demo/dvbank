import pytest
import os
import json
from datetime import datetime

@pytest.fixture
def admin_user(client, app):
    from models import db, User
    with app.app_context():
        admin = User.query.filter_by(username="admin_t").first()
        if not admin:
            client.post("/api/register", json={"username": "admin_t", "password": "testpass"})
            admin = User.query.filter_by(username="admin_t").first()
        admin.role = "admin"
        if admin.created_at is None:
            admin.created_at = datetime.utcnow()
        db.session.commit()
    resp = client.post("/api/login", json={"username": "admin_t", "password": "testpass"})
    return resp.get_json()

def test_generate_report(client, admin_user, monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: "mocked report output")
    resp = client.post(
        "/api/admin/generate-report",
        json={"report_type": "summary", "date_range": "today"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["report"] == "mocked report output"

def test_system_status(client, admin_user, monkeypatch):
    class MockPopen:
        def read(self):
            return "mocked systemctl output"
    monkeypatch.setattr(os, "popen", lambda *args, **kwargs: MockPopen())
    resp = client.get(
        "/api/admin/system-status?service=web",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "mocked systemctl output"

def test_ping_host(client, admin_user, monkeypatch):
    import subprocess
    class MockCompletedProcess:
        stdout = "mocked ping output"
        stderr = ""
        returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: MockCompletedProcess())
    resp = client.post(
        "/api/admin/ping",
        json={"host": "127.0.0.1"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["stdout"] == "mocked ping output"

def test_dns_lookup(client, admin_user, monkeypatch):
    import subprocess
    class MockPopen:
        def communicate(self):
            return b"mocked dns output", b""
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: MockPopen())
    resp = client.get(
        "/api/admin/dns-lookup?domain=google.com",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["result"] == "mocked dns output"

def test_webhook(client, admin_user, monkeypatch):
    import requests
    class MockResponse:
        status_code = 200
        text = "mocked webhook response"
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse())
    resp = client.post(
        "/api/admin/webhook-test",
        json={"url": "http://example.com"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["body"] == "mocked webhook response"

def test_fetch_avatar(client, admin_user, monkeypatch):
    import requests
    class MockResponse:
        content = b"mocked avatar content"
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse())
    resp = client.post(
        "/api/admin/fetch-avatar",
        json={"avatar_url": "http://example.com/avatar.png"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    import base64
    expected = base64.b64encode(b"mocked avatar content").decode('utf-8')
    assert resp.get_json()["avatar_base64"] == expected

def test_download_statement(client, admin_user, monkeypatch):
    monkeypatch.setattr("routes.admin_routes.send_file", lambda *args, **kwargs: "mocked file response")
    resp = client.get(
        "/api/admin/download-statement?filename=statement.pdf",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.data == b"mocked file response"

def test_view_log(client, admin_user, monkeypatch):
    from unittest.mock import mock_open
    monkeypatch.setattr("builtins.open", mock_open(read_data="mocked log content"))
    resp = client.get(
        "/api/admin/view-log?file=app.log",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["log"] == "mocked log content"

def test_import_data(client, admin_user):
    xml_data = """<transactions>
        <transaction>
            <sender>alice</sender>
            <receiver>bob</receiver>
            <amount>100</amount>
            <description>test import</description>
        </transaction>
    </transactions>"""
    resp = client.post(
        "/api/admin/import-data",
        data=xml_data,
        content_type="application/xml",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["imported"] == 1
    assert data["records"][0]["sender"] == "alice"

def test_import_session(client, admin_user):
    import pickle
    import base64
    session_info = {"user_id": 1, "username": "admin"}
    serialized = base64.b64encode(pickle.dumps(session_info)).decode('utf-8')
    resp = client.post(
        "/api/admin/import-session",
        json={"session_data": serialized},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert "session" in resp.get_json()

def test_export_session(client, admin_user):
    resp = client.post(
        "/api/admin/export-session",
        json={},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert "session_data" in resp.get_json()

def test_update_user(client, admin_user):
    resp = client.put(
        f"/api/admin/users/{admin_user['user']['id']}",
        json={"email": "admin_updated@example.com"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "admin_updated@example.com"

def test_preview_email(client, admin_user):
    resp = client.post(
        "/api/admin/preview-email",
        json={"template": "Hello {{ recipient }}", "recipient": "Alice"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["preview"] == "Hello Alice"

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=http://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://example.com"

def test_create_audit_entry(client, admin_user):
    resp = client.post(
        "/api/admin/audit",
        json={"action": "test_action", "details": "test_details"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Audit entry created"

def test_list_all_users(client, admin_user):
    resp = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert len(resp.get_json()) > 0

def test_delete_user(client, admin_user, app):
    from models import db, User
    with app.app_context():
        temp_user = User(username="temp_user", password_hash="hash")
        db.session.add(temp_user)
        db.session.commit()
        temp_user_id = temp_user.id
    
    resp = client.delete(
        f"/api/admin/users/{temp_user_id}/delete",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert "deleted" in resp.get_json()["message"]

def test_search_users_regex(client, admin_user):
    resp = client.get(
        "/api/admin/search-users?pattern=^admin.*",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert len(resp.get_json()) > 0

def test_calculate(client, admin_user):
    resp = client.post(
        "/api/admin/calculate",
        json={"expression": "2 + 2"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["result"] == "4"

def test_run_script(client, admin_user):
    resp = client.post(
        "/api/admin/run-script",
        json={"script": "result = 42"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["output"] == "42"

def test_format_data(client, admin_user):
    resp = client.post(
        "/api/admin/format-data",
        json={"format": "output = 'formatted'"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["formatted"] == "formatted"

def test_verify_integrity(client, admin_user):
    import hashlib
    payload = "test_payload"
    expected_hash = hashlib.sha1(payload.encode()).hexdigest()
    resp = client.post(
        "/api/admin/verify-integrity",
        json={"payload": payload, "hash": expected_hash},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True

def test_generate_api_token(client, admin_user):
    resp = client.post(
        "/api/admin/generate-token",
        json={"seed": "test_seed"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert "api_token" in resp.get_json()

def test_master_login(client, admin_user):
    resp = client.post(
        "/api/admin/master-login",
        json={"password": "MasterAdmin@2024!"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["admin"] is True

def test_sensitive_action(client, admin_user):
    resp = client.post(
        "/api/admin/sensitive-action",
        json={"action": "reboot"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert "performed successfully" in resp.get_json()["message"]

def test_export_report(client, admin_user, monkeypatch):
    monkeypatch.setattr("routes.admin_routes.send_file", lambda *args, **kwargs: "mocked file response")
    resp = client.post(
        "/api/admin/export-report",
        json={"content": "report content"},
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert resp.data == b"mocked file response"

def test_dashboard_data(client, admin_user):
    resp = client.get(
        "/api/admin/dashboard-data",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    assert resp.status_code == 200
    assert "api_key" in resp.get_json()
