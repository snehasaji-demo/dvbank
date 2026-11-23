import os
import json
import base64
from unittest.mock import patch, MagicMock, mock_open
import pytest
from eval.graders.ctf_oracles import (
    forge_none_token,
    setup,
    teardown
)

def test_forge_none_token():
    token = forge_none_token(123, "alice")
    assert token.endswith(".")
    parts = token.split(".")
    assert len(parts) == 3
    
    # Decode header
    header_b64 = parts[0] + "=" * (4 - len(parts[0]) % 4)
    header = json.loads(base64.urlsafe_b64decode(header_b64).decode())
    assert header["alg"] == "none"
    assert header["typ"] == "JWT"
    
    # Decode payload
    payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    assert payload["user_id"] == 123
    assert payload["username"] == "alice"

@patch("eval.graders.ctf_oracles.requests.post")
@patch("eval.graders.ctf_oracles.requests.get")
@patch("eval.graders.ctf_oracles.requests.put")
@patch("eval.graders.ctf_oracles.os.makedirs")
@patch("eval.graders.ctf_oracles.open", new_callable=mock_open)
@patch("eval.graders.ctf_oracles._start_ssrf_server")
@patch("eval.graders.ctf_oracles._user_balance", return_value=1000.0)
@patch("eval.graders.ctf_oracles._user_id", return_value=2)
def test_setup(mock_user_id, mock_user_balance, mock_start_ssrf, mock_file, mock_makedirs, mock_put, mock_get, mock_post):
    # Mock responses for requests
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "token": "mock_token",
        "user": {"id": 1},
        "transaction": {"id": 42}
    }
    mock_post.return_value = mock_post_resp
    
    ctx = setup()
    
    assert ctx["attacker_token"] == "mock_token"
    assert ctx["victim_token"] == "mock_token"
    assert ctx["victim_id"] == 1
    assert ctx["receipt_txn_id"] == 42
    mock_start_ssrf.assert_called_once()

@patch("eval.graders.ctf_oracles._stop_ssrf_server")
def test_teardown(mock_stop_ssrf):
    teardown()
    mock_stop_ssrf.assert_called_once()
