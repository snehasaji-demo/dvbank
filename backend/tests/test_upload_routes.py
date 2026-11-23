import io
import os
from unittest.mock import patch

def test_upload_and_serve_avatar(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    
    # Test upload avatar
    data = {
        'file': (io.BytesIO(b"dummy avatar content"), 'test_avatar.png')
    }
    resp = client.post('/api/upload-avatar', data=data, content_type='multipart/form-data', headers=headers)
    assert resp.status_code == 200
    resp_data = resp.get_json()
    assert resp_data["message"] == "Avatar uploaded"
    assert "url" in resp_data
    
    # Test serve upload
    resp_serve = client.get(resp_data["url"])
    assert resp_serve.status_code == 200
    assert resp_serve.data == b"dummy avatar content"

def test_upload_avatar_no_file(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    resp = client.post('/api/upload-avatar', data={}, headers=headers)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "No file provided"

def test_serve_upload_not_found(client):
    resp = client.get('/uploads/nonexistent_file.png')
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Not found"
