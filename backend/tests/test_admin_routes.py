from unittest.mock import patch, mock_open
import hashlib
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

def test_generate_report(client, alice):
    with patch('routes.admin_routes.subprocess.check_output') as mock_sub:
        mock_sub.return_value = "mocked report content"
        resp = client.post("/api/admin/generate-report", json={"report_type": "summary", "date_range": "today"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["report"] == "mocked report content"

def test_system_status(client, alice):
    with patch('routes.admin_routes.os.popen') as mock_popen:
        mock_popen.return_value.read.return_value = "mocked status"
        resp = client.get("/api/admin/system-status?service=web", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "mocked status"

def test_ping_host(client, alice):
    with patch('routes.admin_routes.subprocess.run') as mock_run:
        mock_run.return_value.stdout = "mocked ping"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0
        resp = client.post("/api/admin/ping", json={"host": "127.0.0.1"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["stdout"] == "mocked ping"

def test_dns_lookup(client, alice):
    with patch('routes.admin_routes.subprocess.Popen') as mock_popen:
        mock_popen.return_value.communicate.return_value = (b"mocked dns", b"")
        resp = client.get("/api/admin/dns-lookup?domain=google.com", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["result"] == "mocked dns"

def test_webhook(client, alice):
    with patch('routes.admin_routes.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "mocked webhook response"
        resp = client.post("/api/admin/webhook-test", json={"url": "http://example.com"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["status_code"] == 200
        assert resp.get_json()["body"] == "mocked webhook response"

def test_fetch_avatar(client, alice):
    with patch('routes.admin_routes.requests.get') as mock_get:
        mock_get.return_value.content = b"avatar_data"
        resp = client.post("/api/admin/fetch-avatar", json={"avatar_url": "http://example.com/avatar.png"}, headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert "avatar_base64" in resp.get_json()

def test_download_statement(client, alice):
    with patch('routes.admin_routes.send_file') as mock_send:
        mock_send.return_value = "file_content"
        resp = client.get("/api/admin/download-statement?filename=statement.pdf", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.data == b"file_content"

def test_view_log(client, alice):
    with patch('builtins.open', mock_open(read_data="mocked log content")):
        resp = client.get("/api/admin/view-log?file=app.log", headers={"Authorization": f"Bearer {alice['token']}"})
        assert resp.status_code == 200
        assert resp.get_json()["log"] == "mocked log content"

def test_import_data(client, alice):
    xml_data = """<transactions>
        <transaction>
            <sender>alice</sender>
            <receiver>bob</receiver>
            <amount>100</amount>
            <description>test</description>
        </transaction>
    </transactions>"""
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
    resp = client.put(f"/api/admin/users/{alice['user']['id']}", json={"email": "new_alice@example.com"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "new_alice@example.com"

def test_preview_email(client, alice):
    resp = client.post("/api/admin/preview-email", json={"template": "Hello {{ recipient }}", "recipient": "Alice"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["preview"] == "Hello Alice"

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=http://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://example.com"

def test_create_audit_entry(client, alice):
    resp = client.post("/api/admin/audit", json={"action": "test_action", "details": "test_details"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Audit entry created"

def test_list_all_users(client, alice):
    resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert len(resp.get_json()) > 0

def test_delete_user(client, alice):
    resp_reg = client.post("/api/register", json={"username": "temp_user", "password": "password"})
    assert resp_reg.status_code == 201
    user_id = resp_reg.get_json()["id"]

    resp = client.delete(f"/api/admin/users/{user_id}/delete", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert "deleted" in resp.get_json()["message"]

def test_search_users_regex(client, alice):
    resp = client.get("/api/admin/search-users?pattern=alice.*", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert len(resp.get_json()) > 0

def test_calculate(client, alice):
    resp = client.post("/api/admin/calculate", json={"expression": "2 + 2"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == "4"

def test_run_script(client, alice):
    resp = client.post("/api/admin/run-script", json={"script": "result = 42"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["output"] == "42"

def test_format_data(client, alice):
    resp = client.post("/api/admin/format-data", json={"format": "output = 'formatted'"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["formatted"] == "formatted"

def test_verify_integrity(client, alice):
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

def test_sensitive_action(client, alice):
    resp = client.post("/api/admin/sensitive-action", json={"action": "do_something"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 401

    resp_up = client.put(f"/api/admin/users/{alice['user']['id']}", json={"role": "admin"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp_up.status_code == 200

    resp_sens = client.post("/api/admin/sensitive-action", json={"action": "do_something"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp_sens.status_code == 200
    assert "successfully" in resp_sens.get_json()["message"]

    resp_reset = client.put(f"/api/admin/users/{alice['user']['id']}", json={"role": "user"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp_reset.status_code == 200

def test_export_report(client, alice):
    resp = client.post("/api/admin/export-report", json={"content": "report_content"}, headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.data == b"report_content"

def test_dashboard_data(client, alice):
    resp = client.get("/api/admin/dashboard-data", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert "api_key" in resp.get_json()
