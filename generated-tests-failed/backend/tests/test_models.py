import pytest
import sqlite3
import jwt
from unittest.mock import MagicMock
from models import User, Transaction, LoginAttempt, AuditLog, db
from datetime import datetime
from decimal import Decimal
from app import set_sqlite_pragma, after_request, not_found_error, internal_error, init_db
from auth import token_required, cookie_auth
from flask import jsonify, Response

def test_user_password(app):
    with app.app_context():
        user = User(username="test_user")
        user.set_password("my_secure_password")
        assert user.password_hash is not None
        assert user.check_password("my_secure_password") is True
        assert user.check_password("wrong_password") is False

def test_user_profile(app):
    with app.app_context():
        user = User(username="test_user")
        assert user.get_profile() == {}
        
        profile_data = {"theme": "dark", "notifications": True}
        user.set_profile(profile_data)
        assert user.get_profile() == profile_data

def test_user_to_dict(app):
    with app.app_context():
        user = User(
            id=123,
            username="test_user",
            email="test@example.com",
            balance=Decimal("100.50"),
            role="user",
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            last_login=datetime(2023, 1, 2, 12, 0, 0)
        )
        d = user.to_dict()
        assert d["id"] == 123
        assert d["username"] == "test_user"
        assert d["email"] == "test@example.com"
        assert d["balance"] == 100.50
        assert d["role"] == "user"
        assert d["created_at"] == "2023-01-01T12:00:00"
        assert d["last_login"] == "2023-01-02T12:00:00"

def test_transaction_to_dict(app):
    with app.app_context():
        tx = Transaction(
            id=456,
            sender_id=1,
            receiver_id=2,
            amount=Decimal("50.00"),
            description="Test transfer",
            status="completed",
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            completed_at=datetime(2023, 1, 1, 12, 5, 0)
        )
        d = tx.to_dict()
        assert d["id"] == 456
        assert d["sender_id"] == 1
        assert d["receiver_id"] == 2
        assert d["amount"] == 50.00
        assert d["description"] == "Test transfer"
        assert d["status"] == "completed"
        assert d["created_at"] == "2023-01-01T12:00:00"
        assert d["completed_at"] == "2023-01-01T12:05:00"

def test_login_attempt_creation(app):
    with app.app_context():
        attempt = LoginAttempt(
            id=789,
            user_id=1,
            username="test_user",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            success=True,
            created_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        assert attempt.id == 789
        assert attempt.user_id == 1
        assert attempt.username == "test_user"
        assert attempt.ip_address == "127.0.0.1"
        assert attempt.user_agent == "Mozilla/5.0"
        assert attempt.success is True
        assert attempt.created_at == datetime(2023, 1, 1, 12, 0, 0)

def test_audit_log_to_dict(app):
    with app.app_context():
        log = AuditLog(
            id=999,
            user_id=1,
            action="login",
            details='{"status": "success"}',
            ip_address="127.0.0.1",
            created_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        d = log.to_dict()
        assert d["id"] == 999
        assert d["user_id"] == 1
        assert d["action"] == "login"
        assert d["details"] == {"status": "success"}
        assert d["ip_address"] == "127.0.0.1"
        assert d["created_at"] == "2023-01-01T12:00:00"

def test_set_sqlite_pragma():
    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    set_sqlite_pragma(mock_conn, None)
    assert mock_cursor.execute.call_count == 3

def test_after_request(client):
    resp = Response()
    after_request(resp)
    assert resp is not None

def test_not_found_error(client):
    resp, status = not_found_error(Exception("not found"))
    assert status == 404

def test_internal_error(app):
    with app.app_context():
        resp, status = internal_error(Exception("test error"))
        assert status == 500
        assert resp.get_json() == {"error": "test error"}

def test_init_db(app):
    with app.app_context():
        init_db()
        alice = User.query.filter_by(username="alice").first()
        assert alice is not None
        assert alice.email == "alice@bank.com"

def test_token_required(app):
    @app.route("/test-token")
    @token_required
    def dummy_token_route(current_user):
        return jsonify({"username": current_user.username})

    client = app.test_client()

    # 1. Missing token
    resp = client.get("/test-token")
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Token is missing"}

    # 2. Invalid token
    resp = client.get("/test-token", headers={"Authorization": "Bearer invalid_token"})
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Invalid token"}

    # 3. Valid token
    with app.app_context():
        user = User.query.filter_by(username="alice").first()
        if not user:
            user = User(username="alice", email="alice@bank.com")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
        
        token = jwt.encode({"user_id": user.id}, "secret", algorithm="HS256")
    
    resp = client.get("/test-token", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json() == {"username": "alice"}

    # 4. None algorithm token bypass
    token_none = jwt.encode({"user_id": user.id}, "", algorithm="none")
    resp = client.get("/test-token", headers={"Authorization": f"Bearer {token_none}"})
    assert resp.status_code == 200
    assert resp.get_json() == {"username": "alice"}

def test_cookie_auth(app):
    @app.route("/test-cookie")
    @cookie_auth
    def dummy_cookie_route(current_user):
        return jsonify({"username": current_user.username})

    client = app.test_client()

    # 1. Missing cookie
    resp = client.get("/test-cookie")
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Not authenticated"}

    # 2. Invalid cookie
    client.set_cookie("session_token", "invalid_token")
    resp = client.get("/test-cookie")
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Invalid session"}

    # 3. Valid cookie
    with app.app_context():
        user = User.query.filter_by(username="alice").first()
    
    token = jwt.encode({"user_id": user.id}, "secret", algorithm="HS256")
    client.set_cookie("session_token", token)
    resp = client.get("/test-cookie")
    assert resp.status_code == 200
    assert resp.get_json() == {"username": "alice"}
