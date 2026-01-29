"""
CLI smoke tests for aisentry.

Tests basic CLI functionality including scan, audit, and output formats.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


# Sample vulnerable code for testing
SAMPLE_CODE = '''
"""Sample vulnerable code for testing."""
from openai import OpenAI

client = OpenAI()

def vulnerable_prompt(user_input):
    """Vulnerable: user input directly in prompt."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Process this: {user_input}"}]
    )
    return response.choices[0].message.content

def safe_prompt(user_input):
    """Safe: parameterized prompt."""
    sanitized = user_input.replace("{", "").replace("}", "")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": sanitized}
        ]
    )
    return response.choices[0].message.content
'''


@pytest.fixture
def temp_project():
    """Create a temporary project directory with sample code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample Python file
        sample_file = Path(tmpdir) / "app.py"
        sample_file.write_text(SAMPLE_CODE)
        yield tmpdir


class TestCLIScan:
    """Test scan command."""

    def test_scan_text_output(self, temp_project):
        """Test scan with default text output."""
        result = subprocess.run(
            ["aisentry", "scan", temp_project, "--no-audit"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "aisentry" in result.stdout or "Scan" in result.stdout

    def test_scan_json_output(self, temp_project):
        """Test scan with JSON output (uses quiet mode for clean parsing)."""
        # Use quiet mode for reliable JSON parsing
        result = subprocess.run(
            ["aisentry", "scan", temp_project, "-o", "json", "--no-audit", "-q"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "report_type" in data
        assert data["report_type"] == "static_scan"
        assert "summary" in data
        assert "findings" in data

    def test_scan_json_quiet(self, temp_project):
        """Test scan with JSON output in quiet mode."""
        result = subprocess.run(
            ["aisentry", "scan", temp_project, "-o", "json", "-q", "--no-audit"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # In quiet mode, output should be pure JSON
        data = json.loads(result.stdout)
        assert "report_type" in data
        assert data["report_type"] == "static_scan"

    def test_scan_sarif_output(self, temp_project):
        """Test scan with SARIF output."""
        result = subprocess.run(
            ["aisentry", "scan", temp_project, "-o", "sarif", "-q", "--no-audit"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "$schema" in data
        assert "runs" in data
        assert data["runs"][0]["tool"]["driver"]["name"] == "aisentry"

    def test_scan_html_output(self, temp_project):
        """Test scan with HTML output to file."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_file = f.name

        try:
            result = subprocess.run(
                ["aisentry", "scan", temp_project, "-o", "html", "-f", output_file, "--no-audit", "-q"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert Path(output_file).exists()
            content = Path(output_file).read_text()
            assert "<!DOCTYPE html>" in content
            assert "aisentry" in content
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_scan_severity_filter(self, temp_project):
        """Test scan with severity filter."""
        result = subprocess.run(
            ["aisentry", "scan", temp_project, "-o", "json", "-q", "-s", "high", "--no-audit"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # All findings should be HIGH or CRITICAL
        for finding in data.get("findings", []):
            assert finding["severity"] in ["HIGH", "CRITICAL"]

    def test_scan_category_filter(self, temp_project):
        """Test scan with category filter."""
        result = subprocess.run(
            ["aisentry", "scan", temp_project, "-o", "json", "-q", "--category", "LLM01", "--no-audit"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # All findings should be LLM01 category
        for finding in data.get("findings", []):
            assert "LLM01" in finding["category"]

    def test_scan_nonexistent_path(self):
        """Test scan with nonexistent path."""
        result = subprocess.run(
            ["aisentry", "scan", "/nonexistent/path", "-q", "--no-audit"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Error" in result.stderr or "Error" in result.stdout


class TestCLIAudit:
    """Test audit command."""

    def test_audit_text_output(self, temp_project):
        """Test audit with default text output."""
        result = subprocess.run(
            ["aisentry", "audit", temp_project],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "AUDIT" in result.stdout.upper() or "Score" in result.stdout

    def test_audit_json_output(self, temp_project):
        """Test audit with JSON output."""
        result = subprocess.run(
            ["aisentry", "audit", temp_project, "-o", "json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Check that output contains JSON-like structure
        output = result.stdout
        assert '"audit_id"' in output
        assert '"overall_score"' in output
        assert '"categories"' in output


class TestCLIHelp:
    """Test help commands."""

    def test_main_help(self):
        """Test main --help."""
        result = subprocess.run(
            ["aisentry", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "scan" in result.stdout
        assert "audit" in result.stdout

    def test_scan_help(self):
        """Test scan --help."""
        result = subprocess.run(
            ["aisentry", "scan", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "OWASP" in result.stdout or "LLM" in result.stdout
        assert "--quiet" in result.stdout

    def test_audit_help(self):
        """Test audit --help."""
        result = subprocess.run(
            ["aisentry", "audit", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "security" in result.stdout.lower() or "audit" in result.stdout.lower()

    def test_version(self):
        """Test --version."""
        result = subprocess.run(
            ["aisentry", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "aisentry" in result.stdout


class TestCLIOutputFile:
    """Test output file functionality."""

    def test_json_output_file(self, temp_project):
        """Test saving JSON to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            result = subprocess.run(
                ["aisentry", "scan", temp_project, "-o", "json", "-f", output_file, "-q", "--no-audit"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert Path(output_file).exists()

            content = Path(output_file).read_text()
            data = json.loads(content)
            assert "report_type" in data
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_sarif_output_file(self, temp_project):
        """Test saving SARIF to file."""
        with tempfile.NamedTemporaryFile(suffix=".sarif", delete=False) as f:
            output_file = f.name

        try:
            result = subprocess.run(
                ["aisentry", "scan", temp_project, "-o", "sarif", "-f", output_file, "-q", "--no-audit"],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert Path(output_file).exists()

            content = Path(output_file).read_text()
            data = json.loads(content)
            assert "$schema" in data
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
