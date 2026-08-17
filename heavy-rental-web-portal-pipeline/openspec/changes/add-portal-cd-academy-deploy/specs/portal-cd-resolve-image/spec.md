# Delta for portal-cd-resolve-image

## ADDED Requirements

### Requirement: Pipeline chooses the portal image
On `action=deploy`, a `resolve-image` job SHALL set extra-vars for Ansible. It SHALL prefer a non-empty `image_http_url` input or Environment `IMAGE_HTTP_URL` for `docker load`. Otherwise it SHALL use `image_ref` or Environment `PORTAL_IMAGE` as a registry tag. It SHALL NOT run `docker build` or `npm run build`.

#### Scenario: Deploy with no image
- GIVEN `action=deploy`
- AND `image_http_url`, `IMAGE_HTTP_URL`, `image_ref`, and `PORTAL_IMAGE` are all empty
- WHEN resolve-image runs
- THEN the job fails
- AND it does not default to stock `nginx`

#### Scenario: HTTPS string in image_ref
- GIVEN `image_ref` starts with `http://` or `https://`
- WHEN resolve-image runs
- THEN the job fails telling the operator to use `image_http_url`

#### Scenario: Private GHCR
- GIVEN the chosen tag is `ghcr.io/…`
- AND an unauthenticated manifest/API request returns 401 or 403
- WHEN resolve-image runs
- THEN the job fails telling the operator to copy the image to ECR or pass a tar URL
- AND no GitHub PAT is written for the guest

#### Scenario: configure-only skips resolve
- GIVEN `action=configure-only` or `action=verify`
- WHEN the workflow runs
- THEN resolve-image does not run
