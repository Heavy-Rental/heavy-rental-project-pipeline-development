# Delta for haystack-ci-security

## Purpose

Static and supply-chain scanning of the Python + Haystack application. Standard report format is SARIF 2.1.0. Python-specific SCA is reported with pip-audit; the fail gate remains Trivy CRITICAL.

## ADDED Requirements

### Requirement: Security Testing needs Integration
Security Testing SHALL run only after Integration succeeds, in parallel with Quality Control, and SHALL scan the same application source.

### Requirement: Semgrep Python SAST
Security Testing SHALL run two Semgrep passes. The application pass SHALL use Python, FastAPI, OWASP Top Ten, security-audit, secrets, CWE Top 25, Gitleaks, SQL injection, JWT, and insecure-transport rulesets, plus custom ERROR-severity rules that flag hard-coded credentials in `.env`/properties/YAML and hard-coded password/secret assignments in Python. The application pass SHALL exclude `.github/**` so `p/secrets` and `p/gitleaks` do not flag reusable-workflow secrets-context maps. The GitHub Actions pass SHALL scan `.github/**` with `p/github-actions` plus custom rules that flag `secrets: inherit` (ERROR, except `haystack-cd-paid-caller.yml`) and hard-coded workflow credentials, and SHALL allow explicit GitHub secrets-context maps and `persist-credentials`. It SHALL always attempt to write `semgrep.sarif` and `semgrep-gha.sarif` covering all severities (not only ERROR). It SHALL fail the job only when ERROR-severity findings exist on either pass (or Semgrep cannot complete the gate scan). It SHALL NOT use Kotlin or Java rulesets.

#### Scenario: SARIF written on clean scan
- GIVEN Semgrep finds no ERROR-severity issues
- WHEN Security Testing runs
- THEN `security-reports/semgrep.sarif` exists
- AND `security-reports/semgrep-gha.sarif` exists
- AND the Semgrep gate step succeeds

#### Scenario: explicit secrets map is not a finding
- GIVEN a workflow maps a secret with `${{ secrets.NAME }}`
- WHEN the GitHub Actions Semgrep pass runs
- THEN that mapping is not an ERROR finding
- AND `secrets: inherit` in a CI caller would be an ERROR finding

#### Scenario: persist-credentials is not a finding
- GIVEN a workflow sets `persist-credentials: false` on `actions/checkout`
- WHEN either Semgrep pass runs
- THEN that key is not an ERROR finding

#### Scenario: full report when ERROR gate fails
- GIVEN Semgrep reports at least one ERROR-severity finding
- WHEN the Semgrep gate fails
- THEN `semgrep.sarif` is still uploaded when present

#### Scenario: ERROR findings fail the job
- GIVEN Semgrep reports at least one ERROR-severity finding
- WHEN the Semgrep gate runs
- THEN the job fails
- AND the SARIF file is still uploaded when present

#### Scenario: plaintext password in env or Python
- GIVEN `.env` contains `password=` with a literal value, or Python assigns `password = "..."` in non-test source
- WHEN Semgrep SAST runs
- THEN the finding is ERROR severity
- AND the Semgrep gate fails

### Requirement: pip-audit lockfile report
Security Testing SHALL export the frozen production lock with uv and run `pip-audit` against that export. A pip-audit finding SHALL NOT fail the job in this change (report only). The report SHALL be uploaded when present.

#### Scenario: Report is written
- GIVEN Security Testing reaches the pip-audit step
- WHEN `uvx pip-audit` finishes
- THEN `security-reports/pip-audit.json` is uploaded when the file exists
- AND a non-zero pip-audit exit does not fail Security Testing by itself

### Requirement: Trivy filesystem scan
Security Testing SHALL run Trivy filesystem scanning for HIGH and CRITICAL vulnerabilities, write `trivy-fs.sarif`, print a table, and fail only on unfixed CRITICAL vulnerabilities.

#### Scenario: HIGH does not fail the gate
- GIVEN Trivy finds unfixed HIGH but no unfixed CRITICAL issues
- WHEN the Trivy CRITICAL gate runs
- THEN the job succeeds
- AND `trivy-fs.sarif` is uploaded

#### Scenario: CRITICAL unfixed fails the job
- GIVEN Trivy finds an unfixed CRITICAL vulnerability
- WHEN the Trivy CRITICAL gate runs
- THEN the job fails

### Requirement: Combined security report PDF
Security Testing SHALL combine present scanner outputs under `security-reports/` (all `*.sarif` files and `pip-audit.json` when present) into `security-reports/combined-security-report.pdf` after the scanners finish, including when a scanner gate has failed. The PDF SHALL be uploaded as workflow artifact `security-combined-report-pdf` and included in the existing SARIF artifact when present. SARIF 2.1.0 remains the machine-readable standard. The PDF SHALL omit SARIF region snippets so secret-scanner matches are not echoed. On `pull_request`, Security Testing SHALL publish a Checks-tab download link (Security Testing job summary and a completed check named `Security combined report (PDF)`). A Checks API failure SHALL NOT fail the job.

#### Scenario: PDF on clean scan
- GIVEN scanners write at least one SARIF file and no gate fails
- WHEN Security Testing finishes
- THEN `security-reports/combined-security-report.pdf` exists
- AND artifact `security-combined-report-pdf` is uploaded

#### Scenario: PDF includes pip-audit
- GIVEN `security-reports/pip-audit.json` exists
- WHEN the combined PDF is written
- THEN the PDF includes a pip-audit section

#### Scenario: PDF when a gate fails
- GIVEN a Semgrep ERROR or Trivy CRITICAL gate fails
- WHEN Security Testing finishes
- THEN `combined-security-report.pdf` is still uploaded when the file was produced

#### Scenario: downloadable from pull request Checks
- GIVEN the workflow ran on `pull_request`
- AND the combined PDF artifact was uploaded
- WHEN Checks are shown for the pull request
- THEN the Security Testing job summary includes a download link
- AND a check named `Security combined report (PDF)` is created when the Checks API accepts the request

### Requirement: Publish SARIF
Security Testing SHALL upload Semgrep SARIF/JSON/text and Trivy SARIF files as a workflow artifact and SHALL attempt to publish SARIF to GitHub Code Scanning. A Code Scanning upload failure SHALL NOT fail the job.

#### Scenario: Code Scanning optional
- GIVEN SARIF files exist and the Code Scanning API rejects the upload
- WHEN the upload step runs
- THEN the Security Testing job can still succeed if Semgrep and Trivy gates passed
