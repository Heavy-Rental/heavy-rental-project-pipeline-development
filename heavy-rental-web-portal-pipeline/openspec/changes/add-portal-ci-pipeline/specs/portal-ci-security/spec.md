# Delta for portal-ci-security

## Purpose

Static and supply-chain scanning of the TypeScript / React application. Standard report format is SARIF 2.1.0.

## ADDED Requirements

### Requirement: Security Testing needs Integration
Security Testing SHALL run only after Integration succeeds, in parallel with Quality Control.

### Requirement: Semgrep TypeScript / React SAST
Security Testing SHALL run Semgrep with TypeScript, React, JavaScript, Node.js, OWASP Top Ten, security-audit, secrets, CWE Top 25, Gitleaks, SQL injection, JWT, and insecure-transport rulesets, plus custom ERROR-severity rules that flag hard-coded credentials in `.env`/properties/YAML and hard-coded secret assignments in JavaScript/TypeScript. It SHALL always attempt to write `semgrep.sarif`, `semgrep.json`, and `semgrep.txt` covering all severities (not only ERROR). It SHALL fail the job only when ERROR-severity findings exist.

#### Scenario: ERROR findings fail the job
- GIVEN Semgrep reports at least one ERROR-severity finding
- WHEN the Semgrep gate runs
- THEN the job fails
- AND `semgrep.sarif`, `semgrep.json`, and `semgrep.txt` are still uploaded when present

#### Scenario: plaintext password in env or properties
- GIVEN a production `.env` or properties file contains `password=` / `secret=` / `api-key=` with a literal value (not `${ENV}`)
- WHEN Semgrep SAST runs
- THEN the finding is ERROR severity
- AND the Semgrep gate fails

### Requirement: npm audit report
Security Testing SHALL run npm audit and convert the JSON to SARIF when conversion is implemented. An audit finding SHALL NOT by itself replace the Trivy CRITICAL gate.

### Requirement: Trivy filesystem scan
Security Testing SHALL write `trivy-fs.sarif` and fail only on unfixed CRITICAL vulnerabilities.

#### Scenario: HIGH does not fail the gate
- GIVEN Trivy finds unfixed HIGH but no unfixed CRITICAL issues
- WHEN the Trivy CRITICAL gate runs
- THEN the job succeeds

### Requirement: Combined security report PDF
Security Testing SHALL combine present scanner outputs under `security-reports/` (all `*.sarif` files, including npm-audit SARIF) into `security-reports/combined-security-report.pdf` after the scanners finish, including when a scanner gate has failed. The PDF SHALL be uploaded as workflow artifact `security-combined-report-pdf` and included in the existing SARIF artifact when present. SARIF 2.1.0 remains the machine-readable standard. The PDF SHALL omit SARIF region snippets so secret-scanner matches are not echoed. On `pull_request`, Security Testing SHALL publish a Checks-tab download link (Security Testing job summary and a completed check named `Security combined report (PDF)`). A Checks API failure SHALL NOT fail the job.

#### Scenario: PDF on clean scan
- GIVEN scanners write at least one SARIF file and no gate fails
- WHEN Security Testing finishes
- THEN `security-reports/combined-security-report.pdf` exists
- AND artifact `security-combined-report-pdf` is uploaded

#### Scenario: PDF when a gate fails
- GIVEN a Semgrep ERROR, npm audit high/critical, or Trivy CRITICAL gate fails
- WHEN Security Testing finishes
- THEN `combined-security-report.pdf` is still uploaded when the file was produced

#### Scenario: downloadable from pull request Checks
- GIVEN the workflow ran on `pull_request`
- AND the combined PDF artifact was uploaded
- WHEN Checks are shown for the pull request
- THEN the Security Testing job summary includes a download link
- AND a check named `Security combined report (PDF)` is created when the Checks API accepts the request

### Requirement: Publish SARIF
Security Testing SHALL upload Semgrep SARIF/JSON/text, Trivy SARIF, and npm-audit SARIF files when present. A Code Scanning upload failure SHALL NOT fail the job.
