import backend.routes.transaction_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_get_transactions(client, alice):
    resp = client.get("/api/transactions", headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_quickpay(client, alice, bob):
    client.set_cookie('session_token', alice["token"])
    resp = client.post(
        "/api/quickpay",
        json={"to_user_id": bob["user"]["id"], "amount": 10, "description": "QP test"}
    )
    assert resp.status_code == 200
    assert "QuickPay sent" in resp.get_json()["message"]

def test_split_bill(client, alice, bob):
    resp = client.post(
        "/api/split-bill",
        json={
            "from_user_id": bob["user"]["id"],
            "to_user_id": alice["user"]["id"],
            "amount": 15,
            "description": "Split test"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert "Bill split" in resp.get_json()["message"]
