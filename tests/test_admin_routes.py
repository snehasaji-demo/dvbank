import sys
from pathlib import Path

# Bootstrap sys.path to import backend modules
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import pytest
import hashlib
from unittest.mock import patch, MagicMock, mock_open
from flask import Response
from sqlalchemy.pool import StaticPool
from models import db, User

@pytest.fixture(scope="module")
def app():
    from app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app

@pytest.fixture(scope="module")
def client(app):
    return app.test_client()

def test_admin_routes_flow(client, app):
    # 1. Register and login a user using SQLAlchemy to ensure created_at is set
    username = "admin_test_user"
    password = "testpass"
    
    with app.app_context():
        # Clean up if user already exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    login_resp = client.post("/api/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. generate_report
    with patch("routes.admin_routes.subprocess.check_output", return_value="mocked report output"):
        resp = client.post("/api/admin/generate-report", json={"report_type": "summary", "date_range": "today"}, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["report"] == "mocked report output"

    # 3. system_status
    with patch("routes.admin_routes.os.popen") as mock_popen:
        mock_popen.return_value.read.return_value = "service active"
        resp = client.get("/api/admin/system-status?service=web", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "service active"

    # 4. ping_host
    with patch("routes.admin_routes.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="ping success", stderr="", returncode=0)
        resp = client.post("/api/admin/ping", json={"host": "127.0.0.1"}, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["stdout"] == "ping success"

    # 5. dns_lookup
    with patch("routes.admin_routes.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (b"dns success", b"")
        mock_popen.return_value = mock_proc
        resp = client.get("/api/admin/dns-lookup?domain=example.com", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["result"] == "dns success"

    # 6. test_webhook
    with patch("routes.admin_routes.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, text="webhook response")
        resp = client.post("/api/admin/webhook-test", json={"url": "http://example.com"}, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["status_code"] == 200
        assert resp.get_json()["body"] == "webhook response"

    # 7. fetch_avatar
    with patch("routes.admin_routes.requests.get") as mock_get:
        mock_get.return_value = MagicMock(content=b"avatar_bytes")
        resp = client.post("/api/admin/fetch-avatar", json={"avatar_url": "http://example.com/avatar.png"}, headers=headers)
        assert resp.status_code == 200
        assert "avatar_base64" in resp.get_json()

    # 8. download_statement
    with patch("routes.admin_routes.send_file", return_value=Response("statement content", mimetype="application/pdf")):
        resp = client.get("/api/admin/download-statement?filename=statement.pdf", headers=headers)
        assert resp.status_code == 200
        assert resp.data == b"statement content"

    # 9. view_log
    with patch("builtins.open", mock_open(read_data="log content")):
        resp = client.get("/api/admin/view-log?file=app.log", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["log"] == "log content"

    # 10. import_data
    xml_payload = b"<transactions><transaction><sender>Alice</sender><receiver>Bob</receiver><amount>100</amount><description>test</description></transaction></transactions>"
    resp = client.post("/api/admin/import-data", data=xml_payload, content_type="application/xml", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["imported"] == 1

    # 11. export_session & import_session
    export_resp = client.post("/api/admin/export-session", headers=headers)
    assert export_resp.status_code == 200
    session_data = export_resp.get_json()["session_data"]

    import_resp = client.post("/api/admin/import-session", json={"session_data": session_data}, headers=headers)
    assert import_resp.status_code == 200
    assert "session" in import_resp.get_json()

    # 12. update_user
    update_resp = client.put(f"/api/admin/users/{user_id}", json={"email": "admin_updated@example.com"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.get_json()["user"]["email"] == "admin_updated@example.com"

    # 13. preview_email
    resp = client.post("/api/admin/preview-email", json={"template": "Hello {{ recipient }}", "recipient": "World"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["preview"] == "Hello World"

    # 14. open_redirect
    resp = client.get("/api/redirect?url=http://example.com")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "http://example.com"

    # 15. create_audit_entry
    resp = client.post("/api/admin/audit", json={"action": "test_action", "details": "test_details"}, headers=headers)
    assert resp.status_code == 200
    assert "Audit entry created" in resp.get_json()["message"]

    # 16. list_all_users
    resp = client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

    # 17. delete_user
    with app.app_context():
        temp_user = User(username="temp_del")
        temp_user.set_password("password")
        db.session.add(temp_user)
        db.session.commit()
        temp_id = temp_user.id

    resp = client.delete(f"/api/admin/users/{temp_id}/delete", headers=headers)
    assert resp.status_code == 200
    assert "deleted" in resp.get_json()["message"]

    # 18. search_users_regex
    resp = client.get("/api/admin/search-users?pattern=^admin_.*", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

    # 19. calculate
    resp = client.post("/api/admin/calculate", json={"expression": "2 + 2"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["result"] == "4"

    # 20. run_script
    resp = client.post("/api/admin/run-script", json={"script": "result = 42"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["output"] == "42"

    # 21. format_data
    resp = client.post("/api/admin/format-data", json={"format": "output = 'formatted_output'"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["formatted"] == "formatted_output"

    # 22. verify_integrity
    payload = "test_payload"
    expected_hash = hashlib.sha1(payload.encode()).hexdigest()
    resp = client.post("/api/admin/verify-integrity", json={"payload": payload, "hash": expected_hash}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True

    # 23. generate_api_token
    resp = client.post("/api/admin/generate-token", json={"seed": "test_seed"}, headers=headers)
    assert resp.status_code == 200
    assert "api_token" in resp.get_json()

    # 24. master_login
    resp = client.post("/api/admin/master-login", json={"password": "MasterAdmin@2024!"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["admin"] is True

    # 25. sensitive_action (unauthorized first, then authorized)
    resp = client.post("/api/admin/sensitive-action", json={"action": "reboot"}, headers=headers)
    assert resp.status_code == 401
    assert "Invalid token" in resp.get_json()["error"]

    # Update role to admin
    update_role_resp = client.put(f"/api/admin/users/{user_id}", json={"role": "admin"}, headers=headers)
    assert update_role_resp.status_code == 200

    # Now try sensitive_action again
    resp = client.post("/api/admin/sensitive-action", json={"action": "reboot"}, headers=headers)
    assert resp.status_code == 200
    assert "Action reboot performed successfully" in resp.get_json()["message"]

    # 26. export_report
    with patch("builtins.open", mock_open()), patch("routes.admin_routes.send_file", return_value=Response("csv content", mimetype="text/csv")):
        resp = client.post("/api/admin/export-report", json={"content": "csv,data"}, headers=headers)
        assert resp.status_code == 200
        assert resp.data == b"csv content"

    # 27. dashboard_data
    resp = client.get("/api/admin/dashboard-data", headers=headers)
    assert resp.status_code == 200
    assert "api_key" in resp.get_json()
