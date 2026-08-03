def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_transfer_success(client, alice, bob):
    resp = client.post(
        "/api/transfer",
        json={"to_user_id": bob["user"]["id"], "amount": 50, "description": "pytest"},
        headers=_h(alice["token"]),
    )
    assert resp.status_code == 200
    assert "Transfer successful" in resp.get_json()["message"]


def test_transfer_insufficient_balance(client, alice, bob):
    resp = client.post(
        "/api/transfer",
        json={"to_user_id": bob["user"]["id"], "amount": 999999, "description": "too much"},
        headers=_h(alice["token"]),
    )
    assert resp.status_code == 400


def test_search_transactions(client, alice):
    resp = client.get(
        "/api/transactions/search?description=pytest",
        headers=_h(alice["token"]),
    )
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)
