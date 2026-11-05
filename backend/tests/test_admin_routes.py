import pytest
from unittest.mock import patch, MagicMock
from flask import Response
from datetime import datetime

@pytest.fixture(autouse=True)
def ensure_created_at(app):
    from models import db, User
    with app.app_context():
        for user in User.query.all():
            if user.created_at is None:
                user.created_at = datetime.utcnow()
        db.session.commit()

def test_generate_report(client, alice):
    with patch("routes.admin_routes.subprocess.check_output", return_value="mocked report"):
        resp = client.post("/api/admin/generate-report", json={"report_type": "summary", "date_range": "today"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["report"] == "mocked report"

def test_system_status(client, alice):
    class MockPopen:
        def read(self):
            return "mocked status"
    with patch("routes.admin_routes.os.popen", return_value=MockPopen()):
        resp = client.get("/api/admin/system-status?service=web", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "mocked status"

def test_ping_host(client, alice):
    class MockCompletedProcess:
        stdout = "ping success"
        stderr = ""
        returncode = 0
    with patch("routes.admin_routes.subprocess.run", return_value=MockCompletedProcess()):
        resp = client.post("/api/admin/ping", json={"host": "127.0.0.1"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["stdout"] == "ping success"

def test_dns_lookup(client, alice):
    class MockProcess:
        def communicate(self):
            return (b"dns success", b"")
    with patch("routes.admin_routes.subprocess.Popen", return_value=MockProcess()):
        resp = client.get("/api/admin/dns-lookup?domain=google.com", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["result"] == "dns success"

def test_webhook(client, alice):
    class MockResponse:
        status_code = 200
        text = "webhook success"
    with patch("routes.admin_routes.requests.get", return_value=MockResponse()):
        resp = client.post("/api/admin/webhook-test", json={"url": "http://example.com"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["status_code"] == 200
        assert resp.get_json()["body"] == "webhook success"

def test_webhook_exception(client, alice):
    with patch("routes.admin_routes.requests.get", side_effect=Exception("connection error")):
        resp = client.post("/api/admin/webhook-test", json={"url": "http://example.com"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 400
        assert "connection error" in resp.get_json()["error"]

def test_fetch_avatar(client, alice):
    class MockResponse:
        content = b"avatar_data"
    with patch("routes.admin_routes.requests.get", return_value=MockResponse()):
        resp = client.post("/api/admin/fetch-avatar", json={"avatar_url": "http://example.com/avatar.png"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert "avatar_base64" in resp.get_json()

def test_download_statement(client, alice):
    with patch("routes.admin_routes.send_file", return_value=Response("file_sent", 200)):
        resp = client.get("/api/admin/download-statement?filename=statement.pdf", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.data == b"file_sent"

def test_view_log(client, alice):
    from unittest.mock import mock_open
    with patch("routes.admin_routes.open", mock_open(read_data="log content")):
        resp = client.get("/api/admin/view-log?file=app.log", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["log"] == "log content"

def test_import_data(client, alice):
    xml_data = "<transactions><transaction><sender>Alice</sender><receiver>Bob</receiver><amount>100</amount><description>test</description></transaction></transactions>"
    resp = client.post("/api/admin/import-data", data=xml_data, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["imported"] == 1

def test_import_export_session(client, alice):
    resp = client.post("/api/admin/export-session", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    session_data = resp.get_json()["session_data"]
    
    resp2 = client.post("/api/admin/import-session", json={"session_data": session_data}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp2.status_code == 200
    assert "session" in resp2.get_json()

def test_update_user(client, alice):
    payload = {"email": "updated_by_admin@example.com"}
    resp = client.put(f"/api/admin/users/{alice['user']['id']}", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "User updated"

def test_update_user_not_found(client, alice):
    payload = {"email": "updated_by_admin@example.com"}
    resp = client.put("/api/admin/users/99999", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 404

def test_preview_email(client, alice):
    payload = {"template": "Hello {{ recipient }}", "recipient": "Bob"}
    resp = client.post("/api/admin/preview-email", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["preview"] == "Hello Bob"

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=http://example.com")
    assert resp.status_code in (301, 302, 303, 307, 308)
    assert resp.headers["Location"] == "http://example.com"

def test_create_audit_entry(client, alice):
    payload = {"action": "test_action", "details": "test_details"}
    resp = client.post("/api/admin/audit", json=payload, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Audit entry created"

def test_list_all_users(client, alice):
    resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    users = resp.get_json()
    assert len(users) > 0

def test_delete_user(client, alice):
    client.post("/api/register", json={"username": "to_delete", "password": "password"})
    from models import User
    user = User.query.filter_by(username="to_delete").first()
    assert user is not None
    
    resp = client.delete(f"/api/admin/users/{user.id}/delete", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert "deleted" in resp.get_json()["message"]

def test_delete_user_not_found(client, alice):
    resp = client.delete("/api/admin/users/99999/delete", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 404

def test_search_users_regex(client, alice):
    resp = client.get("/api/admin/search-users?pattern=alice.*", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    matches = resp.get_json()
    assert len(matches) > 0

def test_calculate(client, alice):
    resp = client.post("/api/admin/calculate", json={"expression": "2 + 2"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == "4"

def test_calculate_error(client, alice):
    resp = client.post("/api/admin/calculate", json={"expression": "invalid"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 400

def test_run_script(client, alice):
    resp = client.post("/api/admin/run-script", json={"script": "result = 42"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["output"] == "42"

def test_format_data(client, alice):
    resp = client.post("/api/admin/format-data", json={"format": "output = 'formatted'"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["formatted"] == "formatted"

def test_verify_integrity(client, alice):
    import hashlib
    payload = "test_payload"
    expected_hash = hashlib.sha1(payload.encode()).hexdigest()
    resp = client.post("/api/admin/verify-integrity", json={"payload": payload, "hash": expected_hash}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True

def test_generate_api_token(client, alice):
    resp = client.post("/api/admin/generate-token", json={"seed": "test_seed"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert "api_token" in resp.get_json()

def test_master_login(client, alice):
    resp = client.post("/api/admin/master-login", json={"password": "MasterAdmin@2024!"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["admin"] is True

def test_master_login_invalid(client, alice):
    resp = client.post("/api/admin/master-login", json={"password": "wrong"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 403

def test_sensitive_action(client, alice, app):
    from models import db, User
    try:
        with app.app_context():
            user = User.query.filter_by(username="alice_t").first()
            user.role = "admin"
            db.session.commit()
            
        resp = client.post("/api/admin/sensitive-action", json={"action": "delete_all"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert "performed successfully" in resp.get_json()["message"]
    finally:
        with app.app_context():
            user = User.query.filter_by(username="alice_t").first()
            user.role = "user"
            db.session.commit()

def test_export_report(client, alice):
    from unittest.mock import mock_open
    with patch("routes.admin_routes.open", mock_open()):
        with patch("routes.admin_routes.send_file", return_value=Response("csv_data", 200)):
            resp = client.post("/api/admin/export-report", json={"content": "col1,col2\nval1,val2"}, headers={"Authorization": f"Bearer {alice['token']}"})
            assert resp.status_code == 200
            assert resp.data == b"csv_data"

def test_dashboard_data(client, alice):
    resp = client.get("/api/admin/dashboard-data", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "users" in data
    assert "transactions" in data
    assert "api_key" in data
