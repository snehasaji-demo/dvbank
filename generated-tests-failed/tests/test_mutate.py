import os
import json
import pytest
from unittest.mock import patch, MagicMock
from eval.mutate import (
    apply_mutations,
    is_backend_py,
    build_mutated,
    build_manifest,
    validate
)

def test_apply_mutations():
    # Test with a known mutation path
    text = "app.config['SECRET_KEY'] = 'supersecret'"
    mutated = apply_mutations("backend/app.py", text)
    assert mutated == "app.config['SECRET_KEY'] = 'ch4ng3me-d3v-s3cr3t'"

    # Test with an unknown path
    text2 = "some other text"
    assert apply_mutations("unknown.py", text2) == text2

def test_is_backend_py():
    assert is_backend_py("backend/app.py") is True
    assert is_backend_py("backend/routes/admin_routes.py") is True
    assert is_backend_py("frontend/app.js") is False
    assert is_backend_py("backend/static/style.css") is False
    assert is_backend_py("app.py") is False

@patch('eval.mutate.os.path.isdir')
@patch('eval.mutate.subprocess.run')
@patch('eval.mutate.os.path.exists')
@patch('eval.mutate.shutil.rmtree')
@patch('eval.mutate.shutil.copytree')
@patch('eval.mutate.os.walk')
@patch('eval.mutate._read')
@patch('eval.mutate._write')
@patch('eval.mutate.os.path.relpath')
def test_build_mutated(mock_relpath, mock_write, mock_read, mock_walk, mock_copytree, mock_rmtree, mock_exists, mock_run, mock_isdir):
    mock_isdir.return_value = True
    mock_exists.return_value = True
    mock_walk.return_value = [
        ("/fake/mutated/backend", [], ["app.py"])
    ]
    mock_read.return_value = "app.config['SECRET_KEY'] = 'supersecret'"
    mock_relpath.return_value = "backend/app.py"

    build_mutated()

    assert mock_copytree.call_count == 1
    assert mock_rmtree.call_count == 1
    mock_write.assert_any_call("/fake/mutated/backend/app.py", "\n" * 5 + "app.config['SECRET_KEY'] = 'ch4ng3me-d3v-s3cr3t'")

@patch('eval.mutate.json.load')
@patch('eval.mutate._read')
@patch('eval.mutate._write')
@patch('eval.mutate.open')
def test_build_manifest(mock_open, mock_write, mock_read, mock_json_load):
    mock_json_load.return_value = {
        "vulnerabilities": [
            {
                "id": "csrf-quickpay",
                "file": "backend/routes/transaction_routes.py",
                "line": 1,
                "line_range": [1, 2],
                "route": "/api/quickpay"
            }
        ]
    }
    # Mock clean and mutated file reads
    mock_read.side_effect = lambda path: "def quickpay(\n" if "clean" in path else "\n\n\n\n\ndef quickpay(\n"

    manifest, gt, line_changed, route_changed, unfound = build_manifest()

    assert "csrf-quickpay" in manifest
    assert manifest["csrf-quickpay"]["route"] == "/api/fastpay"
    assert line_changed >= 0
    assert route_changed >= 0

@patch('eval.mutate.os.walk')
@patch('eval.mutate.subprocess.run')
def test_validate(mock_run, mock_walk):
    mock_walk.return_value = [
        ("/fake/mutated/backend", [], ["app.py"])
    ]
    # Mock successful py_compile and import app
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stderr = ""
    mock_run.return_value = mock_res

    manifest = {
        "csrf-quickpay": {}
    }
    gt = [
        {"id": "csrf-quickpay"}
    ]

    assert validate(manifest, gt) is True
