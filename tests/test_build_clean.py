import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from eval.build_clean import (
    strip_leaking_docstrings,
    strip_py_comments,
    clean_python,
    strip_js_comments,
    copy_target,
    process_tree
)
from eval.decoys.decoy_sql_parameterized import get_user_by_name, search_transactions, insert_user
from eval.decoys.decoy_subprocess_constant import disk_usage_report, kernel_version, list_app_processes

def test_strip_leaking_docstrings():
    src = '"""This is a semgrep leak"""\ndef foo():\n    pass'
    cleaned = strip_leaking_docstrings(src)
    assert "semgrep" not in cleaned
    assert '""""""' in cleaned

    src_no_leak = '"""This is safe"""\ndef foo():\n    pass'
    assert strip_leaking_docstrings(src_no_leak) == src_no_leak

def test_strip_py_comments():
    src = "x = 1  # some comment\ny = 2"
    cleaned = strip_py_comments(src)
    assert "# some comment" not in cleaned
    assert "x = 1" in cleaned

def test_clean_python():
    src = '"""This is a semgrep leak"""\nx = 1  # some comment'
    cleaned = clean_python(src)
    assert "semgrep" not in cleaned
    assert "some comment" not in cleaned
    assert "x = 1" in cleaned

def test_strip_js_comments():
    src = "const x = 1; // cwe-123 comment\nconst y = 2;"
    cleaned = strip_js_comments(src)
    assert "cwe-123" not in cleaned
    assert "const x = 1;" in cleaned

@patch('eval.build_clean.shutil.copytree')
@patch('eval.build_clean.shutil.copy2')
@patch('eval.build_clean.shutil.rmtree')
@patch('eval.build_clean.os.makedirs')
@patch('eval.build_clean.os.path.exists')
def test_copy_target(mock_exists, mock_makedirs, mock_rmtree, mock_copy2, mock_copytree):
    mock_exists.return_value = True
    copy_target()
    assert mock_rmtree.call_count == 1
    assert mock_makedirs.call_count >= 1
    assert mock_copytree.call_count >= 1
    assert mock_copy2.call_count >= 1

@patch('eval.build_clean.os.walk')
@patch('eval.build_clean._read')
@patch('eval.build_clean._write')
def test_process_tree(mock_write, mock_read, mock_walk):
    mock_walk.return_value = [
        ("/fake/clean", [], ["file1.py", "file2.js", "file3.txt"])
    ]
    mock_read.side_effect = lambda path: "some content" if path.endswith(".py") else "js content"
    
    count_py, count_js = process_tree()
    assert count_py == 1
    assert count_js == 1
    mock_write.assert_any_call(os.path.join("/fake/clean", "file1.py"), clean_python("some content"))
    mock_write.assert_any_call(os.path.join("/fake/clean", "file2.js"), strip_js_comments("js content"))

def test_decoy_sql_parameterized():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, username TEXT, email TEXT)")
    cur.execute("CREATE TABLE txn (id INTEGER PRIMARY KEY, account_id INTEGER, description TEXT, amount REAL)")
    
    user_id = insert_user(conn, "alice", "alice@example.com")
    assert user_id == 1
    
    user = get_user_by_name(conn, "alice")
    assert user == (1, "alice")
    
    cur.execute("INSERT INTO txn (account_id, description, amount) VALUES (1, 'Rent payment', 100.0)")
    txs = search_transactions(conn, 1, "Rent")
    assert len(txs) == 1
    assert txs[0][1] == "Rent payment"

@patch('eval.decoys.decoy_subprocess_constant.subprocess.run')
def test_disk_usage_report(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = "df output"
    mock_run.return_value = mock_res
    assert disk_usage_report() == "df output"

@patch('eval.decoys.decoy_subprocess_constant.subprocess.check_output')
def test_kernel_version(mock_check_output):
    mock_check_output.return_value = "5.15.0"
    assert kernel_version() == "5.15.0"

@patch('eval.decoys.decoy_subprocess_constant.subprocess.run')
def test_list_app_processes(mock_run):
    mock_res = MagicMock()
    mock_res.stdout = "ps output"
    mock_run.return_value = mock_res
    assert list_app_processes() == "ps output"
