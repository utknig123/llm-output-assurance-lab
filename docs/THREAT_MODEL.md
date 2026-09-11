# Threat Model

## Protected assets

- Client and employee personal information
- Proprietary business and risk data
- LLM/provider credentials
- System/developer prompts and policies
- Generated recommendations and code
- Audit integrity and model-promotion decisions

## Trust boundaries

1. User/browser to FastAPI input validation
2. Untrusted prompt, retrieval content, and generated output
3. Application to external LLM provider
4. Application to SQLite audit store
5. CI/container supply chain

## Priority threats and controls

### Prompt injection

Threat: retrieved/user content asks the model to ignore policy or disclose
instructions. Controls: delimit untrusted blocks, instruction hierarchy,
deterministic injection scan, minimal tools, output validation, and human review.

### Data leakage

Threat: secrets or PII appear in provider requests, responses, logs, or audit
records. Controls: least-data prompts, credential/PII scanning, approved evidence,
redacted metadata-only audit, secret manager, retention policy, and access control.

### Unsupported decisions

Threat: plausible quantified claims or certainty influence business decisions.
Controls: authorized context, citation requirement, quantified-claim comparison,
required/forbidden terms, calibrated uncertainty, and owner approval.

### Unsafe generated code

Threat: command injection, disabled TLS, dynamic execution, or unsafe
deserialization. Controls: pattern checks, manual review, SAST/dependency audit,
tests, sandboxing for untrusted execution, and least-privilege runtime.

### Model regression

Threat: a new prompt/model improves one metric while degrading reliability.
Controls: representative golden set, separate retrieval/generation metrics,
non-regression gate, versioning, canary release, monitoring, and rollback.

### Supply-chain compromise

Threat: malicious dependency or CI action. Controls: pinned dependencies,
read-only CI permissions, dependency audit, image scanning in production,
trusted action versions, and minimal container user.

## Known limitations

- Regex controls are demonstrative and can be bypassed; production requires
  layered DLP, policy enforcement, and contextual classifiers.
- Authentication/RBAC is not included in this single-user reference app.
- SQLite is not suitable for high-volume distributed operation.
- Deterministic fallback cannot semantically fact-check an answer.
- External provider data handling must be reviewed against company contracts,
  residency, retention, and compliance requirements.
