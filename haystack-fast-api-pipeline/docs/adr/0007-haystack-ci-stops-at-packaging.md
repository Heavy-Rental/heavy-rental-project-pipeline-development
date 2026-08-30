# ADR 0007: Haystack CI family does not compose onto guests

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-ci-pipeline`

## Context

The CI OpenSpec (`haystack-ci-scope`) forbids Terraform, rollout, and operate jobs in Fast Feedback / Integration / Release. Academy app CD later landed in the same authoring tree (`deploy-pipeline/`) as a **separate** family.

## Decision

CI workflows end at versioned wheel/sdist + image tar, then Release DAST and Publish (public GHCR + GitHub Release). They do not SSH, compose, or apply IaC. Deploy lives in the CD family ([ADR 0001](0001-haystack-cd-academy-only.md)). The Security Report pair summarizes existing Code Scanning alerts; it is not packaging, not a merge gate, and does not deploy.

## Consequences

- `haystack-ci-scope` stays historically correct for the three CI pipelines.
- Living docs must name both families; they must not say “deploy is another project” for the whole tree.
- Fast Feedback and Integration CI do not request `packages: write`.
