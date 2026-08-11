def test_register_success(client):
    resp = client.post("/api/register", json={"username": "carol_t", "password": "testpass"})
    assert resp.status_code == 201


def test_register_duplicate(client):
    client.post("/api/register", json={"username": "dup_t", "password": "testpass"})
    resp = client.post("/api/register", json={"username": "dup_t", "password": "testpass"})
    assert resp.status_code == 400


def test_login_returns_token(alice):
    assert "token" in alice
    assert alice["user"]["username"] == "alice_t"


def test_login_wrong_password(client):
    resp = client.post("/api/login", json={"username": "alice_t", "password": "wrong"})
    assert resp.status_code == 401


def test_me_authenticated(client, alice):
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {alice['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "alice_t"


def test_me_unauthenticated(client):
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_login_sql_injection(client):
    resp = client.post("/api/login", json={"username": "alice_t' OR '1'='1", "password": "any"})
    assert resp.status_code == 401


def test_register_sql_injection(client):
    resp = client.post("/api/register", json={"username": "malicious' OR '1'='1", "password": "any"})
    assert resp.status_code == 201
    resp_login = client.post("/api/login", json={"username": "malicious' OR '1'='1", "password": "any"})
    assert resp_login.status_code == 200
