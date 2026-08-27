# Delta for rest-cd-verify

## ADDED Requirements

### Requirement: SSM health on REST :8080
After discover (and after ansible-rest when that job ran), `action=verify`, `deploy`, and `configure-only` SHALL prove Tomcat on each InService + SSM Online `asg-rest` guest with SSM `GET http://127.0.0.1:8080/actuator/health`. Accept HTTP **2xx only** (same as ALB `tg-rest` matcher `200-299` on `<instance>:8080/actuator/health`). 401/403 (Spring Security on `GET /`) SHALL NOT count as healthy.

#### Scenario: Tomcat answers
- GIVEN at least one guest returns HTTP 2xx on `:8080/actuator/health`
- WHEN verify runs
- THEN the job succeeds
- AND a failing Haystack (`HAYSTACK_BASE_URL`) SHALL NOT fail this job by itself

#### Scenario: No Tomcat
- GIVEN every guest fails `:8080/actuator/health` with a non-2xx status (including 401) or SSM command execution fails
- WHEN verify runs
- THEN the job fails

#### Scenario: Summary is safe
- GIVEN verify runs
- THEN the step summary may show guest **counts**
- AND it SHALL NOT print instance IPs or `REST_BASE_URL`
