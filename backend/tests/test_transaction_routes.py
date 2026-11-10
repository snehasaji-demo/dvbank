from decimal import Decimal
import backend.routes.transaction_routes
from backend.routes.transaction_routes import get_transactions, quickpay, split_bill

def _h(token):
    return {"Authorization": f"Bearer {token}"}

def test_get_transactions(client, alice):
    assert get_transactions is not None
    resp = client.get(
        "/api/transactions",
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_quickpay(client, alice, bob):
    assert quickpay is not None
    client.set_cookie('session_token', alice['token'])
    resp = client.post(
        "/api/quickpay",
        json={"to_user_id": bob["user"]["id"], "amount": 10, "description": "QP"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "QuickPay sent"

def test_split_bill(client, alice, bob):
    assert split_bill is not None
    resp = client.post(
        "/api/split-bill",
        json={"from_user_id": bob["user"]["id"], "to_user_id": alice["user"]["id"], "amount": 15},
        headers=_h(alice["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Bill split"
