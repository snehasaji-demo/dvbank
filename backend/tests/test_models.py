from models import User, LoginAttempt, db
import pytest
from datetime import datetime

def test_user_password():
    user = User()
    user.set_password("my_secure_password")
    assert user.password_hash is not None
    assert user.check_password("my_secure_password") is True
    assert user.check_password("wrong_password") is False

def test_user_profile():
    user = User()
    assert user.get_profile() == {}
    
    profile_data = {"fullName": "Alice Johnson", "phone": "+1-555-0123"}
    user.set_profile(profile_data)
    assert user.get_profile() == profile_data

def test_user_to_dict(app):
    with app.app_context():
        user = User(
            username="test_user",
            email="test@example.com",
            balance=100.50,
            role="user",
            created_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        d = user.to_dict()
        assert d["username"] == "test_user"
        assert d["email"] == "test@example.com"
        assert d["balance"] == 100.50
        assert d["role"] == "user"
        assert d["created_at"] == "2023-01-01T12:00:00"
        assert d["last_login"] is None

def test_login_attempt(app):
    with app.app_context():
        attempt = LoginAttempt(
            username="test_user",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            success=True
        )
        assert attempt.username == "test_user"
        assert attempt.ip_address == "127.0.0.1"
        assert attempt.user_agent == "Mozilla/5.0"
        assert attempt.success is True
