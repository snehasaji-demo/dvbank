import io
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

def test_upload_avatar(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy content"), 'test_avatar.png')
    }
    resp = client.post("/api/upload-avatar", data=data, content_type='multipart/form-data', headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Avatar uploaded"
    assert "url" in resp.get_json()

def test_serve_upload(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy content"), 'test_serve.png')
    }
    resp = client.post("/api/upload-avatar", data=data, content_type='multipart/form-data', headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    url = resp.get_json()["url"]

    resp2 = client.get(url)
    assert resp2.status_code == 200
    assert resp2.data == b"dummy content"
