import io
from routes import upload_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_avatar(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy avatar content"), 'test_avatar.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Avatar uploaded"
    assert resp.get_json()["url"] == "/uploads/test_avatar.png"

def test_serve_upload(client):
    resp = client.get("/uploads/test_avatar.png")
    assert resp.status_code == 200
    assert resp.data == b"dummy avatar content"
    assert resp.content_type == "image/png"

def test_serve_upload_not_found(client):
    resp = client.get("/uploads/nonexistent_file.png")
    assert resp.status_code == 404
