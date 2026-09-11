# Operations and Support Runbook

## Service indicators

- Request count by endpoint and decision
- p50/p95/p99 latency
- Finding count by category and severity
- LLM provider/fallback rate
- HTTP 4xx/5xx rate
- Model promotion approvals/rejections
- SQLite availability and disk growth

## Suggested initial objectives

These are pilot targets, not measured production commitments:

- 99.5% monthly API availability
- p95 deterministic assurance latency under 250 ms
- zero raw prompts, generated code, secrets, or PII in audit records
- 100% of external actions blocked pending explicit approval
- 100% of model releases pass configured non-regression gates

## Alerts

- 5xx rate above 2% for 10 minutes
- p95 latency above the agreed endpoint threshold
- provider fallback rate above 20% for 15 minutes
- any secret-exposure or prompt-injection critical finding
- failed database writes or disk use above 80%

## Incident response

1. Identify affected version, endpoint, provider, and request IDs.
2. Disable external actions or provider access if confidentiality is at risk.
3. Preserve metadata-only audit evidence; do not copy sensitive payloads to tickets.
4. Roll back the application, prompt, policy, or model to the last approved version.
5. Rotate any potentially exposed credential.
6. Add the failure to the regression set and document root cause/corrective action.

## Deployment

1. Run tests, compilation, JavaScript syntax check, and dependency audit.
2. Build the immutable non-root container.
3. Deploy to staging with synthetic/non-sensitive data.
4. Run health, assurance, critique, promotion, metrics, and audit smoke tests.
5. Release through canary/rolling deployment.
6. Observe errors, latency, provider behavior, and decisions.
7. Roll back if an SLO or safety gate is violated.

## Backup and recovery

- Back up the SQLite audit database only if policy permits retention.
- Encrypt backups and test restore.
- Production should use a managed relational database with point-in-time recovery.
- Prompts, policies, and evaluation sets should be versioned in source control.
