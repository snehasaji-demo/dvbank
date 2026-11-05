import pytest
import io
import os

def test_upload_avatar_success(client, alice):
    data = {
        'file': (io.BytesIO(b"fake image content"), 'test_avatar.png')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 200
    res_json = resp.get_json()
    assert res_json["message"] == "Avatar uploaded"
    assert "url" in res_json

def test_upload_avatar_no_file(client, alice):
    resp = client.post(
        "/api/upload-avatar",
        data={},
        content_type='multipart/form-data',
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "No file provided"

def test_serve_upload_success(client, alice):
    # First upload a file
    data = {
        'file': (io.BytesIO(b"hello world"), 'hello.txt')
    }
    resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type='multipart/form-data',
        headers={"Authorization": f"Bearer {alice['token']}"}
    )
    assert resp.status_code == 200
    url = resp.get_json()["url"]
    
    # Now serve it
    resp_serve = client.get(url)
    assert resp_serve.status_code == 200
    assert resp_serve.data == b"hello world"
    assert resp_serve.content_type == "text/plain"

def test_serve_upload_not_found(client):
    resp = client.get("/uploads/nonexistent_file.png")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Not found"
