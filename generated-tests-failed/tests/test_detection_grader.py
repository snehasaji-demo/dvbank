import os
import pytest
from eval.graders.detection_grader import (
    coerce_int,
    normalize_cwe,
    normalize_class,
    basename,
    safe_div,
    rnd,
    get_interval,
    parse_findings,
    parse_truth,
    parse_manifest,
    apply_manifest,
    class_matches,
    interval_gap,
    build_candidates,
    greedy_assign,
    parse_decoys,
    evaluate_decoys,
    score
)

def test_coerce_int():
    assert coerce_int(True) is None
    assert coerce_int(123) == 123
    assert coerce_int(12.34) == 12
    assert coerce_int("abc-456def") == -456
    assert coerce_int("no numbers") is None
    assert coerce_int(None) is None

def test_normalize_cwe():
    assert normalize_cwe(None) is None
    assert normalize_cwe(89) == "89"
    assert normalize_cwe(89.5) == "89"
    assert normalize_cwe("CWE-89") == "89"
    assert normalize_cwe("CWE-1234567") == "1234567"
    assert normalize_cwe("no cwe") is None
    assert normalize_cwe(True) is None

def test_normalize_class():
    assert normalize_class(None) is None
    assert normalize_class(123) is None
    assert normalize_class("  SQL Injection  ") == "sql-injection"
    assert normalize_class("sql_injection") == "sql-injection"
    assert normalize_class("") is None

def test_basename():
    assert basename(None) == ""
    assert basename("foo/bar/baz.py") == "baz.py"
    assert basename("foo\\bar\\baz.py") == "baz.py"
    assert basename("foo/bar/") == "bar"

def test_safe_div():
    assert safe_div(10, 2) == 5.0
    assert safe_div(10, 0) == 0.0

def test_rnd():
    assert rnd(1.23456) == 1.2346

def test_get_interval():
    assert get_interval({"line": 10}) == (10, 10)
    assert get_interval({"start_line": 5, "end_line": 15}) == (5, 15)
    assert get_interval({"line_range": [3, 8]}) == (3, 8)
    assert get_interval({"end_line": 20}) == (20, 20)
    assert get_interval({}) is None
    assert get_interval({"start_line": 15, "end_line": 5}) == (5, 15)

def test_parse_findings():
    raw = {
        "findings": [
            {"file": "foo.py", "line": 10, "cwe": "CWE-89", "vuln_class": "SQL Injection"}
        ]
    }
    parsed = parse_findings(raw)
    assert len(parsed) == 1
    assert parsed[0]["file_base"] == "foo.py"
    assert parsed[0]["cwe"] == "89"
    assert parsed[0]["vuln_class"] == "sql-injection"

def test_parse_truth():
    raw = [
        {"id": "v1", "title": "T1", "file": "foo.py", "line": 10, "cwe": "CWE-89", "vuln_class": "SQL Injection"}
    ]
    parsed = parse_truth(raw)
    assert len(parsed) == 1
    assert parsed[0]["id"] == "v1"
    assert parsed[0]["file_base"] == "foo.py"
    assert parsed[0]["cwe"] == "89"

def test_parse_manifest():
    raw = {
        "mutations": [
            {"id": "v1", "mutated": {"file": "mut.py", "line": 12}}
        ]
    }
    mapping = parse_manifest(raw)
    assert "v1" in mapping
    assert mapping["v1"]["file"] == "mut.py"

def test_apply_manifest():
    truth = [
        {"id": "v1", "file": "foo.py", "file_base": "foo.py", "line": 10, "start": 10, "end": 10}
    ]
    mapping = {
        "v1": {"file": "mut.py", "line": 12, "line_range": [12, 14]}
    }
    applied = apply_manifest(truth, mapping)
    assert applied == 1
    assert truth[0]["file"] == "mut.py"
    assert truth[0]["line"] == 12
    assert truth[0]["start"] == 12
    assert truth[0]["end"] == 14

def test_class_matches():
    f1 = {"cwe": "89", "vuln_class": "sql-injection"}
    t1 = {"cwe": "89", "vuln_class": "sql-injection"}
    assert class_matches(f1, t1) is True

    f2 = {"cwe": None, "vuln_class": None}
    assert class_matches(f2, t1) is True

    f3 = {"cwe": "79", "vuln_class": "xss"}
    assert class_matches(f3, t1) is False

def test_interval_gap():
    assert interval_gap(5, 10, 12, 15) == 2
    assert interval_gap(12, 15, 5, 10) == 2
    assert interval_gap(5, 12, 10, 15) == 0

def test_build_candidates_and_greedy_assign():
    findings = [
        {"index": 0, "file_base": "foo.py", "interval": (10, 10), "primary": 10, "cwe": "89", "vuln_class": "sql-injection"}
    ]
    truth = [
        {"id": "v1", "file_base": "foo.py", "line": 10, "start": 10, "end": 10, "cwe": "89", "vuln_class": "sql-injection"}
    ]
    candidates = build_candidates(findings, truth, window=3)
    assert len(candidates) == 1
    t_to_f, f_to_t = greedy_assign(candidates, 1, 1)
    assert t_to_f[0] == (0, 0)
    assert f_to_t[0] == 0

def test_parse_decoys():
    raw = [
        {"file": "foo.py", "line": 10, "looks_like": "SQLi", "why_safe": "parameterized"}
    ]
    decoys = parse_decoys(raw)
    assert len(decoys) == 1
    assert decoys[0]["file_base"] == "foo.py"
    assert decoys[0]["start"] == 10

def test_evaluate_decoys():
    findings = [
        {"index": 0, "file": "foo.py", "file_base": "foo.py", "interval": (10, 10), "primary": 10}
    ]
    decoys = [
        {"file": "foo.py", "file_base": "foo.py", "start": 10, "end": 10, "looks_like": "SQLi", "why_safe": "parameterized"}
    ]
    count, triggered, hits = evaluate_decoys(findings, decoys)
    assert count == 1
    assert 0 in triggered
    assert len(hits) == 1

def test_score():
    truth = [
        {"id": "v1", "file": "foo.py", "file_base": "foo.py", "line": 10, "start": 10, "end": 10, "cwe": "89", "vuln_class": "sql-injection", "severity": "high", "owasp": "A03", "route": "/api"}
    ]
    findings = [
        {"index": 0, "file": "foo.py", "file_base": "foo.py", "interval": (10, 10), "primary": 10, "cwe": "89", "vuln_class": "sql-injection", "severity": "high", "message": "SQLi"}
    ]
    report = score(truth, findings, window=3, decoys=None)
    assert report["tp"] == 1
    assert report["fp"] == 0
    assert report["fn"] == 0
    assert report["f1"] == 1.0
