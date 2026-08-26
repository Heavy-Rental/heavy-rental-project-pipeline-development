# Delta for rest-ci-codeql

## Purpose

GitHub CodeQL analysis for the Java / Spring REST API.

## ADDED Requirements

### Requirement: CodeQL needs Integration
CodeQL Analysis SHALL run only after Integration Check succeeds and SHALL analyze the same application source.

### Requirement: Language is java-kotlin
CodeQL SHALL initialize with language `java-kotlin` and SHALL run a security-and-quality query suite.

#### Scenario: Java analysis
- GIVEN Integration Check succeeded
- WHEN CodeQL Analysis runs
- THEN CodeQL is initialized for `java-kotlin`
- AND the analyze step uploads results to GitHub Code Scanning

### Requirement: No packaging
CodeQL SHALL NOT produce a WAR or Docker image.

#### Scenario: No packaging job dependency
- GIVEN Integration CI (not Release)
- WHEN CodeQL finishes
- THEN Packaging is not part of this workflow
