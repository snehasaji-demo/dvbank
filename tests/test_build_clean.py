import os
import shutil
from unittest.mock import patch
import pytest
import eval.build_clean as bc

def test_strip_leaking_docstrings():
    src = '"""This is a semgrep vulnerability cwe-78 test"""\ndef foo():\n    pass'
    cleaned = bc.strip_leaking_docstrings(src)
    assert "semgrep" not in cleaned
    assert "vulnerability" not in cleaned
    assert '""""""' in cleaned

def test_strip_py_comments():
    src = "def foo():\n    # This is a comment\n    pass"
    cleaned = bc.strip_py_comments(src)
    assert "comment" not in cleaned
    assert "def foo():" in cleaned

def test_clean_python():
    src = '"""cwe-100"""\n# comment\npass'
    cleaned = bc.clean_python(src)
    assert "cwe" not in cleaned
    assert "comment" not in cleaned

def test_strip_js_comments():
    src = "function foo() {\n    // cwe-123 comment\n    return 1;\n}"
    cleaned = bc.strip_js_comments(src)
    assert "cwe" not in cleaned
    assert "return 1;" in cleaned

def test_copy_target_and_process_tree(tmp_path):
    repo_dir = tmp_path / "repo"
    clean_dir = tmp_path / "clean"
    
    # Create dummy repo structure
    os.makedirs(repo_dir / "backend")
    os.makedirs(repo_dir / "frontend" / "src")
    
    with open(repo_dir / "backend" / "app.py", "w") as f:
        f.write('"""cwe-100"""\n# comment\npass')
        
    with open(repo_dir / "frontend" / "src" / "index.js", "w") as f:
        f.write("// cwe-123 comment\nconsole.log(1);")
        
    with open(repo_dir / "frontend" / "package.json", "w") as f:
        f.write("{}")
        
    with open(repo_dir / "docker-compose.yml", "w") as f:
        f.write("version: '3'")
        
    with patch("eval.build_clean.REPO", str(repo_dir)), \
         patch("eval.build_clean.CLEAN", str(clean_dir)):
        
        bc.copy_target()
        assert os.path.exists(clean_dir / "backend" / "app.py")
        assert os.path.exists(clean_dir / "frontend" / "src" / "index.js")
        
        count_py, count_js = bc.process_tree()
        assert count_py == 1
        assert count_js == 1
        
        # Verify they were cleaned
        with open(clean_dir / "backend" / "app.py", "r") as f:
            content = f.read()
            assert "cwe" not in content
            assert "comment" not in content
            
        with open(clean_dir / "frontend" / "src" / "index.js", "r") as f:
            content = f.read()
            assert "cwe" not in content
