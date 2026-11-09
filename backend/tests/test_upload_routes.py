import io
import pytest
from routes import upload_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_and_serve_avatar(client, alice):
    headers = _h(alice["token"])
    data = {
        'file': (io.BytesIO(b"my file content"), 'test_avatar.png')
    }
    resp = client.post("/api/upload-avatar", data=data, content_type='multipart/form-data', headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["url"] == "/uploads/test_avatar.png"

    resp = client.get("/uploads/test_avatar.png")
    assert resp.status_code == 200
    assert resp.data == b"my file content"
