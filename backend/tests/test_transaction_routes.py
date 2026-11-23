def test_get_transactions(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    resp = client.get("/api/transactions", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_quickpay(client, alice, bob):
    headers = {"Cookie": f"session_token={alice['token']}"}
    to_user_id = bob["user"]["id"]
    
    resp = client.post("/api/quickpay", json={
        "to_user_id": to_user_id,
        "amount": 50,
        "description": "Lunch"
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "QuickPay sent"
    assert data["transaction"]["amount"] == 50.0

def test_quickpay_receiver_not_found(client, alice):
    headers = {"Cookie": f"session_token={alice['token']}"}
    resp = client.post("/api/quickpay", json={
        "to_user_id": 99999,
        "amount": 50
    }, headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Receiver not found"

def test_split_bill(client, alice, bob):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    from_user_id = bob["user"]["id"]
    to_user_id = alice["user"]["id"]
    
    resp = client.post("/api/split-bill", json={
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        "amount": 25,
        "description": "Dinner split"
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Bill split"
    assert data["transaction"]["amount"] == 25.0

def test_split_bill_user_not_found(client, alice):
    headers = {"Authorization": f"Bearer {alice['token']}"}
    resp = client.post("/api/split-bill", json={
        "from_user_id": 99999,
        "to_user_id": alice["user"]["id"],
        "amount": 25
    }, headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "User not found"
