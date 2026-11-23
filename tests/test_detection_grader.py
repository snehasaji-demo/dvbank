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
    assert coerce_int(False) is None
    assert coerce_int(123) == 123
    assert coerce_int(12.3) == 12
    assert coerce_int("123") == 123
    assert coerce_int("abc-123xyz") == -123
    assert coerce_int("abc") is None
    assert coerce_int(None) is None

def test_normalize_cwe():
    assert normalize_cwe(None) is None
    assert normalize_cwe(89) == "89"
    assert normalize_cwe("CWE-89") == "89"
    assert normalize_cwe("cwe-89") == "89"
    assert normalize_cwe("89") == "89"
    assert normalize_cwe("abc") is None
    assert normalize_cwe(True) is None

def test_normalize_class():
    assert normalize_class(None) is None
    assert normalize_class("SQL Injection") == "sql-injection"
    assert normalize_class("  sql_injection  ") == "sql-injection"
    assert normalize_class("") is None
    assert normalize_class(123) is None

def test_basename():
    assert basename("foo/bar.py") == "bar.py"
    assert basename("foo\\bar.py") == "bar.py"
    assert basename(None) == ""
    assert basename(123) == ""

def test_safe_div():
    assert safe_div(1, 2) == 0.5
    assert safe_div(1, 0) == 0.0

def test_rnd():
    assert rnd(1.23456) == 1.2346

def test_get_interval():
    assert get_interval({"line": 10}) == (10, 10)
    assert get_interval({"start_line": 10, "end_line": 20}) == (10, 20)
    assert get_interval({"line_range": [10, 20]}) == (10, 20)
    assert get_interval({"end_line": 20}) == (20, 20)
    assert get_interval({"start_line": 20, "end_line": 10}) == (10, 20)
    assert get_interval({}) is None

def test_parse_findings():
    raw = {"findings": [{"file": "foo.py", "line": 10, "cwe": "CWE-89", "vuln_class": "SQL Injection"}]}
    parsed = parse_findings(raw)
    assert len(parsed) == 1
    assert parsed[0]["file_base"] == "foo.py"
    assert parsed[0]["cwe"] == "89"
    assert parsed[0]["vuln_class"] == "sql-injection"

    assert parse_findings("not a dict") == []
    assert parse_findings([]) == []

def test_parse_truth():
    raw = {"vulnerabilities": [{"id": "v1", "file": "foo.py", "line": 10, "cwe": "CWE-89", "vuln_class": "SQL Injection"}]}
    parsed = parse_truth(raw)
    assert len(parsed) == 1
    assert parsed[0]["id"] == "v1"
    assert parsed[0]["file_base"] == "foo.py"
    assert parsed[0]["cwe"] == "89"

def test_parse_manifest():
    raw = {"mutations": [{"id": "v1", "mutated": {"file": "foo.py", "line": 10}}]}
    mapping = parse_manifest(raw)
    assert "v1" in mapping
    assert mapping["v1"]["file"] == "foo.py"

    raw_list = [{"id": "v1", "mutated": {"file": "foo.py", "line": 10}}]
    mapping_list = parse_manifest(raw_list)
    assert "v1" in mapping_list

def test_apply_manifest():
    truth = [{"id": "v1", "file": "old.py", "start": 5, "end": 5, "line": 5, "route": "/old"}]
    mapping = {"v1": {"file": "new.py", "line_range": [10, 12], "line": 11, "route": "/new"}}
    applied = apply_manifest(truth, mapping)
    assert applied == 1
    assert truth[0]["file"] == "new.py"
    assert truth[0]["start"] == 10
    assert truth[0]["end"] == 12
    assert truth[0]["line"] == 11
    assert truth[0]["route"] == "/new"

def test_class_matches():
    finding = {"cwe": "89", "vuln_class": "sql-injection"}
    truth = {"cwe": "89", "vuln_class": "sql-injection"}
    assert class_matches(finding, truth) is True

    finding_loc_only = {"cwe": None, "vuln_class": None}
    assert class_matches(finding_loc_only, truth) is True

    finding_mismatch = {"cwe": "78", "vuln_class": "command-injection"}
    assert class_matches(finding_mismatch, truth) is False

def test_interval_gap():
    assert interval_gap(5, 10, 12, 15) == 2
    assert interval_gap(12, 15, 5, 10) == 2
    assert interval_gap(5, 12, 10, 15) == 0

def test_build_candidates_and_greedy_assign():
    findings = parse_findings([{"file": "foo.py", "line": 10, "cwe": "CWE-89"}])
    truth = parse_truth([{"id": "v1", "file": "foo.py", "line": 11, "cwe": "CWE-89"}])
    candidates = build_candidates(findings, truth, window=3)
    assert len(candidates) == 1
    
    truth_to_finding, finding_to_truth = greedy_assign(candidates, len(truth), len(findings))
    assert truth_to_finding[0][0] == 0

def test_parse_decoys_and_evaluate_decoys():
    raw = [{"file": "foo.py", "line": 10, "looks_like": "sql", "why_safe": "parameterized"}]
    decoys = parse_decoys(raw)
    assert len(decoys) == 1
    assert decoys[0]["file_base"] == "foo.py"

    findings = parse_findings([{"file": "foo.py", "line": 10}])
    count, triggered, hits = evaluate_decoys(findings, decoys)
    assert count == 1
    assert 0 in triggered

def test_score():
    findings = parse_findings([{"file": "foo.py", "line": 10, "cwe": "CWE-89"}])
    truth = parse_truth([{"id": "v1", "file": "foo.py", "line": 11, "cwe": "CWE-89"}])
    decoys = parse_decoys([{"file": "foo.py", "line": 20, "looks_like": "sql", "why_safe": "parameterized"}])
    
    res = score(truth, findings, window=3, decoys=decoys)
    assert res["summary"]["true_positives"] == 1
    assert res["summary"]["false_positives"] == 0
    assert res["summary"]["false_negatives"] == 0
    assert res["summary"]["precision"] == 1.0
    assert res["summary"]["recall"] == 1.0
    assert res["summary"]["f1"] == 1.0
