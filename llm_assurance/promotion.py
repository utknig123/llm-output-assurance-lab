from .models import PromotionRequest, PromotionResponse
from .validation import POLICY_VERSION


def evaluate_promotion(request: PromotionRequest) -> PromotionResponse:
    baseline = request.baseline
    candidate = request.candidate
    deltas = {
        "category_coverage": round(
            candidate.category_coverage - baseline.category_coverage, 3
        ),
        "structured_output_pct": round(
            candidate.structured_output_pct - baseline.structured_output_pct, 3
        ),
        "error_detection_pct": round(
            candidate.error_detection_pct - baseline.error_detection_pct, 3
        ),
        "latency_pct": round(
            (candidate.avg_latency_seconds - baseline.avg_latency_seconds)
            / baseline.avg_latency_seconds
            * 100,
            3,
        ),
    }
    reasons: list[str] = []
    if deltas["category_coverage"] < 0:
        reasons.append("Candidate reduced category coverage.")
    if deltas["structured_output_pct"] < 0:
        reasons.append("Candidate reduced structured-output compliance.")
    if deltas["error_detection_pct"] < 0:
        reasons.append("Candidate reduced error-detection performance.")
    if deltas["latency_pct"] > request.max_latency_regression_pct:
        reasons.append(
            "Candidate exceeded the allowed latency regression "
            f"of {request.max_latency_regression_pct:.1f}%."
        )
    if not reasons:
        reasons.append("Candidate met all configured non-regression gates.")

    promoted = len(reasons) == 1 and reasons[0].startswith("Candidate met")
    return PromotionResponse(
        promoted=promoted,
        decision="promote" if promoted else "reject",
        reasons=reasons,
        metric_deltas=deltas,
        policy_version=POLICY_VERSION,
    )
