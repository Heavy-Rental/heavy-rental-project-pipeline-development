# Delta for haystack-cd-resolve-image

## ADDED Requirements

### Requirement: Pipeline chooses the Haystack image
On `action=deploy`, `resolve-image` SHALL set extra-vars. Prefer `image_http_url` / `IMAGE_HTTP_URL` for `docker load`. Otherwise `image_ref` or Environment `HAYSTACK_IMAGE`. SHALL NOT `docker build` or `uv build`.

#### Scenario: Deploy with no image
- GIVEN `action=deploy` and all image fields empty
- WHEN resolve-image runs
- THEN the job fails (no stock uvicorn)

#### Scenario: Private GHCR
- GIVEN a `ghcr.io/…` tag returns 401 or 403 unauthenticated
- THEN the job fails (copy to ECR or use a tar). No PAT on the guest.

#### Scenario: configure-only skips resolve
- GIVEN `action=configure-only` or `verify`
- THEN resolve-image does not run
