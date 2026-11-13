from routes import transaction_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_get_transactions(client, alice):
    resp = client.get(
        "/api/transactions",
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_quickpay(client, alice, bob):
    # Use Cookie header for cookie_auth
    headers = {
        "Cookie": f"session_token={alice['token']}"
    }
    resp = client.post(
        "/api/quickpay",
        json={
            "to_user_id": bob["user"]["id"],
            "amount": 10,
            "description": "Lunch"
        },
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "QuickPay sent"
    assert data["transaction"]["amount"] == 10.0

def test_split_bill(client, alice, bob):
    resp = client.post(
        "/api/split-bill",
        json={
            "from_user_id": bob["user"]["id"],
            "to_user_id": alice["user"]["id"],
            "amount": 5,
            "description": "Dinner split"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Bill split"
    assert data["transaction"]["amount"] == 5.0
