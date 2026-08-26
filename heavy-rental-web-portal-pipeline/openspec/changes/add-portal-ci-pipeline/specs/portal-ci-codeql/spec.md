# Delta for portal-ci-codeql

## Purpose

GitHub CodeQL analysis for the JavaScript / TypeScript portal.

## ADDED Requirements

### Requirement: CodeQL needs Integration
CodeQL Analysis SHALL run only after Integration Check succeeds and SHALL analyze the same application source.

### Requirement: Language is javascript-typescript
CodeQL SHALL initialize with language `javascript-typescript`.

#### Scenario: JS/TS analysis
- GIVEN Integration succeeded
- WHEN CodeQL Analysis runs
- THEN CodeQL is initialized for `javascript-typescript`
- AND the analyze step uploads results to GitHub Code Scanning

### Requirement: No packaging
CodeQL SHALL NOT produce a `dist/` zip or Docker image on Integration CI.
