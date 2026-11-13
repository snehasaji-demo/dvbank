import routes.transaction_routes

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_get_transactions(client, alice):
    resp = client.get(
        "/api/transactions",
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_quickpay_success(client, alice, bob):
    client.set_cookie('localhost', 'session_token', alice['token'])
    resp = client.post(
        "/api/quickpay",
        json={
            "to_user_id": bob["user"]["id"],
            "amount": 50,
            "description": "QuickPay test"
        }
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "QuickPay sent"

def test_quickpay_receiver_not_found(client, alice):
    client.set_cookie('localhost', 'session_token', alice['token'])
    resp = client.post(
        "/api/quickpay",
        json={
            "to_user_id": 999999,
            "amount": 50,
            "description": "QuickPay test"
        }
    )
    assert resp.status_code == 404

def test_split_bill_success(client, alice, bob):
    resp = client.post(
        "/api/split-bill",
        json={
            "from_user_id": bob["user"]["id"],
            "to_user_id": alice["user"]["id"],
            "amount": 30,
            "description": "Split bill test"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Bill split"

def test_split_bill_user_not_found(client, alice):
    resp = client.post(
        "/api/split-bill",
        json={
            "from_user_id": 999999,
            "to_user_id": alice["user"]["id"],
            "amount": 30,
            "description": "Split bill test"
        },
        headers=_h(alice["token"])
    )
    assert resp.status_code == 404
