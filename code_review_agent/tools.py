"""Code Review Agent — tool functions (no ADK dependency)."""

from __future__ import annotations

import ast
import re


def detect_code_smells(code: str, language: str = "python") -> dict:
    """Detect common code smells in a source code snippet.

    Args:
        code: The source code snippet to analyze.
        language: Programming language hint. Full AST analysis only for Python.

    Returns:
        dict with 'status' and 'smells' list, or 'error_message'.
    """
    if not code.strip():
        return {"status": "error", "error_message": "code cannot be empty."}

    smells = []
    lines = code.splitlines()

    if len(lines) > 50:
        smells.append({
            "name": "Long File/Snippet",
            "severity": "medium",
            "detail": f"Snippet is {len(lines)} lines — consider splitting into smaller units.",
        })

    magic_hits = [
        f"line {i+1}"
        for i, line in enumerate(lines)
        if re.search(r'\b(?<!\.)\d{2,}\b', line) and not line.strip().startswith(("#", "//", "*"))
    ]
    if len(magic_hits) > 2:
        smells.append({
            "name": "Magic Numbers",
            "severity": "low",
            "detail": f"Found {len(magic_hits)} numeric literals — consider named constants.",
        })

    todo_hits = [
        f"line {i+1}"
        for i, line in enumerate(lines)
        if re.search(r'\bTODO\b|\bFIXME\b|\bHACK\b', line, re.I)
    ]
    if todo_hits:
        smells.append({
            "name": "TODO/FIXME Markers",
            "severity": "low",
            "detail": f"Unresolved markers at {', '.join(todo_hits)}.",
        })

    if language.lower() == "python":
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"status": "error", "error_message": f"Python syntax error: {e}"}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno or 0) - node.lineno
                if func_lines > 30:
                    smells.append({
                        "name": "Long Function",
                        "severity": "medium",
                        "detail": f"Function `{node.name}` is {func_lines} lines — aim for ≤30.",
                    })
                if len(node.args.args) > 5:
                    smells.append({
                        "name": "Too Many Parameters",
                        "severity": "medium",
                        "detail": f"Function `{node.name}` has {len(node.args.args)} params — consider a dataclass.",
                    })
                if not ast.get_docstring(node):
                    smells.append({
                        "name": "Missing Docstring",
                        "severity": "low",
                        "detail": f"Function `{node.name}` lacks a docstring.",
                    })

    return {
        "status": "success",
        "language": language,
        "smells": smells,
        "smell_count": len(smells),
    }


def check_security_patterns(code: str) -> dict:
    """Scan a code snippet for common security anti-patterns.

    Args:
        code: The source code snippet to scan.

    Returns:
        dict with 'status' and 'issues' list, or 'error_message'.
    """
    if not code.strip():
        return {"status": "error", "error_message": "code cannot be empty."}

    lines = code.splitlines()
    issues = []

    PATTERNS = [
        (r'(?i)(password|passwd|pwd|secret|api_key|token)\s*=\s*["\'][^"\']{4,}["\']',
         "Hardcoded Credential", "critical", "Hardcoded secret detected — use environment variables."),
        (r'(?i)eval\s*\(',
         "eval() Usage", "high", "eval() executes arbitrary code — avoid entirely."),
        (r'(?i)exec\s*\(',
         "exec() Usage", "high", "exec() executes arbitrary code — refactor to explicit calls."),
        (r'(?i)(subprocess\.call|os\.system|os\.popen)\s*\(',
         "Shell Injection Risk", "high", "Possible command injection — use subprocess with a list, not a string."),
        (r'(?i)pickle\.loads?\(',
         "Insecure Deserialization", "high", "pickle.load is unsafe with untrusted data — use JSON."),
        (r'(?i)SELECT\s+\*?\s+FROM.*\+|WHERE.*\+',
         "SQL Injection Risk", "critical", "String-concatenated SQL — use parameterized queries."),
        (r'(?i)assert\s+.*==.*password|assert\s+.*token',
         "Auth via assert", "high", "assert is stripped in optimized builds — use explicit checks."),
        (r'(?i)verify\s*=\s*False',
         "SSL Verification Disabled", "medium", "SSL verification disabled — re-enable in production."),
    ]

    for i, line in enumerate(lines):
        for pattern, name, severity, detail in PATTERNS:
            if re.search(pattern, line):
                issues.append({
                    "name": name,
                    "severity": severity,
                    "line": i + 1,
                    "detail": detail,
                    "snippet": line.strip()[:80],
                })

    critical = [x for x in issues if x["severity"] == "critical"]
    high = [x for x in issues if x["severity"] == "high"]
    overall_risk = "critical" if critical else "high" if high else "medium" if issues else "low"

    return {
        "status": "success",
        "issues": issues,
        "issue_count": len(issues),
        "overall_risk": overall_risk,
    }


def calculate_complexity_metrics(code: str) -> dict:
    """Compute cyclomatic complexity and other metrics for a Python snippet.

    Args:
        code: Python source code snippet to measure.

    Returns:
        dict with 'status' and 'metrics', or 'error_message'.
    """
    if not code.strip():
        return {"status": "error", "error_message": "code cannot be empty."}

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"status": "error", "error_message": f"Python syntax error: {e}"}

    decision_nodes = (
        ast.If, ast.For, ast.While, ast.ExceptHandler,
        ast.With, ast.Assert, ast.comprehension,
    )

    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, decision_nodes):
            complexity += 1
        if isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1

    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    if complexity <= 5:
        rating = "Simple — easy to test and maintain."
    elif complexity <= 10:
        rating = "Moderate — test all branches."
    elif complexity <= 20:
        rating = "Complex — consider refactoring."
    else:
        rating = "Very complex — high risk, refactor urgently."

    return {
        "status": "success",
        "metrics": {
            "cyclomatic_complexity": complexity,
            "line_count": len(code.splitlines()),
            "function_count": len(functions),
            "class_count": len(classes),
            "complexity_rating": rating,
        },
    }
