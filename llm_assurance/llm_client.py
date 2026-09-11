from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

from .models import CritiqueCategory, CritiqueRequest, CritiqueResponse
from .prompts import CATEGORIES, CRITIQUE_PROMPT_VERSION, build_critique_prompt


DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        raise ValueError("Provider did not return a JSON object.")
    payload = json.loads(text[start:end])
    if not isinstance(payload, dict):
        raise ValueError("Provider response must be a JSON object.")
    return payload


def _normalize_categories(payload: dict[str, Any]) -> list[CritiqueCategory]:
    supplied = {
        item.get("name"): item
        for item in payload.get("categories", [])
        if isinstance(item, dict) and item.get("name") in CATEGORIES
    }
    categories = []
    for name in CATEGORIES:
        item = supplied.get(name)
        if item is None:
            categories.append(
                CritiqueCategory(
                    name=name,
                    status="unknown",
                    reason="The provider omitted this required category.",
                    evidence=None,
                )
            )
            continue
        categories.append(CritiqueCategory.model_validate(item))
    return categories


def _provider_critique(request: CritiqueRequest) -> tuple[str, list[CritiqueCategory], bool, str]:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("No LLM provider key configured.")

    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    prompt = build_critique_prompt(
        request.question,
        request.answer,
        request.authorized_evidence,
    )
    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 1_800,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    payload = _extract_json(content)
    categories = _normalize_categories(payload)
    return (
        str(payload.get("summary") or "Structured critique completed.")[:2_000],
        categories,
        bool(payload.get("requires_human_review", True)),
        model,
    )


def _deterministic_critique(
    request: CritiqueRequest,
) -> tuple[str, list[CritiqueCategory], bool, str]:
    answer = request.answer.casefold()
    evidence = request.authorized_evidence.casefold()
    certainty = any(term in answer for term in ("guaranteed", "zero risk", "always correct"))
    evidence_available = bool(evidence.strip())
    categories: list[CritiqueCategory] = []
    for name in CATEGORIES:
        status = "pass"
        reason = "No deterministic issue detected; model-based review is still recommended."
        if name in {"factual_accuracy", "contextual_relevance"} and not evidence_available:
            status = "unknown"
            reason = "No authorized evidence was provided for factual verification."
        elif name == "compliance" and certainty:
            status = "fail"
            reason = "The answer contains an unjustified certainty claim."
        elif name == "completeness" and len(request.answer.split()) < 20:
            status = "unknown"
            reason = "The answer may be too brief to satisfy the intended use case."
        categories.append(
            CritiqueCategory(
                name=name,
                status=status,
                reason=reason,
                evidence=None,
            )
        )
    failures = sum(item.status == "fail" for item in categories)
    unknowns = sum(item.status == "unknown" for item in categories)
    summary = (
        f"Offline verification completed with {failures} failed and "
        f"{unknowns} unknown categories. Configure an OpenAI-compatible provider "
        "for semantic critique."
    )
    return summary, categories, True, "offline-rules-v1"


def generate_critique(request_id: str, request: CritiqueRequest) -> CritiqueResponse:
    started = time.perf_counter()
    try:
        summary, categories, human_review, model = _provider_critique(request)
        provider = "openai_compatible"
    except (RuntimeError, httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        summary, categories, human_review, model = _deterministic_critique(request)
        provider = "deterministic_fallback"

    return CritiqueResponse(
        request_id=request_id,
        summary=summary,
        categories=categories,
        requires_human_review=human_review,
        provider=provider,
        model=model,
        prompt_version=CRITIQUE_PROMPT_VERSION,
        latency_ms=round((time.perf_counter() - started) * 1_000, 3),
    )
