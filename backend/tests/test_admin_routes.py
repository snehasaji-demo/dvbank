from unittest.mock import patch, mock_open
import base64
import hashlib
from flask import Response
from datetime import datetime

def test_generate_report(client, alice):
    with patch("subprocess.check_output", return_value="mocked report output"):
        resp = client.post(
            "/api/admin/generate-report",
            headers={"Authorization": f"Bearer {alice['token']}"},
            json={"report_type": "summary", "date_range": "today"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["report"] == "mocked report output"

def test_system_status(client, alice):
    with patch("os.popen") as mock_popen:
        mock_popen.return_value.read.return_value = "mocked systemctl output"
        resp = client.get(
            "/api/admin/system-status?service=web",
            headers={"Authorization": f"Bearer {alice['token']}"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "mocked systemctl output"

def test_ping_host(client, alice):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "ping success"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0
        resp = client.post(
            "/api/admin/ping",
            headers={"Authorization": f"Bearer {alice['token']}"},
            json={"host": "127.0.0.1"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["stdout"] == "ping success"

def test_dns_lookup(client, alice):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.communicate.return_value = (b"dns result", b"")
        resp = client.get(
            "/api/admin/dns-lookup?domain=example.com",
            headers={"Authorization": f"Bearer {alice['token']}"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["result"] == "dns result"

def test_test_webhook(client, alice):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "webhook response"
        resp = client.post(
            "/api/admin/webhook-test",
            headers={"Authorization": f"Bearer {alice['token']}"},
            json={"url": "http://example.com"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["status_code"] == 200
        assert resp.get_json()["body"] == "webhook response"

def test_test_webhook_error(client, alice):
    with patch("requests.get", side_effect=Exception("connection error")):
        resp = client.post(
            "/api/admin/webhook-test",
            headers={"Authorization": f"Bearer {alice['token']}"},
            json={"url": "http://example.com"}
        )
        assert resp.status_code == 400
        assert "connection error" in resp.get_json()["error"]

def test_fetch_avatar(client, alice):
    with patch("requests.get") as mock_get:
        mock_get.return_value.content = b"avatar content"
        resp = client.post(
            "/api/admin/fetch-avatar",
            headers={"Authorization": f"Bearer {alice['token']}"},
            json={"avatar_url": "http://example.com/avatar.png"}
        )
        assert resp.status_code == 200
        assert "avatar_base64" in resp.get_json()

def test_download_statement(client, alice):
    with patch("routes.admin_routes.send_file") as mock_send_file:
        mock_send_file.return_value = Response("file content", mimetype="application/pdf")
        resp = client.get(
            "/api/admin/download-statement?filename=statement.pdf",
            headers={"Authorization": f"Bearer {alice['token']}"}
        )
        assert resp.status_code == 200
        assert resp.data == b"file content"

def test_view_log(client, alice):
    with patch("builtins.open", mock_open(read_data="log content")):
        resp = client.get(
            "/api/admin/view-log?file=app.log",
            headers={"Authorization": f"Bearer {alice['token']}"}
        )
        assert resp.status_code == 200
        assert resp.get_json()["log"] == "log content"

def test_import_data(client, alice):
    xml_payload = """<transactions>
        <transaction>
            <sender>alice</sender>
            <receiver>bob</receiver>
            <amount>100</amount>
            <description>test</description>
        </transaction>
    </transactions>"""
    resp = client.post(
        "/api/admin/import-data",
        headers={"Authorization": f"Bearer {alice['token']}", "Content-Type": "application/xml"},
        data=xml_payload
    )
    assert resp.status_code == 200
    assert resp.get_json()["imported"] == 1

def test_export_import_session(client, alice):
    resp_export = client.post(
        "/api/admin/export-session",
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp_export.status_code == 200
    session_data = resp_export.get_json()["session_data"]
    
    resp_import = client.post(
        "/api/admin/import-session",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"session_data": session_data}
    )
    assert resp_import.status_code == 200
    assert "session" in resp_import.get_json()

def test_update_user(client, alice):
    from models import db, User
    with client.application.app_context():
        user = User.query.get(alice['user']['id'])
        if user and user.created_at is None:
            user.created_at = datetime.utcnow()
            db.session.commit()

    resp = client.put(
        f"/api/admin/users/{alice['user']['id']}",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"email": "updated_admin@example.com"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "updated_admin@example.com"

def test_update_user_not_found(client, alice):
    resp = client.put(
        "/api/admin/users/99999",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"email": "updated_admin@example.com"}
    )
    assert resp.status_code == 404

def test_preview_email(client, alice):
    resp = client.post(
        "/api/admin/preview-email",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"template": "Hello {{ recipient }}", "recipient": "Alice"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["preview"] == "Hello Alice"

def test_open_redirect(client):
    resp = client.get("/api/redirect?url=http://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://example.com"

def test_create_audit_entry(client, alice):
    resp = client.post(
        "/api/admin/audit",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"action": "test_action", "details": "test_details"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Audit entry created"

def test_list_all_users(client, alice):
    resp = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 200
    assert len(resp.get_json()) >= 1

def test_delete_user(client, alice):
    client.post("/api/register", json={"username": "temp_user", "password": "password"})
    from models import User
    user = User.query.filter_by(username="temp_user").first()
    
    resp = client.delete(
        f"/api/admin/users/{user.id}/delete",
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 200
    assert "deleted" in resp.get_json()["message"]

def test_delete_user_not_found(client, alice):
    resp = client.delete(
        "/api/admin/users/99999/delete",
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 404

def test_search_users_regex(client, alice):
    from models import db, User
    with client.application.app_context():
        for user in User.query.all():
            if user.created_at is None:
                user.created_at = datetime.utcnow()
        db.session.commit()

    resp = client.get(
        "/api/admin/search-users?pattern=alice.*",
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 200
    assert len(resp.get_json()) >= 1

def test_calculate(client, alice):
    resp = client.post(
        "/api/admin/calculate",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"expression": "2 + 2"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["result"] == "4"

def test_calculate_error(client, alice):
    resp = client.post(
        "/api/admin/calculate",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"expression": "invalid"}
    )
    assert resp.status_code == 400

def test_run_script(client, alice):
    resp = client.post(
        "/api/admin/run-script",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"script": "result = 42"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["output"] == "42"

def test_format_data(client, alice):
    resp = client.post(
        "/api/admin/format-data",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"format": "output = 'formatted'"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["formatted"] == "formatted"

def test_verify_integrity(client, alice):
    payload = "test_payload"
    expected_hash = hashlib.sha1(payload.encode()).hexdigest()
    resp = client.post(
        "/api/admin/verify-integrity",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"payload": payload, "hash": expected_hash}
    )
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True

def test_generate_api_token(client, alice):
    resp = client.post(
        "/api/admin/generate-token",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"seed": "test_seed"}
    )
    assert resp.status_code == 200
    assert "api_token" in resp.get_json()

def test_master_login(client, alice):
    resp = client.post(
        "/api/admin/master-login",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"password": "MasterAdmin@2024!"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["admin"] is True

def test_master_login_wrong(client, alice):
    resp = client.post(
        "/api/admin/master-login",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"password": "wrong"}
    )
    assert resp.status_code == 403

def test_sensitive_action(client, alice):
    from models import db, User
    with client.application.app_context():
        user = User.query.filter_by(username="alice_t").first()
        user.role = "admin"
        db.session.commit()
        
    resp = client.post(
        "/api/admin/sensitive-action",
        headers={"Authorization": f"Bearer {alice['token']}"},
        json={"action": "test_action"}
    )
    assert resp.status_code == 200
    assert "performed successfully" in resp.get_json()["message"]

def test_export_report(client, alice):
    with patch("routes.admin_routes.send_file") as mock_send_file:
        mock_send_file.return_value = Response("csv content", mimetype="text/csv")
        resp = client.post(
            "/api/admin/export-report",
            headers={"Authorization": f"Bearer {alice['token']}"},
            json={"content": "col1,col2\nval1,val2"}
        )
        assert resp.status_code == 200
        assert resp.data == b"csv content"

def test_dashboard_data(client, alice):
    resp = client.get(
        "/api/admin/dashboard-data",
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 200
    assert "api_key" in resp.get_json()
