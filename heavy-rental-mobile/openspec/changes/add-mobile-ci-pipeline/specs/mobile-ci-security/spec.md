# Delta for mobile-ci-security

## Purpose

Static and supply-chain scanning of the Android application. Standard report format is SARIF 2.1.0.

## ADDED Requirements

### Requirement: Security Testing needs Integration
Security Testing SHALL run only after Integration succeeds, in parallel with Quality Control, and SHALL scan the same application source.

### Requirement: Semgrep SAST
Security Testing SHALL run Semgrep with Kotlin, Java, OWASP Top Ten, security-audit, and secrets rulesets. It SHALL always attempt to write `semgrep.sarif`. It SHALL fail the job only when ERROR-severity findings exist (or Semgrep cannot complete the gate scan).

#### Scenario: SARIF written on clean scan
- GIVEN Semgrep finds no ERROR-severity issues
- WHEN Security Testing runs
- THEN `security-reports/semgrep.sarif` exists
- AND the Semgrep gate step succeeds

#### Scenario: ERROR findings fail the job
- GIVEN Semgrep reports at least one ERROR-severity finding
- WHEN the Semgrep gate runs
- THEN the job fails
- AND the SARIF file is still uploaded when present

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

### Requirement: Publish SARIF
Security Testing SHALL upload Semgrep and Trivy SARIF files as a workflow artifact and SHALL attempt to publish them to GitHub Code Scanning. A Code Scanning upload failure SHALL NOT fail the job.

#### Scenario: Code Scanning optional
- GIVEN SARIF files exist and the Code Scanning API rejects the upload
- WHEN the upload step runs
- THEN the Security Testing job can still succeed if Semgrep and Trivy gates passed
