# Delta for haystack-ci-codeql

## Purpose

GitHub CodeQL analysis of the FastAPI + Haystack Python sources.

## ADDED Requirements

### Requirement: CodeQL needs Integration
CodeQL Analysis SHALL run only after Integration succeeds and SHALL analyze the same application source Integration resolved.

### Requirement: Python query suite
CodeQL SHALL initialize with language `python` and query suite `security-and-quality`, using the application checkout as the source root. It SHALL NOT initialize Java, Kotlin, or JavaScript.

#### Scenario: Language and suite
- GIVEN Integration succeeded
- WHEN CodeQL initializes
- THEN the language is `python`
- AND the query suite is `security-and-quality`

### Requirement: Autobuild is sufficient
CodeQL SHALL use the default Python autobuild (or no custom compile). It SHALL NOT invoke Gradle, Maven, or npm.

#### Scenario: No JVM build
- GIVEN CodeQL has initialized
- WHEN analysis runs
- THEN no `gradlew` or `mvn` command is invoked

### Requirement: Results in Code Scanning
CodeQL SHALL publish results to GitHub Code Scanning under a haystack-specific category.

#### Scenario: Category
- GIVEN analysis completes
- WHEN results are uploaded
- THEN the category identifies the haystack CI or release pipeline (not the REST API, portal, or mobile categories)
