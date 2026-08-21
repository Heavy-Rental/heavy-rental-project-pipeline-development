#!/usr/bin/env python3
"""Unit tests for combine-security-report.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "combine_security_report", ROOT / "combine-security-report.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["combine_security_report"] = _MODULE
_SPEC.loader.exec_module(_MODULE)
csr = _MODULE


SEMGREP_SNIPPET_SECRET = "password=SUPERSECRET123"


def _semgrep_sarif() -> dict:
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "semgrep", "rules": []}},
                "results": [
                    {
                        "ruleId": "heavy-rental.secrets.hardcoded",
                        "level": "error",
                        "message": {"text": "Hard-coded credential in env file"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "app/.env"},
                                    "region": {
                                        "startLine": 3,
                                        "snippet": {"text": SEMGREP_SNIPPET_SECRET},
                                    },
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _trivy_sarif() -> dict:
    return {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "Trivy"}},
                "results": [
                    {
                        "ruleId": "CVE-2024-0001",
                        "level": "warning",
                        "message": {"text": "HIGH vulnerability in libexample"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "pom.xml"},
                                    "region": {"startLine": 42},
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _pip_audit() -> dict:
    return {
        "dependencies": [
            {
                "name": "requests",
                "version": "2.31.0",
                "vulns": [
                    {
                        "id": "GHSA-xxxx-yyyy",
                        "fix_versions": ["2.32.0"],
                        "description": "Example advisory",
                    }
                ],
            }
        ]
    }


def _write_reports(tmp_path: Path) -> Path:
    (tmp_path / "semgrep.sarif").write_text(json.dumps(_semgrep_sarif()), encoding="utf-8")
    (tmp_path / "trivy-fs.sarif").write_text(json.dumps(_trivy_sarif()), encoding="utf-8")
    (tmp_path / "pip-audit.json").write_text(json.dumps(_pip_audit()), encoding="utf-8")
    (tmp_path / "semgrep-custom-rules.yml").write_text("rules: []\n", encoding="utf-8")
    return tmp_path


def _pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def test_collects_sarif_and_pip_audit(tmp_path: Path) -> None:
    reports = csr.collect_reports(_write_reports(tmp_path))
    names = {r.source_file: r for r in reports}
    assert set(names) == {"semgrep.sarif", "trivy-fs.sarif", "pip-audit.json"}
    assert names["semgrep.sarif"].findings[0].location == "app/.env:3"
    assert names["semgrep.sarif"].findings[0].message == "Hard-coded credential in env file"
    assert SEMGREP_SNIPPET_SECRET not in names["semgrep.sarif"].findings[0].message
    assert names["pip-audit.json"].findings[0].rule_id == "GHSA-xxxx-yyyy"


def test_empty_dir_writes_valid_pdf(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out.pdf"
    rc = csr.main(
        [
            "--input-dir",
            str(empty),
            "--output",
            str(out),
            "--title",
            "Empty combined security report",
            "--repo",
            "acme/app",
            "--sha",
            "abc123def",
            "--run-url",
            "https://github.com/acme/app/actions/runs/1",
        ]
    )
    assert rc == 0
    text = _pdf_text(out)
    assert "No scanner outputs were produced" in text
    assert "acme/app" in text
    assert "abc123def" in text


def test_pdf_contains_findings_and_redacts_snippets(tmp_path: Path) -> None:
    reports_dir = _write_reports(tmp_path)
    out = tmp_path / "combined-security-report.pdf"
    rc = csr.main(
        [
            "--input-dir",
            str(reports_dir),
            "--output",
            str(out),
            "--title",
            "REST API combined security report",
            "--repo",
            "Heavy-Rental/heavy-rental-spring-rest-api",
            "--sha",
            "deadbeefcafebabe",
            "--run-url",
            "https://github.com/Heavy-Rental/app/actions/runs/99",
        ]
    )
    assert rc == 0
    assert out.is_file() and out.stat().st_size > 0
    text = _pdf_text(out)
    assert "REST API combined security report" in text
    assert "semgrep" in text.lower()
    assert "Trivy" in text
    assert "pip-audit" in text
    assert "Hard-coded credential in env file" in text
    assert "app/.env:3" in text
    assert "CVE-2024-0001" in text
    assert "GHSA-xxxx-yyyy" in text
    assert SEMGREP_SNIPPET_SECRET not in text
    assert "SUPERSECRET" not in text
    assert "Source snippets are omitted" in text


def test_unreadable_sarif_is_noted(tmp_path: Path) -> None:
    (tmp_path / "broken.sarif").write_text("{not json", encoding="utf-8")
    report = csr.parse_sarif(tmp_path / "broken.sarif")
    assert report.present
    assert report.findings == []
    assert "Could not parse SARIF" in report.note
