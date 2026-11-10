import io
import backend.routes.upload_routes
from backend.routes.upload_routes import upload_avatar, serve_upload

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_avatar(client, alice):
    assert upload_avatar is not None
    data = {
        'file': (io.BytesIO(b"my file content"), 'test_avatar.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Avatar uploaded"
    assert "url" in resp.get_json()

def test_serve_upload(client, alice):
    assert serve_upload is not None
    # First upload a file
    data = {
        'file': (io.BytesIO(b"my file content"), 'test_avatar.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    url = resp.get_json()["url"]
    
    # Now serve it
    resp_serve = client.get(url)
    assert resp_serve.status_code == 200
    assert resp_serve.data == b"my file content"
