import io
from routes import upload_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_avatar(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy content"), 'test_avatar.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert "Avatar uploaded" in resp.get_json()["message"]
    assert "test_avatar.png" in resp.get_json()["url"]

def test_serve_upload(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy content"), 'test_serve.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    
    resp_serve = client.get("/uploads/test_serve.png")
    assert resp_serve.status_code == 200
    assert resp_serve.data == b"dummy content"
