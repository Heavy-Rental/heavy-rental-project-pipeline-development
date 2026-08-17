# Delta for portal-cd-verify

## ADDED Requirements

### Requirement: SSM health on portal :80
After discover (and after ansible-portal when that job ran), `action=verify`, `deploy`, and `configure-only` SHALL prove nginx on each InService + SSM Online `asg-portal` guest with SSM `GET http://127.0.0.1/` accepting HTTP 200–302.

#### Scenario: Nginx answers
- GIVEN at least one guest returns 200, 301, or 302 for `/`
- WHEN verify runs
- THEN the job succeeds
- AND a failing `/api` (REST) SHALL NOT fail this job by itself

#### Scenario: No nginx
- GIVEN every guest fails `GET /` or SSM command execution fails
- WHEN verify runs
- THEN the job fails

#### Scenario: Summary is public-only
- GIVEN verify runs
- THEN the step summary MAY print public portal ALB DNS
- AND it SHALL NOT print instance IPs or `REST_BASE_URL`
