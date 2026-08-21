#!/usr/bin/env python3
"""Combine Release DAST tool outputs into one PDF.

Keep this file in sync with the heredoc in each Release CI
``release-pipeline.yml`` DAST job.

Supported inputs (all optional):
  - zap.json (OWASP ZAP baseline)
  - dastardly-report.xml (Dastardly JUnit XML)
  - nuclei.jsonl (Nuclei)
  - mobsf-report.json (MobSF)

Request bodies, ZAP evidence, and SARIF-style snippets are never copied
into the PDF (scanner hits can echo credentials).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

MAX_MESSAGE = 400
MAX_FINDINGS_PER_TOOL = 200
SKIP_NAMES = {
    "combined-dast-report.pdf",
    "combine-dast-report.py",
    "INDEX.md",
    "zap.html",
    "zap.md",
    "mobsf-upload.json",
    "mobsf-scan.json",
    "mobsf-report.pdf",
}
HTML_TAG_RE = re.compile(r"<[^>]+>")
ZAP_RISK = {"0": "info", "1": "low", "2": "medium", "3": "high", "4": "critical"}


@dataclass
class Finding:
    rule_id: str
    level: str
    location: str
    message: str


@dataclass
class ToolReport:
    name: str
    source_file: str
    present: bool
    findings: list[Finding] = field(default_factory=list)
    note: str = ""


def pdf_safe(text: str) -> str:
    raw = "" if text is None else str(text)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = raw.encode("latin-1", "replace").decode("latin-1")
    return xml_escape(raw)


def truncate(text: str, limit: int = MAX_MESSAGE) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def strip_html(text: str) -> str:
    return HTML_TAG_RE.sub(" ", text or "")


def _unreadable(path: Path, name: str, exc: Exception) -> ToolReport:
    return ToolReport(
        name=name,
        source_file=path.name,
        present=True,
        note=f"Could not parse {path.name}: {exc}",
    )


def _placeholder_note(path: Path, prefix: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    stripped = text.strip()
    if stripped.startswith(prefix) or stripped.startswith("ZAP did not write"):
        return truncate(stripped, 200)
    return None


def parse_zap(path: Path) -> ToolReport:
    note = _placeholder_note(path, "ZAP did not write")
    if note:
        return ToolReport(name="OWASP ZAP", source_file=path.name, present=True, note=note)
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError) as exc:
        return _unreadable(path, "OWASP ZAP", exc)
    if not isinstance(data, dict):
        return ToolReport(
            name="OWASP ZAP",
            source_file=path.name,
            present=True,
            note="ZAP JSON was not an object.",
        )
    findings: list[Finding] = []
    for site in data.get("site") or []:
        if not isinstance(site, dict):
            continue
        site_name = site.get("@name") or site.get("name") or ""
        for alert in site.get("alerts") or []:
            if not isinstance(alert, dict):
                continue
            riskcode = str(alert.get("riskcode") or "")
            level = (alert.get("riskdesc") or ZAP_RISK.get(riskcode) or "warning").split()[0].lower()
            name = alert.get("alert") or alert.get("name") or "alert"
            instances = alert.get("instances") or []
            uri = site_name or "—"
            if instances and isinstance(instances[0], dict):
                uri = instances[0].get("uri") or uri
            desc = truncate(strip_html(str(alert.get("desc") or "")))
            findings.append(
                Finding(
                    rule_id=str(alert.get("pluginid") or alert.get("alertRef") or name),
                    level=level or "warning",
                    location=str(uri),
                    message=desc or truncate(str(name)),
                )
            )
    return ToolReport(name="OWASP ZAP", source_file=path.name, present=True, findings=findings)


def parse_dastardly(path: Path) -> ToolReport:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return _unreadable(path, "Dastardly", exc)
    stripped = text.strip()
    if stripped in {"<testsuites name=\"dastardly\"/>", "<testsuites name='dastardly'/>"}:
        return ToolReport(
            name="Dastardly",
            source_file=path.name,
            present=True,
            note="Placeholder empty Dastardly report (scanner did not write XML).",
        )
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        return _unreadable(path, "Dastardly", exc)
    findings: list[Finding] = []
    for case in root.iter("testcase"):
        name = case.get("name") or case.get("classname") or "testcase"
        location = case.get("classname") or "—"
        for child in list(case):
            tag = child.tag.split("}", 1)[-1]
            if tag not in {"failure", "error"}:
                continue
            msg = child.get("message") or ""
            findings.append(
                Finding(
                    rule_id=str(name),
                    level="high" if tag == "failure" else "error",
                    location=str(location),
                    message=truncate(msg or (child.text or tag)),
                )
            )
    return ToolReport(name="Dastardly", source_file=path.name, present=True, findings=findings)


def parse_nuclei(path: Path) -> ToolReport:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return _unreadable(path, "Nuclei", exc)
    findings: list[Finding] = []
    notes: list[str] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            notes.append(f"line {line_no}: {exc}")
            continue
        if not isinstance(row, dict):
            continue
        info = row.get("info") if isinstance(row.get("info"), dict) else {}
        name = info.get("name") or row.get("template-id") or row.get("template_id") or "nuclei"
        level = str(info.get("severity") or "info").lower()
        location = str(row.get("matched-at") or row.get("matched_at") or row.get("host") or "—")
        desc = info.get("description") or name
        findings.append(
            Finding(
                rule_id=str(row.get("template-id") or row.get("template_id") or name),
                level=level,
                location=location,
                message=truncate(str(desc)),
            )
        )
    note = ""
    if notes:
        note = truncate("; ".join(notes[:5]))
    return ToolReport(
        name="Nuclei",
        source_file=path.name,
        present=True,
        findings=findings,
        note=note,
    )


def _mobsf_finding(rule_id: str, level: str, location: str, message: str) -> Finding:
    return Finding(
        rule_id=truncate(str(rule_id), 80),
        level=(level or "warning").lower(),
        location=truncate(str(location or "—"), 120),
        message=truncate(str(message)),
    )


def _walk_mobsf_list(items: object, default_level: str, location: str) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(items, list):
        return findings
    for item in items:
        if isinstance(item, str):
            findings.append(_mobsf_finding(item, default_level, location, item))
        elif isinstance(item, (list, tuple)) and item:
            level = default_level
            msg = item[-1] if len(item) > 1 else item[0]
            if len(item) >= 2 and isinstance(item[0], str):
                level = str(item[0])
            rule = item[1] if len(item) > 1 else item[0]
            findings.append(_mobsf_finding(str(rule), level, location, str(msg)))
        elif isinstance(item, dict):
            level = str(
                item.get("severity")
                or item.get("level")
                or item.get("stat")
                or default_level
            )
            title = item.get("title") or item.get("rule") or item.get("name") or "finding"
            desc = item.get("description") or item.get("desc") or title
            loc = item.get("file") or item.get("path") or location
            findings.append(_mobsf_finding(str(title), level, str(loc), str(desc)))
    return findings


def parse_mobsf(path: Path) -> ToolReport:
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError) as exc:
        return _unreadable(path, "MobSF", exc)
    if not isinstance(data, dict):
        return ToolReport(
            name="MobSF",
            source_file=path.name,
            present=True,
            note="MobSF JSON was not an object.",
        )
    if data.get("error") and len(data) <= 2:
        return ToolReport(
            name="MobSF",
            source_file=path.name,
            present=True,
            note=truncate(str(data.get("error"))),
        )
    findings: list[Finding] = []
    for key, level in (("high", "high"), ("warning", "warning"), ("info", "info")):
        findings.extend(_walk_mobsf_list(data.get(key), level, key))
    cert = data.get("certificate_analysis")
    if isinstance(cert, dict):
        findings.extend(
            _walk_mobsf_list(cert.get("certificate_findings"), "warning", "certificate")
        )
    manifest = data.get("manifest_analysis")
    if isinstance(manifest, dict):
        findings.extend(
            _walk_mobsf_list(manifest.get("manifest_findings"), "warning", "manifest")
        )
    network = data.get("network_security")
    if isinstance(network, dict):
        findings.extend(
            _walk_mobsf_list(network.get("network_findings"), "warning", "network")
        )
    code = data.get("code_analysis")
    if isinstance(code, dict):
        code_findings = code.get("findings")
        if isinstance(code_findings, dict):
            for rule_id, body in code_findings.items():
                if not isinstance(body, dict):
                    continue
                meta = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}
                level = str(meta.get("severity") or "info")
                desc = meta.get("description") or rule_id
                files = body.get("files")
                loc = "code"
                if isinstance(files, dict) and files:
                    loc = next(iter(files))
                findings.append(_mobsf_finding(str(rule_id), level, str(loc), str(desc)))
    return ToolReport(name="MobSF", source_file=path.name, present=True, findings=findings)


PARSERS = {
    "zap.json": parse_zap,
    "dastardly-report.xml": parse_dastardly,
    "nuclei.jsonl": parse_nuclei,
    "mobsf-report.json": parse_mobsf,
}


def collect_reports(input_dir: Path) -> list[ToolReport]:
    reports: list[ToolReport] = []
    if not input_dir.is_dir():
        return reports
    for filename, parser in PARSERS.items():
        path = input_dir / filename
        if path.is_file():
            reports.append(parser(path))
    return reports


def level_counts(findings: list[Finding]) -> str:
    counts = Counter(f.level for f in findings)
    if not findings:
        return "0"
    order = ["critical", "high", "medium", "low", "error", "warning", "info", "note", "none"]
    parts = [f"{lvl}={counts[lvl]}" for lvl in order if counts.get(lvl)]
    extra = sorted(k for k in counts if k not in order)
    parts.extend(f"{lvl}={counts[lvl]}" for lvl in extra)
    return f"{len(findings)} ({', '.join(parts)})"


def _styles() -> dict:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#333333"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CellHead",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
        )
    )
    return styles


def _table(rows: list[list], col_widths: list[float]) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_story(reports: list[ToolReport], args: argparse.Namespace) -> list:
    styles = _styles()
    cell, head = styles["Cell"], styles["CellHead"]
    story: list = [
        Paragraph(pdf_safe(args.title), styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"<b>Repository:</b> {pdf_safe(args.repo)}", styles["Meta"]),
        Paragraph(f"<b>Commit:</b> {pdf_safe(args.sha)}", styles["Meta"]),
        Paragraph(f"<b>Workflow run:</b> {pdf_safe(args.run_url)}", styles["Meta"]),
        Paragraph(
            f"<b>Generated (UTC):</b> {pdf_safe(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ'))}",
            styles["Meta"],
        ),
        Paragraph(
            "Machine-readable DAST outputs remain in this artifact (ZAP JSON/HTML, "
            "Dastardly XML, Nuclei JSONL, MobSF JSON). This PDF is a human download. "
            "Request bodies and scanner evidence snippets are omitted.",
            styles["Meta"],
        ),
        Spacer(1, 14),
        Paragraph("Summary", styles["Heading1"]),
    ]
    usable = 7.5 * inch
    if not reports:
        story.append(Paragraph("No DAST scanner outputs were produced in dast-reports/.", styles["Normal"]))
        return story

    summary_rows = [[
        Paragraph("Tool", head),
        Paragraph("File", head),
        Paragraph("Present", head),
        Paragraph("Findings", head),
    ]]
    for report in reports:
        summary_rows.append([
            Paragraph(pdf_safe(report.name), cell),
            Paragraph(pdf_safe(report.source_file), cell),
            Paragraph("yes" if report.present else "no", cell),
            Paragraph(pdf_safe(level_counts(report.findings)), cell),
        ])
    story.append(_table(summary_rows, [1.6 * inch, 2.0 * inch, 0.8 * inch, usable - 4.4 * inch]))
    story.append(Spacer(1, 12))

    for index, report in enumerate(reports):
        if index:
            story.append(PageBreak())
        story.append(Paragraph(pdf_safe(f"{report.name} ({report.source_file})"), styles["Heading1"]))
        if report.note:
            story.append(Paragraph(pdf_safe(report.note), styles["Normal"]))
        if not report.findings:
            story.append(Paragraph("No findings in this report.", styles["Normal"]))
            continue
        shown = report.findings[:MAX_FINDINGS_PER_TOOL]
        omitted = len(report.findings) - len(shown)
        rows = [[
            Paragraph("Level", head),
            Paragraph("Rule", head),
            Paragraph("Location", head),
            Paragraph("Message", head),
        ]]
        for finding in shown:
            rows.append([
                Paragraph(pdf_safe(finding.level), cell),
                Paragraph(pdf_safe(finding.rule_id), cell),
                Paragraph(pdf_safe(finding.location), cell),
                Paragraph(pdf_safe(finding.message).replace("\n", "<br/>"), cell),
            ])
        story.append(
            _table(rows, [0.8 * inch, 1.6 * inch, 2.0 * inch, usable - 4.4 * inch])
        )
        if omitted > 0:
            story.append(Spacer(1, 6))
            story.append(
                Paragraph(pdf_safe(f"… and {omitted} more finding(s) not listed."), styles["Meta"])
            )
    return story


def add_page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "Combined DAST report")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def write_pdf(reports: list[ToolReport], args: argparse.Namespace) -> None:
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=args.title,
        author="Heavy Rental Release CI",
    )
    doc.build(build_story(reports, args), onFirstPage=add_page_number, onLaterPages=add_page_number)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Combined DAST report")
    parser.add_argument("--repo", default="")
    parser.add_argument("--sha", default="")
    parser.add_argument("--run-url", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reports = collect_reports(Path(args.input_dir))
    write_pdf(reports, args)
    output = Path(args.output)
    if not output.is_file() or output.stat().st_size == 0:
        print(f"error: PDF was not written: {output}", file=sys.stderr)
        return 1
    print(f"Wrote {output} ({output.stat().st_size} bytes, {len(reports)} report(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
