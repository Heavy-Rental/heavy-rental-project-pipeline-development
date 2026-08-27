# Delta for haystack-cd-verify

## ADDED Requirements

### Requirement: SSM health on Haystack :8000
Verify SHALL SSM `GET http://127.0.0.1:8000/health` and accept HTTP **2xx only** (same as ALB `tg-haystack` matcher `200-299` on `<instance>:8000/health`). `GET /docs` and `GET /` SHALL NOT count as healthy for this check.

#### Scenario: uvicorn answers
- THEN the job succeeds even if SoR RDS or Bolt is down
- AND the job succeeds even if `postgres-haystack-sync` or `neo4j-populate` crash (modules not in the current app image)

#### Scenario: Summary is safe
- THEN no instance IPs or internal ALB DNS
