# Delta for mobile-ci-codeql

## Purpose

GitHub CodeQL analysis of the Android Kotlin/Java sources.

## ADDED Requirements

### Requirement: CodeQL needs Integration
CodeQL Analysis SHALL run only after Integration succeeds and SHALL analyze the same application source Integration resolved.

### Requirement: Java and Kotlin query suite
CodeQL SHALL initialize with language `java-kotlin` and query suite `security-and-quality`, using the application checkout as the source root.

#### Scenario: Language and suite
- GIVEN Integration succeeded
- WHEN CodeQL initializes
- THEN the language is `java-kotlin`
- AND the query suite is `security-and-quality`

### Requirement: Instrumented Gradle build
CodeQL SHALL build the debug variant with the Gradle wrapper (`:app:assembleDebug`, `--no-daemon`) so extraction covers compiled Kotlin.

#### Scenario: Build for analysis
- GIVEN CodeQL has initialized
- WHEN the build step runs
- THEN `./gradlew --no-daemon :app:assembleDebug` is invoked
- AND tests are not required for this build

### Requirement: Results in Code Scanning
CodeQL SHALL publish results to GitHub Code Scanning under a mobile-specific category.

#### Scenario: Category
- GIVEN analysis completes
- WHEN results are uploaded
- THEN the category identifies the mobile CI or release pipeline (not the REST API or portal categories)
