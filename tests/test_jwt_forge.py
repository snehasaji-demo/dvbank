import sys
from unittest.mock import patch
from docs.exploits.jwt_forge import b64url, forge, main

def test_b64url():
    assert b64url(b"hello") == "aGVsbG8"

def test_forge():
    token = forge(1)
    assert token.endswith(".")

def test_main():
    with patch("sys.argv", ["jwt_forge.py", "--print-only"]):
        with patch("builtins.print") as mock_print:
            main()
            mock_print.assert_any_call("[+] Forged 'none'-alg token for user_id=1:")
            assert mock_print.call_count == 2
