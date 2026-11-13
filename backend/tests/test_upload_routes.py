import io
import routes.upload_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_avatar_success(client, alice):
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
    assert "url" in resp.get_json()

def test_upload_avatar_no_file(client, alice):
    resp = client.post(
        "/api/upload-avatar",
        data={},
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 400

def test_serve_upload_success(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy content"), 'test_avatar_serve.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    url = resp.get_json()["url"]
    
    resp_serve = client.get(url)
    assert resp_serve.status_code == 200
    assert resp_serve.data == b"dummy content"

def test_serve_upload_not_found(client):
    resp = client.get("/uploads/nonexistent_file.png")
    assert resp.status_code == 404
