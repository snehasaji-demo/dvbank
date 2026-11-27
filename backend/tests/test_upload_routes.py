import io

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_upload_avatar(client, alice):
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
    assert resp.get_json()["message"] == "Avatar uploaded"
    assert "url" in resp.get_json()

def test_serve_upload(client, alice):
    # Upload first
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
    url = resp.get_json()["url"]

    # Now serve it
    resp_serve = client.get(url)
    assert resp_serve.status_code == 200
    assert resp_serve.data == b"fake image content"
