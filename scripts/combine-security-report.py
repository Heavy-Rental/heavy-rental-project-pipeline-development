#!/usr/bin/env python3
"""Combine SARIF 2.1.0 files (and optional pip-audit JSON) into one PDF.

Keep this file in sync with the heredoc in each Integration CI
``integration-pipeline.yml`` Security Testing job.

Code snippets from SARIF regions are never copied into the PDF (secret-scanner
hits can echo credentials).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
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
    "combined-security-report.pdf",
    "combine-security-report.py",
}


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


def result_level(result: dict, rules_by_id: dict) -> str:
    level = (result.get("level") or "").strip().lower()
    if level:
        return level
    rule_id = result.get("ruleId") or ""
    rule = rules_by_id.get(rule_id) or {}
    default = (rule.get("defaultConfiguration") or {}).get("level") or ""
    return (default or "warning").strip().lower()


def result_location(result: dict) -> str:
    locations = result.get("locations") or []
    if not locations or not isinstance(locations[0], dict):
        return "—"
    phys = locations[0].get("physicalLocation") or {}
    uri = ((phys.get("artifactLocation") or {}).get("uri")) or "—"
    region = phys.get("region") or {}
    line = region.get("startLine")
    if line:
        return f"{uri}:{line}"
    return str(uri)


def result_message(result: dict) -> str:
    message = result.get("message") or {}
    if isinstance(message, dict):
        return truncate(message.get("text") or message.get("markdown") or "")
    return truncate(str(message))


def parse_sarif(path: Path) -> ToolReport:
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError) as exc:
        return ToolReport(
            name=path.stem,
            source_file=path.name,
            present=True,
            note=f"Could not parse SARIF: {exc}",
        )
    findings: list[Finding] = []
    tool_names: list[str] = []
    for run in data.get("runs") or []:
        if not isinstance(run, dict):
            continue
        driver = ((run.get("tool") or {}).get("driver")) or {}
        name = driver.get("name") or path.stem
        tool_names.append(str(name))
        rules_by_id = {}
        for rule in driver.get("rules") or []:
            if isinstance(rule, dict) and rule.get("id"):
                rules_by_id[rule["id"]] = rule
        for result in run.get("results") or []:
            if not isinstance(result, dict):
                continue
            findings.append(
                Finding(
                    rule_id=str(result.get("ruleId") or "—"),
                    level=result_level(result, rules_by_id),
                    location=result_location(result),
                    message=result_message(result),
                )
            )
    display = tool_names[0] if len(set(tool_names)) == 1 else (tool_names[0] if tool_names else path.stem)
    if len(set(tool_names)) > 1:
        display = f"{display} (+{len(set(tool_names)) - 1} tools)"
    return ToolReport(name=str(display), source_file=path.name, present=True, findings=findings)


def _pip_audit_rows(data: object) -> list[dict]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        deps = data.get("dependencies")
        if isinstance(deps, list):
            return [row for row in deps if isinstance(row, dict)]
    return []


def parse_pip_audit(path: Path) -> ToolReport:
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError) as exc:
        return ToolReport(
            name="pip-audit",
            source_file=path.name,
            present=True,
            note=f"Could not parse pip-audit JSON: {exc}",
        )
    findings: list[Finding] = []
    for dep in _pip_audit_rows(data):
        pkg = dep.get("name") or "package"
        version = dep.get("version") or "?"
        for vuln in dep.get("vulns") or []:
            if not isinstance(vuln, dict):
                continue
            vuln_id = vuln.get("id") or "unspecified"
            fixes = vuln.get("fix_versions") or []
            if isinstance(fixes, list):
                fix_txt = ", ".join(str(v) for v in fixes) or "none listed"
            else:
                fix_txt = str(fixes)
            desc = truncate(vuln.get("description") or "")
            msg = f"{pkg} {version}; fix: {fix_txt}"
            if desc:
                msg = f"{msg}. {desc}"
            findings.append(
                Finding(
                    rule_id=str(vuln_id),
                    level="warning",
                    location=f"{pkg}=={version}",
                    message=truncate(msg),
                )
            )
    return ToolReport(name="pip-audit", source_file=path.name, present=True, findings=findings)


def collect_reports(input_dir: Path) -> list[ToolReport]:
    reports: list[ToolReport] = []
    if not input_dir.is_dir():
        return reports
    for path in sorted(input_dir.glob("*.sarif")):
        if path.name in SKIP_NAMES:
            continue
        reports.append(parse_sarif(path))
    pip_audit = input_dir / "pip-audit.json"
    if pip_audit.is_file():
        reports.append(parse_pip_audit(pip_audit))
    return reports


def level_counts(findings: list[Finding]) -> str:
    counts = Counter(f.level for f in findings)
    if not findings:
        return "0"
    order = ["error", "warning", "note", "none"]
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
            "Machine-readable reports remain SARIF 2.1.0. This PDF is a human download. "
            "Source snippets are omitted so secret-scanner matches are not echoed.",
            styles["Meta"],
        ),
        Spacer(1, 14),
        Paragraph("Summary", styles["Heading1"]),
    ]
    usable = 7.5 * inch
    if not reports:
        story.append(Paragraph("No scanner outputs were produced in security-reports/.", styles["Normal"]))
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
    canvas.drawString(0.75 * inch, 0.45 * inch, "Combined security report")
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
        author="Heavy Rental Integration CI",
    )
    doc.build(build_story(reports, args), onFirstPage=add_page_number, onLaterPages=add_page_number)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Combined security report")
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
