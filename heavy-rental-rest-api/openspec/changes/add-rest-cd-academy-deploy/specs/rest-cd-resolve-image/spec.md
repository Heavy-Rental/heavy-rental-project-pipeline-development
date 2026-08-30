# Delta for rest-cd-resolve-image

## ADDED Requirements

### Requirement: Pipeline chooses the REST image
On `action=deploy`, a `resolve-image` job SHALL set extra-vars for Ansible. It SHALL require a non-empty compose tag from `image_ref` or Environment `REST_IMAGE`. A non-empty `image_http_url` input or Environment `IMAGE_HTTP_URL` SHALL be passed through for `docker load` and SHALL NOT replace the compose tag. It SHALL NOT run `docker build` or Maven.

#### Scenario: Deploy with no image
- GIVEN `action=deploy`
- AND `image_ref` and `REST_IMAGE` are both empty
- WHEN resolve-image runs
- THEN the job fails
- AND it does not invent a stock Tomcat tag
- AND a tar URL alone does not satisfy the compose tag

#### Scenario: Tar without a compose tag
- GIVEN `action=deploy`
- AND `image_http_url` or `IMAGE_HTTP_URL` is set
- AND `image_ref` and `REST_IMAGE` are both empty
- WHEN resolve-image runs
- THEN the job fails telling the operator that `docker load` still needs a compose tag

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
