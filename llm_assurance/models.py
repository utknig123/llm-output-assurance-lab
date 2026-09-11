from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]
Verdict = Literal["approved", "needs_review", "blocked"]


class AssuranceRequest(BaseModel):
    use_case: str = Field(min_length=3, max_length=120)
    prompt: str = Field(min_length=3, max_length=20_000)
    output: str = Field(min_length=1, max_length=50_000)
    authorized_context: str = Field(default="", max_length=50_000)
    generated_code: str | None = Field(default=None, max_length=50_000)
    required_terms: list[str] = Field(default_factory=list, max_length=25)
    forbidden_terms: list[str] = Field(default_factory=list, max_length=25)
    external_action: bool = False


class Finding(BaseModel):
    category: Literal[
        "prompt_injection",
        "privacy",
        "secret_exposure",
        "unsupported_claim",
        "code_security",
        "output_quality",
        "fitness_for_purpose",
        "human_approval",
    ]
    severity: Severity
    message: str
    evidence: str
    remediation: str


class AssuranceResponse(BaseModel):
    request_id: str
    verdict: Verdict
    assurance_score: int = Field(ge=0, le=100)
    findings: list[Finding]
    checks_run: list[str]
    latency_ms: float
    policy_version: str


class ModelMetrics(BaseModel):
    name: str
    category_coverage: float = Field(ge=0, le=8)
    structured_output_pct: float = Field(ge=0, le=100)
    error_detection_pct: float = Field(ge=0, le=100)
    avg_latency_seconds: float = Field(gt=0)


class PromotionRequest(BaseModel):
    baseline: ModelMetrics
    candidate: ModelMetrics
    max_latency_regression_pct: float = Field(default=25, ge=0, le=500)


class PromotionResponse(BaseModel):
    promoted: bool
    decision: Literal["promote", "reject"]
    reasons: list[str]
    metric_deltas: dict[str, float]
    policy_version: str


class CritiqueRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)
    answer: str = Field(min_length=3, max_length=8_000)
    authorized_evidence: str = Field(default="", max_length=8_000)


class CritiqueCategory(BaseModel):
    name: Literal[
        "factual_accuracy",
        "logical_reasoning",
        "terminology",
        "completeness",
        "compliance",
        "structure",
        "contextual_relevance",
        "practical_applicability",
    ]
    status: Literal["pass", "fail", "unknown"]
    reason: str = Field(min_length=1, max_length=1_000)
    evidence: str | None = Field(default=None, max_length=1_000)


class CritiqueResponse(BaseModel):
    request_id: str
    summary: str
    categories: list[CritiqueCategory] = Field(min_length=8, max_length=8)
    requires_human_review: bool
    provider: Literal["openai_compatible", "deterministic_fallback"]
    model: str
    prompt_version: str
    latency_ms: float
