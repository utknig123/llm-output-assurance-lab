from fastapi.testclient import TestClient

from llm_assurance.api import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "deterministic-verification"


def test_assurance_api_returns_traceable_decision() -> None:
    response = client.post(
        "/v1/assure",
        json={
            "use_case": "AI-assisted code review",
            "prompt": "Review this generated helper.",
            "output": "The helper is ready for human review before it is merged.",
            "generated_code": "result = parse_json(payload)",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["verdict"] == "approved"
    assert body["request_id"]
    assert body["policy_version"]


def test_structured_critique_has_eight_categories(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.post(
        "/v1/critique",
        json={
            "question": "Should this risk recommendation be sent?",
            "answer": "This is guaranteed to remove all client risk.",
            "authorized_evidence": "A human advisor must approve recommendations.",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["provider"] == "deterministic_fallback"
    assert len(body["categories"]) == 8
    assert body["requires_human_review"] is True
    assert any(
        item["name"] == "compliance" and item["status"] == "fail"
        for item in body["categories"]
    )


def test_promotion_api_blocks_regression() -> None:
    response = client.post(
        "/v1/promotion-check",
        json={
            "baseline": {
                "name": "base",
                "category_coverage": 4,
                "structured_output_pct": 90,
                "error_detection_pct": 80,
                "avg_latency_seconds": 2,
            },
            "candidate": {
                "name": "candidate",
                "category_coverage": 5,
                "structured_output_pct": 75,
                "error_detection_pct": 85,
                "avg_latency_seconds": 2.1,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "reject"


def test_metrics_endpoint() -> None:
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "llm_assurance_requests_total" in response.text
