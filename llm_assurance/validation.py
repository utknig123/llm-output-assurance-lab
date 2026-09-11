from __future__ import annotations

import re

from .models import AssuranceRequest, Finding


POLICY_VERSION = "2026-09-11.2"

INJECTION_PATTERNS = (
    r"ignore (?:all |the )?(?:previous|prior) instructions",
    r"reveal (?:the )?(?:system|developer) prompt",
    r"act as (?:an? )?(?:unrestricted|unfiltered)",
    r"override (?:the )?(?:policy|guardrails|instructions)",
    r"do not follow (?:the )?(?:system|developer) message",
)
SECRET_PATTERNS = (
    r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
    r"sk-[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{20,}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
)
PII_PATTERNS = {
    "email address": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    "Indian phone number": r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
    "credit-card-like number": r"\b(?:\d[ -]*?){13,19}\b",
}
CODE_RISKS = (
    ("dynamic eval", r"\beval\s*\(", "Avoid evaluating untrusted text; use a parser or allowlist."),
    ("dynamic exec", r"\bexec\s*\(", "Do not execute model-generated code without isolation and review."),
    ("shell command execution", r"shell\s*=\s*True", "Use argument arrays and strict allowlists."),
    ("disabled TLS verification", r"verify\s*=\s*False", "Enable certificate verification."),
    ("unsafe deserialization", r"\bpickle\.loads?\s*\(", "Use a safe serialization format such as JSON."),
)


def _snippet(text: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - 25)
    end = min(len(text), match.end() + 25)
    return text[start:end].replace("\n", " ")


def validate_output(request: AssuranceRequest) -> tuple[int, str, list[Finding], list[str]]:
    findings: list[Finding] = []
    checks = [
        "prompt-injection patterns",
        "secret exposure",
        "PII leakage",
        "unsupported quantified claims",
        "generated-code security",
        "output completeness",
        "use-case fitness",
        "human approval for external actions",
    ]

    untrusted_text = (
        f"{request.prompt}\n{request.authorized_context}\n{request.output}"
    )
    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, untrusted_text, re.IGNORECASE)
        if match:
            findings.append(
                Finding(
                    category="prompt_injection",
                    severity="critical",
                    message="Untrusted content contains an instruction-override pattern.",
                    evidence=_snippet(untrusted_text, match),
                    remediation="Treat retrieved/user content as data, delimit it, and never grant it instruction priority.",
                )
            )
            break

    for pattern in SECRET_PATTERNS:
        match = re.search(pattern, request.output)
        if match:
            findings.append(
                Finding(
                    category="secret_exposure",
                    severity="critical",
                    message="The output appears to expose a credential or private key.",
                    evidence=_snippet(request.output, match),
                    remediation="Block the response, revoke the exposed credential, and use secret redaction.",
                )
            )
            break

    for label, pattern in PII_PATTERNS.items():
        output_values = set(re.findall(pattern, request.output, re.IGNORECASE))
        context_values = set(re.findall(pattern, request.authorized_context, re.IGNORECASE))
        leaked_values = output_values - context_values
        if leaked_values:
            findings.append(
                Finding(
                    category="privacy",
                    severity="high",
                    message=f"Output contains an unauthorized {label}.",
                    evidence=str(next(iter(leaked_values)))[:80],
                    remediation="Redact the value and verify user purpose, consent, and data access.",
                )
            )

    quantified_claims = re.findall(
        r"\b\d+(?:\.\d+)?\s*(?:%|percent|₹|USD|INR|million|billion)\b",
        request.output,
        re.IGNORECASE,
    )
    unsupported = [claim for claim in quantified_claims if claim not in request.authorized_context]
    if unsupported:
        findings.append(
            Finding(
                category="unsupported_claim",
                severity="high",
                message="Quantified claims are not present in the authorized evidence.",
                evidence=", ".join(unsupported[:3]),
                remediation="Add a citation to approved evidence or remove/qualify the claim.",
            )
        )

    certainty_match = re.search(
        r"\b(?:guaranteed|always correct|zero risk|will definitely)\b",
        request.output,
        re.IGNORECASE,
    )
    if certainty_match:
        findings.append(
            Finding(
                category="unsupported_claim",
                severity="high",
                message="The output uses unjustified certainty.",
                evidence=_snippet(request.output, certainty_match),
                remediation="Calibrate confidence and state assumptions, evidence, and limitations.",
            )
        )

    if request.generated_code:
        for name, pattern, remediation in CODE_RISKS:
            match = re.search(pattern, request.generated_code, re.IGNORECASE)
            if match:
                findings.append(
                    Finding(
                        category="code_security",
                        severity="high",
                        message=f"Generated code contains {name}.",
                        evidence=_snippet(request.generated_code, match),
                        remediation=remediation,
                    )
                )

    if len(request.output.strip()) < 20:
        findings.append(
            Finding(
                category="output_quality",
                severity="medium",
                message="Output is too short to demonstrate fitness for purpose.",
                evidence=request.output[:80],
                remediation="Require the expected schema and minimum decision-relevant fields.",
            )
        )

    normalized_output = request.output.casefold()
    missing_terms = [
        term for term in request.required_terms
        if term.strip() and term.casefold() not in normalized_output
    ]
    present_forbidden_terms = [
        term for term in request.forbidden_terms
        if term.strip() and term.casefold() in normalized_output
    ]
    if missing_terms:
        findings.append(
            Finding(
                category="fitness_for_purpose",
                severity="medium",
                message="Output is missing required business or engineering content.",
                evidence=", ".join(missing_terms[:5]),
                remediation="Revise the output to satisfy the approved acceptance criteria.",
            )
        )
    if present_forbidden_terms:
        findings.append(
            Finding(
                category="fitness_for_purpose",
                severity="high",
                message="Output contains content prohibited by the use-case policy.",
                evidence=", ".join(present_forbidden_terms[:5]),
                remediation="Remove prohibited content and rerun validation before use.",
            )
        )

    if request.external_action:
        findings.append(
            Finding(
                category="human_approval",
                severity="high",
                message="The workflow requests an external or potentially irreversible action.",
                evidence=request.use_case,
                remediation="Require explicit user confirmation, authorization, idempotency, and an audit record.",
            )
        )

    weights = {"critical": 40, "high": 22, "medium": 10, "low": 4}
    score = max(0, 100 - sum(weights[item.severity] for item in findings))
    severities = {item.severity for item in findings}
    if "critical" in severities or "high" in severities:
        verdict = "blocked"
    elif findings:
        verdict = "needs_review"
    else:
        verdict = "approved"
    return score, verdict, findings, checks
