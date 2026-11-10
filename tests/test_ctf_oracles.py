import os
import json
import base64
import pytest
from unittest.mock import patch, MagicMock
from eval.graders.ctf_oracles import (
    forge_none_token,
    setup,
    teardown,
    _register,
    _login,
    _auth,
    _admin_users,
    _user_balance,
    _user_id
)

def test_forge_none_token():
    token = forge_none_token(123, "alice")
    parts = token.split(".")
    assert len(parts) == 3
    assert parts[2] == ""  # none algorithm has no signature

    # Decode header
    header_bytes = base64.urlsafe_b64decode(parts[0] + "==")
    header = json.loads(header_bytes.decode())
    assert header["alg"] == "none"
    assert header["typ"] == "JWT"

    # Decode payload
    payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
    payload = json.loads(payload_bytes.decode())
    assert payload["user_id"] == 123
    assert payload["username"] == "alice"

@patch('eval.graders.ctf_oracles.requests.post')
def test_register(mock_post):
    _register("user", "pass")
    mock_post.assert_called_once()

@patch('eval.graders.ctf_oracles.requests.post')
def test_login(mock_post):
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"token": "tok"}
    mock_post.return_value = mock_res

    res = _login("user", "pass")
    assert res == {"token": "tok"}

    mock_res.status_code = 400
    assert _login("user", "pass") is None

def test_auth():
    assert _auth("tok") == {"Authorization": "Bearer tok"}

@patch('eval.graders.ctf_oracles.requests.get')
def test_admin_users(mock_get):
    mock_res = MagicMock()
    mock_res.json.return_value = [{"username": "alice"}]
    mock_get.return_value = mock_res

    res = _admin_users("tok")
    assert res == [{"username": "alice"}]

@patch('eval.graders.ctf_oracles.requests.get')
def test_user_balance(mock_get):
    mock_res = MagicMock()
    mock_res.json.return_value = [{"username": "alice", "balance": 100.0}]
    mock_get.return_value = mock_res

    assert _user_balance("tok", "alice") == 100.0
    assert _user_balance("tok", "bob") is None

@patch('eval.graders.ctf_oracles.requests.get')
def test_user_id(mock_get):
    mock_res = MagicMock()
    mock_res.json.return_value = [{"username": "alice", "id": 1}]
    mock_get.return_value = mock_res

    assert _user_id("tok", "alice") == 1
    assert _user_id("tok", "bob") is None

@patch('eval.graders.ctf_oracles.os.makedirs')
@patch('eval.graders.ctf_oracles.open')
@patch('eval.graders.ctf_oracles.os.remove')
@patch('eval.graders.ctf_oracles._register')
@patch('eval.graders.ctf_oracles._login')
@patch('eval.graders.ctf_oracles._user_id')
@patch('eval.graders.ctf_oracles._user_balance')
@patch('eval.graders.ctf_oracles.requests.post')
@patch('eval.graders.ctf_oracles.requests.put')
@patch('eval.graders.ctf_oracles._start_ssrf_server')
def test_setup(mock_start_ssrf, mock_put, mock_post, mock_balance, mock_uid, mock_login, mock_register, mock_remove, mock_open, mock_makedirs):
    # Mock login returns
    mock_login.side_effect = [
        {"token": "atok", "user": {"id": 1}},  # attacker
        {"token": "vtok", "user": {"id": 2}},  # victim
        {"token": "stok", "user": {"id": 3}},  # seed
    ]
    mock_uid.return_value = 4
    mock_balance.return_value = 100.0

    mock_post_res = MagicMock()
    mock_post_res.json.return_value = {"transaction": {"id": 99}}
    mock_post.return_value = mock_post_res

    ctx = setup()

    assert ctx["attacker_token"] == "atok"
    assert ctx["victim_token"] == "vtok"
    assert ctx["victim_id"] == 2
    assert ctx["attacker_id"] == 1
    assert ctx["receipt_txn_id"] == 99
    assert mock_start_ssrf.call_count == 1

@patch('eval.graders.ctf_oracles._stop_ssrf_server')
def test_teardown(mock_stop_ssrf):
    teardown()
    assert mock_stop_ssrf.call_count == 1
