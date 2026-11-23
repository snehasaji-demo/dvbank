from auth import token_required, cookie_auth
from models import User
import jwt

def test_token_required_missing_token(app):
    @token_required
    def dummy_view(current_user):
        return "success"

    with app.test_request_context(headers={}):
        resp, status_code = dummy_view()
        assert status_code == 401
        assert resp.get_json() == {'error': 'Token is missing'}

def test_token_required_invalid_token(app):
    @token_required
    def dummy_view(current_user):
        return "success"

    with app.test_request_context(headers={"Authorization": "Bearer invalid_token"}):
        resp, status_code = dummy_view()
        assert status_code == 401
        assert resp.get_json() == {'error': 'Invalid token'}

def test_token_required_user_not_found(app):
    @token_required
    def dummy_view(current_user):
        return "success"

    token = jwt.encode({"user_id": 99999}, 'secret', algorithm='HS256')
    with app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
        resp, status_code = dummy_view()
        assert status_code == 401
        assert resp.get_json() == {'error': 'Invalid token'}

def test_token_required_success(app):
    from models import db, User
    with app.app_context():
        user = User.query.filter_by(username="token_user").first()
        if not user:
            user = User(username="token_user", email="token@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
        
        token = jwt.encode({"user_id": user.id}, 'secret', algorithm='HS256')
        
        @token_required
        def dummy_view(current_user):
            return f"success: {current_user.username}"

        with app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
            res = dummy_view()
            assert res == f"success: token_user"

def test_token_required_none_algorithm(app):
    from models import db, User
    with app.app_context():
        user = User.query.filter_by(username="token_user").first()
        if not user:
            user = User(username="token_user", email="token@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
        
        token = jwt.encode({"user_id": user.id}, key="", algorithm="none")
        
        @token_required
        def dummy_view(current_user):
            return f"success: {current_user.username}"

        with app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
            res = dummy_view()
            assert res == f"success: token_user"

def test_cookie_auth_missing_cookie(app):
    @cookie_auth
    def dummy_view(current_user):
        return "success"

    with app.test_request_context():
        resp, status_code = dummy_view()
        assert status_code == 401
        assert resp.get_json() == {'error': 'Not authenticated'}

def test_cookie_auth_invalid_cookie(app):
    @cookie_auth
    def dummy_view(current_user):
        return "success"

    with app.test_request_context(headers={"Cookie": "session_token=invalid_token"}):
        resp, status_code = dummy_view()
        assert status_code == 401
        assert resp.get_json() == {'error': 'Invalid session'}

def test_cookie_auth_success(app):
    from models import db, User
    with app.app_context():
        user = User.query.filter_by(username="token_user").first()
        if not user:
            user = User(username="token_user", email="token@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
        
        token = jwt.encode({"user_id": user.id}, 'secret', algorithm='HS256')
        
        @cookie_auth
        def dummy_view(current_user):
            return f"success: {current_user.username}"

        with app.test_request_context(headers={"Cookie": f"session_token={token}"}):
            res = dummy_view()
            assert res == f"success: token_user"
