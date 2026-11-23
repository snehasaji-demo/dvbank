import sys
from unittest.mock import patch, MagicMock
import docs.exploits.race_double_spend as rds

def test_login_recv():
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"token": "mock_token", "user": {"id": 2}}
        mock_post.return_value = mock_resp
        
        token = rds.login_recv(2)
        assert token == "mock_token"

def test_fire():
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp
        
        results = [None]
        rds.fire("token", 2, 100.0, results, 0)
        assert results[0] == 200

def test_main():
    with patch("requests.post") as mock_post, \
         patch("requests.get") as mock_get, \
         patch("sys.argv", ["race_double_spend.py", "--threads", "2"]):
        
        mock_post_resp = MagicMock()
        mock_post_resp.ok = True
        mock_post_resp.json.return_value = {"token": "mock_token", "user": {"id": 2}}
        mock_post.return_value = mock_post_resp
        
        mock_get_resp = MagicMock()
        mock_get_resp.json.return_value = {"balance": 1000.0}
        mock_get.return_value = mock_get_resp
        
        with patch("builtins.print") as mock_print:
            rds.main()
            mock_print.assert_any_call("[+] Starting balance for alice: 1000.0")
