import sys
from unittest.mock import patch, MagicMock
from docs.exploits.jwt_forge import b64url, forge, main as jwt_forge_main
from docs.exploits.race_double_spend import login_recv, balance, fire, main as race_main
from docs.exploits.brute_force import attempt, main as brute_main

def test_b64url():
    assert b64url(b"hello") == "aGVsbG8"
    assert b64url(b"") == ""

def test_forge():
    token = forge(1)
    assert token.startswith("eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0") # header
    assert "eyJ1c2VyX2lkIjogMSwgInVzZXJuYW1lIjogImZvcmdlZCJ9" in token # payload
    assert token.endswith(".")

def test_main_print_only(capsys):
    test_args = ["jwt_forge.py", "--print-only", "--user-id", "5"]
    with patch.object(sys, 'argv', test_args):
        jwt_forge_main()
    captured = capsys.readouterr()
    assert "[+] Forged 'none'-alg token for user_id=5:" in captured.out

@patch('docs.exploits.race_double_spend.requests.post')
def test_login_recv(mock_post):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"token": "fake_token", "user": {"id": 2}}
    mock_post.return_value = mock_resp
    
    token = login_recv(2)
    assert token == "fake_token"

@patch('docs.exploits.race_double_spend.requests.get')
def test_balance(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"balance": 123.45}
    mock_get.return_value = mock_resp
    
    bal = balance("fake_token")
    assert bal == 123.45

@patch('docs.exploits.race_double_spend.requests.post')
def test_fire(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp
    
    results = [None]
    fire("fake_token", 2, 100.0, results, 0)
    assert results[0] == 200

@patch('docs.exploits.race_double_spend.login')
@patch('docs.exploits.race_double_spend.login_recv')
@patch('docs.exploits.race_double_spend.balance')
@patch('docs.exploits.race_double_spend.fire')
@patch('sys.argv', ["race_double_spend.py", "--threads", "2"])
def test_race_main(mock_fire, mock_balance, mock_login_recv, mock_login):
    mock_login.return_value = "sender_token"
    mock_login_recv.return_value = "recv_token"
    mock_balance.side_effect = [500.0, 300.0, 400.0, 400.0]
    
    race_main()
    assert mock_fire.call_count == 2

@patch('docs.exploits.brute_force.requests.post')
def test_attempt(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp
    assert attempt("alice", "password123") is True

@patch('docs.exploits.brute_force.attempt')
@patch('sys.argv', ["brute_force.py", "--user", "alice"])
def test_brute_main(mock_attempt):
    mock_attempt.return_value = True
    brute_main()
    assert mock_attempt.call_count == 1
