import pytest
import io

def test_upload_avatar_no_file(client, alice):
    resp = client.post("/api/upload-avatar", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "No file provided"

def test_upload_avatar_success(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy image content"), 'avatar.png')
    }
    resp = client.post("/api/upload-avatar", data=data, content_type='multipart/form-data', headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Avatar uploaded"
    assert "url" in resp.get_json()

def test_serve_upload_success(client, alice):
    data = {
        'file': (io.BytesIO(b"dummy image content"), 'avatar.png')
    }
    resp = client.post("/api/upload-avatar", data=data, content_type='multipart/form-data', headers={"Authorization": f"Bearer {alice['token']}"})
    url = resp.get_json()["url"]
    
    resp2 = client.get(url)
    assert resp2.status_code == 200
    assert resp2.data == b"dummy image content"

def test_serve_upload_not_found(client):
    resp = client.get("/uploads/non_existent.png")
    assert resp.status_code == 404
