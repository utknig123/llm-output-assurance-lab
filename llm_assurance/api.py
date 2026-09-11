from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .database import initialize_database, recent_events, record_event
from .llm_client import generate_critique
from .models import (
    AssuranceRequest,
    AssuranceResponse,
    CritiqueRequest,
    CritiqueResponse,
    PromotionRequest,
    PromotionResponse,
)
from .promotion import evaluate_promotion
from .validation import POLICY_VERSION, validate_output


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOGGER = logging.getLogger("llm-assurance")

REQUESTS = Counter(
    "llm_assurance_requests_total",
    "Completed assurance requests",
    ["endpoint", "decision"],
)
LATENCY = Histogram(
    "llm_assurance_request_duration_seconds",
    "Assurance request duration",
    ["endpoint"],
)
FINDINGS = Counter(
    "llm_assurance_findings_total",
    "Validation findings",
    ["category", "severity"],
)
CRITIQUES = Counter(
    "llm_assurance_critiques_total",
    "Structured critique requests",
    ["provider"],
)

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="LLM Output Assurance Lab",
    version="1.0.0",
    description=(
        "Policy-based verification and model-promotion gates for AI-assisted "
        "engineering and business workflows."
    ),
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "policy_version": POLICY_VERSION,
        "mode": "deterministic-verification",
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/assure", response_model=AssuranceResponse)
def assure(request: AssuranceRequest) -> AssuranceResponse:
    request_id = uuid.uuid4().hex[:16]
    started = time.perf_counter()
    score, verdict, findings, checks = validate_output(request)
    latency_ms = round((time.perf_counter() - started) * 1_000, 3)

    REQUESTS.labels(endpoint="assure", decision=verdict).inc()
    LATENCY.labels(endpoint="assure").observe(latency_ms / 1_000)
    for finding in findings:
        FINDINGS.labels(
            category=finding.category,
            severity=finding.severity,
        ).inc()

    LOGGER.info(
        json.dumps(
            {
                "event": "assurance_completed",
                "request_id": request_id,
                "use_case": request.use_case,
                "verdict": verdict,
                "score": score,
                "finding_count": len(findings),
                "policy_version": POLICY_VERSION,
                "latency_ms": latency_ms,
            }
        )
    )
    record_event(
        request_id=request_id,
        event_type="output_assurance",
        use_case=request.use_case,
        decision=verdict,
        score=score,
        finding_count=len(findings),
        policy_version=POLICY_VERSION,
        latency_ms=latency_ms,
        metadata={"checks_run": len(checks), "external_action": request.external_action},
    )
    return AssuranceResponse(
        request_id=request_id,
        verdict=verdict,
        assurance_score=score,
        findings=findings,
        checks_run=checks,
        latency_ms=latency_ms,
        policy_version=POLICY_VERSION,
    )


@app.post("/v1/critique", response_model=CritiqueResponse)
def critique(request: CritiqueRequest) -> CritiqueResponse:
    request_id = uuid.uuid4().hex[:16]
    response = generate_critique(request_id, request)
    failed = sum(item.status == "fail" for item in response.categories)
    unknown = sum(item.status == "unknown" for item in response.categories)
    decision = "review_required" if response.requires_human_review else "completed"
    REQUESTS.labels(endpoint="critique", decision=decision).inc()
    CRITIQUES.labels(provider=response.provider).inc()
    LATENCY.labels(endpoint="critique").observe(response.latency_ms / 1_000)
    record_event(
        request_id=request_id,
        event_type="structured_critique",
        use_case="LLM output critique",
        decision=decision,
        score=None,
        finding_count=failed + unknown,
        policy_version=POLICY_VERSION,
        latency_ms=response.latency_ms,
        metadata={
            "provider": response.provider,
            "model": response.model,
            "prompt_version": response.prompt_version,
            "failed_categories": failed,
            "unknown_categories": unknown,
        },
    )
    return response


@app.post("/v1/promotion-check", response_model=PromotionResponse)
def promotion_check(request: PromotionRequest) -> PromotionResponse:
    started = time.perf_counter()
    request_id = uuid.uuid4().hex[:16]
    response = evaluate_promotion(request)
    latency_seconds = time.perf_counter() - started
    latency_ms = round(latency_seconds * 1_000, 3)
    REQUESTS.labels(endpoint="promotion_check", decision=response.decision).inc()
    LATENCY.labels(endpoint="promotion_check").observe(latency_seconds)
    LOGGER.info(
        json.dumps(
            {
                "event": "promotion_evaluated",
                "baseline": request.baseline.name,
                "candidate": request.candidate.name,
                "decision": response.decision,
                "policy_version": POLICY_VERSION,
            }
        )
    )
    record_event(
        request_id=request_id,
        event_type="model_promotion",
        use_case=f"{request.baseline.name} -> {request.candidate.name}",
        decision=response.decision,
        score=None,
        finding_count=len(response.reasons) if not response.promoted else 0,
        policy_version=POLICY_VERSION,
        latency_ms=latency_ms,
        metadata={"metric_deltas": response.metric_deltas},
    )
    return response


@app.get("/v1/audit")
def audit_events(
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, object]:
    events = recent_events(limit)
    return {"events": events, "count": len(events)}
