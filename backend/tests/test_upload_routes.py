import io

def test_upload_avatar(client, alice):
    data = {
        'file': (io.BytesIO(b"fake image content"), 'avatar.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        headers={"Authorization": f"Bearer {alice['token']}"},
        data=data,
        content_type='multipart/form-data'
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Avatar uploaded"
    assert "url" in resp.get_json()

def test_upload_avatar_no_file(client, alice):
    resp = client.post(
        "/api/upload-avatar",
        headers={"Authorization": f"Bearer {alice['token']}"},
        data={},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "No file provided"

def test_serve_upload(client, alice):
    data = {
        'file': (io.BytesIO(b"fake image content"), 'avatar.png')
    }
    resp_upload = client.post(
        "/api/upload-avatar",
        headers={"Authorization": f"Bearer {alice['token']}"},
        data=data,
        content_type='multipart/form-data'
    )
    url = resp_upload.get_json()["url"]
    
    resp_serve = client.get(url)
    assert resp_serve.status_code == 200
    assert resp_serve.data == b"fake image content"

def test_serve_upload_not_found(client):
    resp = client.get("/uploads/nonexistent.png")
    assert resp.status_code == 404
