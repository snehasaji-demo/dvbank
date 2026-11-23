import os
from unittest.mock import patch, MagicMock, mock_open
import pytest
from eval.mutate import (
    apply_mutations,
    is_backend_py,
    build_mutated,
    build_manifest,
    validate
)

def test_apply_mutations():
    # Test with a known mutation
    relpath = "backend/app.py"
    text = "app.config['SECRET_KEY'] = 'supersecret'"
    mutated = apply_mutations(relpath, text)
    assert "ch4ng3me-d3v-s3cr3t" in mutated

    # Test with no mutations
    assert apply_mutations("unknown.py", "some text") == "some text"

def test_is_backend_py():
    assert is_backend_py("backend/app.py") is True
    assert is_backend_py("frontend/index.js") is False
    assert is_backend_py("backend/README.md") is False

@patch("eval.mutate.subprocess.run")
@patch("eval.mutate.shutil.copytree")
@patch("eval.mutate.os.path.isdir", return_value=True)
@patch("eval.mutate.os.path.exists", return_value=True)
@patch("eval.mutate.shutil.rmtree")
@patch("eval.mutate.os.walk")
@patch("eval.mutate.os.path.relpath", return_value="backend/app.py")
@patch("eval.mutate._read")
@patch("eval.mutate._write")
def test_build_mutated(mock_write, mock_read, mock_relpath, mock_walk, mock_rmtree, mock_exists, mock_isdir, mock_copytree, mock_run):
    mock_walk.return_value = [
        ("/path/to/mutated/backend", [], ["app.py"])
    ]
    mock_read.return_value = "app.config['SECRET_KEY'] = 'supersecret'"
    
    build_mutated()
    
    mock_copytree.assert_called_once()
    mock_write.assert_called_once()
    # Verify that the header (5 blank lines) and mutated text are written
    written_text = mock_write.call_args[0][1]
    assert written_text.startswith("\n\n\n\n\n")
    assert "ch4ng3me-d3v-s3cr3t" in written_text

@patch("eval.mutate._read")
@patch("eval.mutate.json.load")
@patch("eval.mutate.open", new_callable=mock_open)
def test_build_manifest(mock_file, mock_json_load, mock_read):
    mock_json_load.return_value = {
        "vulnerabilities": [
            {
                "id": "csrf-quickpay",
                "file": "backend/routes/transaction_routes.py",
                "line": 10,
                "line_range": [8, 12],
                "route": "/api/quickpay"
            }
        ]
    }
    # Mock reading clean and mutated files
    # clean_lines has 15 lines, mutated_lines has 15 lines
    mock_read.side_effect = [
        "\n" * 15, # clean
        "\n" * 20  # mutated
    ]
    
    manifest, gt, line_changed, route_changed, unfound = build_manifest()
    assert "csrf-quickpay" in manifest
    assert manifest["csrf-quickpay"]["route"] == "/api/fastpay"

@patch("eval.mutate.subprocess.run")
@patch("eval.mutate.os.walk")
def test_validate(mock_walk, mock_run):
    mock_walk.return_value = [
        ("/path/to/mutated/backend", [], ["app.py"])
    ]
    # Mock py_compile success
    mock_res_compile = MagicMock()
    mock_res_compile.returncode = 0
    # Mock import app success
    mock_res_import = MagicMock()
    mock_res_import.returncode = 0
    
    mock_run.side_effect = [mock_res_compile, mock_res_import]
    
    manifest = {"csrf-quickpay": {}}
    gt = [{"id": "csrf-quickpay"}]
    
    assert validate(manifest, gt) is True
