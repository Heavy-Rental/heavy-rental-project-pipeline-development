# Delta for haystack-cd-discover

## ADDED Requirements

### Requirement: Discover asg-haystack without instance inputs
After a live Vocareum session, the workflow SHALL list InService instances on `asg-haystack` that are SSM Online. It SHALL `describe-secret` `heavy-rental/haystack` without echoing SecretString. The Run form SHALL NOT ask for instance IDs, private IPs, or SSH hosts.

#### Scenario: No healthy guest
- GIVEN the ASG is missing, desired=0, or no instance is SSM Online
- WHEN discover runs
- THEN the job fails telling the operator to run infra apply / Start Lab / infra configure-only

#### Scenario: Summary is safe
- GIVEN discover succeeds
- THEN the step summary may show instance **count**
- AND it does not print instance IPs, SecretString, or the internal Haystack ALB URL
