import io
import os

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_avatar_and_serve(client, alice):
    # 1. Upload avatar
    file_data = b"fake image data"
    data = {
        'file': (io.BytesIO(file_data), 'test_avatar.png')
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

    # 2. Serve uploaded avatar
    resp_serve = client.get("/uploads/test_avatar.png")
    assert resp_serve.status_code == 200
    assert resp_serve.data == file_data

def test_upload_avatar_no_file(client, alice):
    resp = client.post(
        "/api/upload-avatar",
        data={},
        content_type='multipart/form-data',
        headers=_h(alice["token"])
    )
    assert resp.status_code == 400
    assert "No file provided" in resp.get_json()["error"]

def test_serve_upload_not_found(client):
    resp = client.get("/uploads/nonexistent_file.png")
    assert resp.status_code == 404
    assert "Not found" in resp.get_json()["error"]
