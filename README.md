# LLM Output Assurance Lab

A production-oriented reference application for validating AI-assisted business
outputs and code before they are used, merged, released, or sent externally.

This repository began as a DistilGPT-2 LoRA critique experiment for DrLaw. The
saved five-case evaluation showed that the adapter **must not be promoted**:
category coverage improved slightly and latency decreased, but structured-output
compliance fell from 100% to 40% and error detection fell from 100% to 60%.
Instead of hiding that result, the project now demonstrates the engineering
controls needed to evaluate and safely operate probabilistic AI systems.

## What it demonstrates

- OpenAI-compatible LLM integration with a versioned, injection-aware prompt.
- Strict eight-category structured critique with Pydantic validation.
- Transparent deterministic fallback when no provider is configured.
- Output assurance for unsupported claims, secrets, unauthorized PII, prompt
  injection, unsafe generated code, required/forbidden terms, and external actions.
- Evidence-based model promotion with quality and latency non-regression gates.
- SQLite audit records that exclude raw prompts, outputs, code, PII, and secrets.
- Prometheus request, latency, finding, provider, and decision metrics.
- Hadoop Streaming mapper and reducer (`jobs/hadoop`) that tally decisions and finding categories. `run_local.py` is the same contract without a cluster.
- An R script (`jobs/r/score_summary.R`) that reads that tally and reports the blocked rate with a 95% Wilson interval.
- FastAPI/OpenAPI service, responsive browser UI, Docker health check, pytest,
  GitHub Actions CI, compilation check, and dependency audit.

## Why it matters to a business

AI accelerates delivery only when its outputs remain fit for purpose. This
control plane converts broad review advice into traceable acceptance criteria:

1. **Frame** the use case, approved evidence, and required/forbidden content.
2. **Generate** through a versioned structured prompt contract.
3. **Interrogate** correctness, logic, security, privacy, and business fitness.
4. **Decide** whether to approve, review, block, promote, or reject.
5. **Operate** with metrics, audit records, CI, support documentation, and rollback.

For a real pilot, measure escaped defects, reviewer time, false-positive rate,
promotion lead time, p95 latency, provider failure rate, cost per validated
output, and incidents prevented. Do not claim ROI until a baseline and owner are
defined.

## Architecture

```text
Business use case + approved evidence + AI output / generated code
                              |
                              v
                 FastAPI validation boundary
                    /                   \
                   v                     v
     deterministic policy checks   structured LLM critique
       claims / PII / secrets       versioned prompt + schema
       injection / code / action    provider or safe fallback
                   \                     /
                    v                   v
               approve / review / block
                         |
             SQLite audit + Prometheus metrics

Saved baseline/candidate metrics --> promotion gate --> promote or reject
```

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn llm_assurance.api:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Metrics: http://127.0.0.1:8000/metrics
- Health: http://127.0.0.1:8000/health

The application works without an API key. To enable semantic critique:

```powershell
$env:LLM_API_KEY = "your-provider-key"
$env:LLM_BASE_URL = "https://api.groq.com/openai/v1"
$env:LLM_MODEL = "llama-3.1-8b-instant"
uvicorn llm_assurance.api:app --reload
```

Never commit `.env` or provider credentials.

## API workflows

### Validate an AI-assisted output

`POST /v1/assure`

```json
{
  "use_case": "client risk summary",
  "prompt": "Summarize the approved evidence.",
  "authorized_context": "The approved loss ratio is 12%.",
  "output": "The approved evidence reports a loss ratio of 12%.",
  "generated_code": null,
  "required_terms": ["12%"],
  "forbidden_terms": ["guaranteed"],
  "external_action": false
}
```

### Generate a structured critique

`POST /v1/critique`

```json
{
  "question": "Should this recommendation be sent?",
  "answer": "This guarantees zero client risk.",
  "authorized_evidence": "A human advisor must approve recommendations."
}
```

The response always contains exactly eight validated categories: factual
accuracy, logical reasoning, terminology, completeness, compliance, structure,
contextual relevance, and practical applicability.

### Gate a candidate model

`POST /v1/promotion-check` compares baseline and candidate category coverage,
structured-output compliance, error detection, and latency. Any configured
quality regression or excessive latency regression rejects promotion.

## Verification

```powershell
pytest
python -m compileall -q llm_assurance
node --check web/app.js
docker build -t llm-output-assurance-lab .
```

The CI workflow repeats tests, compilation, dependency audit, and container build.

## AI-assisted engineering workflow

AI tools can accelerate problem framing, implementation alternatives, test-case
generation, documentation, and code review. Their output is never accepted
solely because it compiles.

For every AI-assisted change:

1. Restate the requirement and acceptance criteria.
2. Review the complete diff and dependency changes.
3. Test normal, boundary, failure, security, and privacy cases.
4. Run static checks, unit/integration tests, and dependency audit.
5. Verify logs exclude prompts, secrets, PII, and generated code.
6. Record assumptions and a rollback path in the pull request.

See `docs/AI_ASSISTED_DELIVERY.md`, `docs/THREAT_MODEL.md`, and
`docs/OPERATIONS.md`.

## Training artifacts

Heavy training data, virtual environments, checkpoints, and adapter weights are
intentionally excluded from this application repository. The original experiment
scripts remain available for reproducibility, but use
`requirements-training.txt` in an isolated environment.

The checked-in `evaluation_results.json` is a small regression artifact, not a
production benchmark. Its limitations are documented rather than converted into
inflated “accuracy” claims.

## Roadmap

- Add expert-labeled insurance/risk-management evaluation cases.
- Add provider-specific token/cost metrics and OpenTelemetry traces.
- Add authentication/RBAC before multi-user deployment.
- Replace regex-only controls with layered DLP, SAST, sandboxing, and policy engine.
- Add asynchronous batch evaluation and immutable object-storage evidence.
- Integrate pull-request checks so candidate prompts/models cannot merge on regression.
