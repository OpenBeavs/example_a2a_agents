"""Tests for code_review_agent tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code_review_agent.tools import (
    detect_code_smells,
    check_security_patterns,
    calculate_complexity_metrics,
)

CLEAN_PYTHON = '''
def add(a: int, b: int) -> int:
    """Return the sum of a and b."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Return the product of a and b."""
    return a * b
'''

SMELLY_PYTHON = '''
def do_stuff(a, b, c, d, e, f, g):
    x = a * 3600
    y = b * 86400
    z = c * 1000000
    # TODO: fix this later
    # FIXME: also this
    result = x + y + z
    return result
'''

LONG_FUNCTION = "\n".join(["def long_func():", "    pass"] + ["    x = 1" for _ in range(40)])

SECURE_PYTHON = '''
import os

def get_config():
    """Load config from environment."""
    return {
        "api_key": os.environ.get("API_KEY"),
        "db_url": os.environ.get("DB_URL"),
    }
'''

INSECURE_PYTHON = '''
import subprocess
import pickle

password = "super_secret_123"

def run_cmd(user_input):
    subprocess.call(user_input, shell=True)

def load_data(raw_bytes):
    return pickle.loads(raw_bytes)

def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return query
'''


class TestDetectCodeSmells:
    def test_clean_code_no_smells(self):
        result = detect_code_smells(CLEAN_PYTHON, "python")
        assert result["status"] == "success"
        assert result["smell_count"] == 0

    def test_detects_too_many_parameters(self):
        result = detect_code_smells(SMELLY_PYTHON, "python")
        assert result["status"] == "success"
        names = [s["name"] for s in result["smells"]]
        assert "Too Many Parameters" in names

    def test_detects_todo_markers(self):
        result = detect_code_smells(SMELLY_PYTHON, "python")
        names = [s["name"] for s in result["smells"]]
        assert "TODO/FIXME Markers" in names

    def test_detects_long_function(self):
        result = detect_code_smells(LONG_FUNCTION, "python")
        assert result["status"] == "success"
        names = [s["name"] for s in result["smells"]]
        assert "Long Function" in names

    def test_detects_missing_docstring(self):
        code = "def foo(x):\n    return x + 1\n"
        result = detect_code_smells(code, "python")
        names = [s["name"] for s in result["smells"]]
        assert "Missing Docstring" in names

    def test_syntax_error_returns_error(self):
        result = detect_code_smells("def broken(", "python")
        assert result["status"] == "error"

    def test_empty_code_returns_error(self):
        result = detect_code_smells("   ", "python")
        assert result["status"] == "error"

    def test_non_python_language_still_runs(self):
        js_code = "const x = 999 + 1234 * 5678 // TODO fix\n" * 5
        result = detect_code_smells(js_code, "javascript")
        assert result["status"] == "success"
        assert result["language"] == "javascript"


class TestCheckSecurityPatterns:
    def test_clean_code_low_risk(self):
        result = check_security_patterns(SECURE_PYTHON)
        assert result["status"] == "success"
        assert result["overall_risk"] == "low"
        assert result["issue_count"] == 0

    def test_detects_hardcoded_credential(self):
        result = check_security_patterns(INSECURE_PYTHON)
        names = [i["name"] for i in result["issues"]]
        assert "Hardcoded Credential" in names

    def test_detects_shell_injection(self):
        result = check_security_patterns(INSECURE_PYTHON)
        names = [i["name"] for i in result["issues"]]
        assert "Shell Injection Risk" in names

    def test_detects_insecure_deserialization(self):
        result = check_security_patterns(INSECURE_PYTHON)
        names = [i["name"] for i in result["issues"]]
        assert "Insecure Deserialization" in names

    def test_detects_sql_injection(self):
        result = check_security_patterns(INSECURE_PYTHON)
        names = [i["name"] for i in result["issues"]]
        assert "SQL Injection Risk" in names

    def test_detects_eval(self):
        result = check_security_patterns("result = eval(user_input)")
        names = [i["name"] for i in result["issues"]]
        assert "eval() Usage" in names

    def test_overall_risk_critical_when_critical_issue(self):
        result = check_security_patterns('password = "abc123"')
        assert result["overall_risk"] == "critical"

    def test_empty_code_returns_error(self):
        result = check_security_patterns("  ")
        assert result["status"] == "error"

    def test_issue_contains_line_number(self):
        result = check_security_patterns(INSECURE_PYTHON)
        for issue in result["issues"]:
            assert "line" in issue
            assert issue["line"] > 0


class TestCalculateComplexityMetrics:
    def test_simple_function_low_complexity(self):
        result = calculate_complexity_metrics(CLEAN_PYTHON)
        assert result["status"] == "success"
        assert result["metrics"]["cyclomatic_complexity"] <= 3

    def test_complex_function_higher_score(self):
        complex_code = '''
def check(x, y, z):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                while y > 0:
                    y -= 1
            elif i > 10:
                try:
                    z = z / i
                except ZeroDivisionError:
                    pass
    return x + y + z
'''
        result = calculate_complexity_metrics(complex_code)
        assert result["status"] == "success"
        assert result["metrics"]["cyclomatic_complexity"] > 5

    def test_function_count_accurate(self):
        result = calculate_complexity_metrics(CLEAN_PYTHON)
        assert result["metrics"]["function_count"] == 2

    def test_class_count_accurate(self):
        code = "class Foo:\n    pass\nclass Bar:\n    pass\n"
        result = calculate_complexity_metrics(code)
        assert result["metrics"]["class_count"] == 2

    def test_line_count_accurate(self):
        code = "x = 1\ny = 2\nz = 3\n"
        result = calculate_complexity_metrics(code)
        assert result["metrics"]["line_count"] == 3

    def test_syntax_error_returns_error(self):
        result = calculate_complexity_metrics("def broken(")
        assert result["status"] == "error"

    def test_empty_code_returns_error(self):
        result = calculate_complexity_metrics("  ")
        assert result["status"] == "error"

    def test_complexity_rating_present(self):
        result = calculate_complexity_metrics(CLEAN_PYTHON)
        assert "complexity_rating" in result["metrics"]
        assert len(result["metrics"]["complexity_rating"]) > 0
