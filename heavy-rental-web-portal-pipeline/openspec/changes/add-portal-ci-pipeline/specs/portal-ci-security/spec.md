# Delta for portal-ci-security

## Purpose

Static and supply-chain scanning of the TypeScript / React application. Standard report format is SARIF 2.1.0.

## ADDED Requirements

### Requirement: Security Testing needs Integration
Security Testing SHALL run only after Integration succeeds, in parallel with Quality Control.

### Requirement: Semgrep TypeScript / React SAST
Security Testing SHALL run Semgrep with TypeScript, React, JavaScript, Node.js, OWASP Top Ten, security-audit, secrets, CWE Top 25, Gitleaks, SQL injection, JWT, and insecure-transport rulesets, plus custom ERROR-severity rules that flag hard-coded credentials in `.env`/properties/YAML and hard-coded secret assignments in JavaScript/TypeScript. It SHALL always attempt to write `semgrep.sarif`. It SHALL fail the job only when ERROR-severity findings exist.

#### Scenario: ERROR findings fail the job
- GIVEN Semgrep reports at least one ERROR-severity finding
- WHEN the Semgrep gate runs
- THEN the job fails
- AND the SARIF file is still uploaded when present

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

### Requirement: Publish SARIF
Security Testing SHALL upload Semgrep, Trivy, and npm-audit SARIF files when present. A Code Scanning upload failure SHALL NOT fail the job.
