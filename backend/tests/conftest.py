import subprocess
import sys
import os
import secrets

# Install dvbank's runtime deps into whichever Python is running pytest.
# G2 runs pytest via shell; the interpreter may differ from G1's pip environment.
_req = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
if os.path.exists(_req):
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", _req, "-q"],
        check=False,
    )

# Make backend/ importable so bare imports (models, auth, routes) resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy.pool import StaticPool

# Generate a random password for testing to avoid hardcoding
TEST_PASSWORD = secrets.token_urlsafe(16)


@pytest.fixture(scope="session")
def app():
    from app import app as flask_app
    from models import db

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


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def alice(client, app):
    from models import db, User

    client.post("/api/register", json={"username": "alice_t", "password": TEST_PASSWORD})
    user = User.query.filter_by(username="alice_t").first()
    if user:
        user.balance = 500
        db.session.commit()
    resp = client.post("/api/login", json={"username": "alice_t", "password": TEST_PASSWORD})
    return resp.get_json()


@pytest.fixture(scope="session")
def bob(client, app, alice):
    client.post("/api/register", json={"username": "bob_t", "password": TEST_PASSWORD})
    resp = client.post("/api/login", json={"username": "bob_t", "password": TEST_PASSWORD})
    return resp.get_json()
