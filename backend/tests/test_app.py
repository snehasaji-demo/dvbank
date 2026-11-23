from unittest.mock import MagicMock
import sqlite3
from app import set_sqlite_pragma, internal_error, not_found_error, init_db, app as global_app
from models import User, Transaction

def test_set_sqlite_pragma():
    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    set_sqlite_pragma(mock_conn, None)
    
    mock_conn.cursor.assert_called_once()
    calls = [c[0][0] for c in mock_cursor.execute.call_args_list]
    assert "PRAGMA journal_mode=WAL;" in calls
    assert "PRAGMA synchronous=NORMAL;" in calls
    assert "PRAGMA busy_timeout=10000;" in calls
    mock_cursor.close.assert_called_once()

def test_set_sqlite_pragma_non_sqlite():
    mock_conn = MagicMock()
    set_sqlite_pragma(mock_conn, None)
    mock_conn.cursor.assert_not_called()

def test_after_request_with_origin(client):
    resp = client.get("/api/me", headers={"Origin": "http://malicious.com"})
    assert resp.headers.get("Access-Control-Allow-Origin") == "http://malicious.com"
    assert resp.headers.get("Access-Control-Allow-Credentials") == "true"
    assert "Content-Security-Policy" in resp.headers

def test_after_request_without_origin(client):
    resp = client.get("/api/me")
    assert "Access-Control-Allow-Origin" not in resp.headers
    assert "Content-Security-Policy" in resp.headers

def test_not_found_error_direct():
    with global_app.app_context():
        resp, status_code = not_found_error(Exception("Not Found"))
        assert status_code == 404
        assert resp.get_json() == {"error": "Not Found"}

def test_internal_error_direct():
    with global_app.app_context():
        resp, status_code = internal_error(Exception("Test internal error"))
        assert status_code == 500
        assert resp.get_json() == {"error": "Test internal error"}

def test_init_db():
    global_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    init_db()
    with global_app.app_context():
        assert User.query.filter_by(username='alice').first() is not None
        assert Transaction.query.count() > 0
