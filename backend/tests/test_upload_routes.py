import io
import backend.routes.upload_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_avatar_success(client, alice):
    data = {
        'file': (io.BytesIO(b"fake image content"), 'test_avatar.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert "Avatar uploaded" in resp.get_json()["message"]
    assert resp.get_json()["url"] == "/uploads/test_avatar.png"

def test_upload_avatar_no_file(client, alice):
    resp = client.post(
        "/api/upload-avatar",
        data={},
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 400
    assert "No file provided" in resp.get_json()["error"]

def test_serve_upload_success(client, alice):
    data = {
        'file': (io.BytesIO(b"fake image content"), 'test_serve.png')
    }
    client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    
    resp = client.get("/uploads/test_serve.png")
    assert resp.status_code == 200
    assert resp.data == b"fake image content"
    assert resp.content_type == "image/png"

def test_serve_upload_not_found(client):
    resp = client.get("/uploads/nonexistent_file.png")
    assert resp.status_code == 404
