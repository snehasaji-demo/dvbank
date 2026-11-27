def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_get_transactions(client, alice):
    resp = client.get("/api/transactions", headers=_h(alice["token"]))
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_quickpay(client, alice, bob):
    # Quickpay uses cookie_auth, which reads 'session_token' cookie
    client.set_cookie('session_token', alice["token"])
    resp = client.post(
        "/api/quickpay",
        json={
            "to_user_id": bob["user"]["id"],
            "amount": 10,
            "description": "QuickPay test"
        }
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "QuickPay sent"

def test_split_bill(client, alice, bob):
    resp = client.post(
        "/api/split-bill",
        json={
            "from_user_id": bob["user"]["id"],
            "to_user_id": alice["user"]["id"],
            "amount": 15,
            "description": "Split bill test"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Bill split"
