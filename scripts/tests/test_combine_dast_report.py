#!/usr/bin/env python3
"""Unit tests for combine-dast-report.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "combine_dast_report", ROOT / "combine-dast-report.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["combine_dast_report"] = _MODULE
_SPEC.loader.exec_module(_MODULE)
cdr = _MODULE


ZAP_EVIDENCE_SECRET = "Authorization: Bearer SUPERSECRETTOKEN"
DASTARDLY_BODY_SECRET = "password=SUPERSECRET123"


def _zap_json() -> dict:
    return {
        "site": [
            {
                "@name": "http://dast-app:8080",
                "alerts": [
                    {
                        "pluginid": "10021",
                        "alert": "X-Content-Type-Options Header Missing",
                        "riskcode": "1",
                        "riskdesc": "Low (Medium)",
                        "desc": "<p>The Anti-MIME-Sniffing header is not set.</p>",
                        "instances": [
                            {
                                "uri": "http://dast-app:8080/actuator/health",
                                "method": "GET",
                                "evidence": ZAP_EVIDENCE_SECRET,
                            }
                        ],
                    }
                ],
            }
        ]
    }


def _dastardly_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Dastardly">
  <testsuite name="http://dast-app:8080" tests="1" failures="1">
    <testcase name="Content Security Policy" classname="http://dast-app:8080/">
      <failure message="Missing Content-Security-Policy header">{DASTARDLY_BODY_SECRET}</failure>
    </testcase>
  </testsuite>
</testsuites>
"""


def _nuclei_jsonl() -> str:
    return json.dumps(
        {
            "template-id": "http-missing-security-headers",
            "info": {
                "name": "HTTP Missing Security Headers",
                "severity": "info",
                "description": "One or more security headers are missing.",
            },
            "matched-at": "http://dast-app:8080",
        }
    ) + "\n"


def _mobsf_json() -> dict:
    return {
        "file_name": "heavy-rental-mobile.apk",
        "high": ["Insecure random number generator"],
        "certificate_analysis": {
            "certificate_findings": [
                ["warning", "Signed with v1 scheme", "App is signed with v1 signature scheme"]
            ]
        },
        "manifest_analysis": {
            "manifest_findings": [
                {
                    "rule": "clear_text_traffic",
                    "title": "Clear text traffic",
                    "severity": "high",
                    "description": "The app allows clear text traffic.",
                }
            ]
        },
        "code_analysis": {
            "findings": {
                "android_logging": {
                    "files": {"MainActivity.kt": "42"},
                    "metadata": {
                        "severity": "info",
                        "description": "The App logs information.",
                    },
                }
            }
        },
    }


def _write_web_reports(tmp_path: Path) -> Path:
    (tmp_path / "zap.json").write_text(json.dumps(_zap_json()), encoding="utf-8")
    (tmp_path / "dastardly-report.xml").write_text(_dastardly_xml(), encoding="utf-8")
    (tmp_path / "nuclei.jsonl").write_text(_nuclei_jsonl(), encoding="utf-8")
    (tmp_path / "zap.html").write_text("<html>ignore</html>", encoding="utf-8")
    (tmp_path / "INDEX.md").write_text("# ignore", encoding="utf-8")
    return tmp_path


def _pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def test_collects_zap_dastardly_nuclei(tmp_path: Path) -> None:
    reports = cdr.collect_reports(_write_web_reports(tmp_path))
    names = {r.source_file: r for r in reports}
    assert set(names) == {"zap.json", "dastardly-report.xml", "nuclei.jsonl"}
    zap = names["zap.json"].findings[0]
    assert zap.rule_id == "10021"
    assert zap.location == "http://dast-app:8080/actuator/health"
    assert "Anti-MIME-Sniffing" in zap.message
    assert ZAP_EVIDENCE_SECRET not in zap.message
    dast = names["dastardly-report.xml"].findings[0]
    assert dast.rule_id == "Content Security Policy"
    assert "Missing Content-Security-Policy" in dast.message
    assert DASTARDLY_BODY_SECRET not in dast.message
    nuclei = names["nuclei.jsonl"].findings[0]
    assert nuclei.rule_id == "http-missing-security-headers"
    assert nuclei.location == "http://dast-app:8080"


def test_collects_mobsf(tmp_path: Path) -> None:
    (tmp_path / "mobsf-report.json").write_text(json.dumps(_mobsf_json()), encoding="utf-8")
    reports = cdr.collect_reports(tmp_path)
    assert len(reports) == 1
    ids = {f.rule_id for f in reports[0].findings}
    assert "Insecure random number generator" in ids
    assert "Signed with v1 scheme" in ids
    assert "Clear text traffic" in ids
    assert "android_logging" in ids
    logging = next(f for f in reports[0].findings if f.rule_id == "android_logging")
    assert logging.location == "MainActivity.kt"


def test_empty_dir_writes_valid_pdf(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out.pdf"
    rc = cdr.main(
        [
            "--input-dir",
            str(empty),
            "--output",
            str(out),
            "--title",
            "Empty combined DAST report",
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
    assert "No DAST scanner outputs were produced" in text
    assert "acme/app" in text
    assert "abc123def" in text


def test_pdf_contains_findings_and_omits_evidence(tmp_path: Path) -> None:
    reports_dir = _write_web_reports(tmp_path)
    out = tmp_path / "combined-dast-report.pdf"
    rc = cdr.main(
        [
            "--input-dir",
            str(reports_dir),
            "--output",
            str(out),
            "--title",
            "REST API combined DAST report",
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
    assert "REST API combined DAST report" in text
    assert "OWASP ZAP" in text
    assert "Dastardly" in text
    assert "Nuclei" in text
    assert "10021" in text
    assert "Content Security Policy" in text
    assert "http-missing-security-headers" in text
    assert ZAP_EVIDENCE_SECRET not in text
    assert "SUPERSECRETTOKEN" not in text
    assert DASTARDLY_BODY_SECRET not in text
    assert "SUPERSECRET123" not in text
    assert "Request bodies and scanner evidence snippets are omitted" in text


def test_zap_placeholder_is_noted(tmp_path: Path) -> None:
    (tmp_path / "zap.json").write_text("ZAP did not write zap.json (exit=2)\n", encoding="utf-8")
    report = cdr.parse_zap(tmp_path / "zap.json")
    assert report.present
    assert report.findings == []
    assert "ZAP did not write" in report.note


def test_unreadable_zap_is_noted(tmp_path: Path) -> None:
    (tmp_path / "zap.json").write_text("{not json", encoding="utf-8")
    report = cdr.parse_zap(tmp_path / "zap.json")
    assert report.present
    assert report.findings == []
    assert "Could not parse" in report.note


def test_empty_dastardly_placeholder(tmp_path: Path) -> None:
    (tmp_path / "dastardly-report.xml").write_text(
        '<testsuites name="dastardly"/>\n', encoding="utf-8"
    )
    report = cdr.parse_dastardly(tmp_path / "dastardly-report.xml")
    assert report.findings == []
    assert "Placeholder" in report.note


def test_mobsf_error_object(tmp_path: Path) -> None:
    (tmp_path / "mobsf-report.json").write_text(
        json.dumps({"error": "MobSF JSON report missing"}), encoding="utf-8"
    )
    report = cdr.parse_mobsf(tmp_path / "mobsf-report.json")
    assert report.findings == []
    assert "MobSF JSON report missing" in report.note
