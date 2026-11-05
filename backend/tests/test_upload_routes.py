import io
import pytest

def test_upload_routes_flow(client):
    # 1. Register and login a user
    username = "upload_user"
    password = "testpass"
    client.post("/api/register", json={"username": username, "password": password})
    login_resp = client.post("/api/login", json={"username": username, "password": password})
    token = login_resp.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test upload with no file provided
    resp_no_file = client.post(
        "/api/upload-avatar",
        data={},
        content_type="multipart/form-data",
        headers=headers
    )
    assert resp_no_file.status_code == 400
    assert "No file provided" in resp_no_file.get_json()["error"]

    # 3. Test successful file upload
    file_content = b"fake image data"
    file_name = "test_avatar.png"
    data = {
        "file": (io.BytesIO(file_content), file_name)
    }
    upload_resp = client.post(
        "/api/upload-avatar",
        data=data,
        content_type="multipart/form-data",
        headers=headers
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.get_json()
    assert "Avatar uploaded" in upload_data["message"]
    assert "url" in upload_data
    uploaded_url = upload_data["url"]

    # 4. Test serving the uploaded file
    serve_resp = client.get(uploaded_url)
    assert serve_resp.status_code == 200
    assert serve_resp.data == file_content
    assert serve_resp.content_type == "image/png"

    # 5. Test serving a non-existent file
    non_existent_resp = client.get("/uploads/does_not_exist.png")
    assert non_existent_resp.status_code == 404
    assert "Not found" in non_existent_resp.get_json()["error"]
