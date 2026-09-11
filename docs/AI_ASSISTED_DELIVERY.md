# AI-Assisted Delivery Standard

## Purpose

Use coding assistants and LLM APIs as active accelerators while keeping a human
engineer accountable for correctness, security, privacy, performance, and
business fitness.

## Definition of ready

- Business problem, user, owner, and expected outcome are named.
- Acceptance criteria include normal, failure, security, privacy, and performance cases.
- Approved data sources and prohibited data are identified.
- Human-approval and rollback points are explicit.

## Development loop

1. Ask the assistant for alternatives and trade-offs, not just code.
2. Give it the minimum necessary context; never provide secrets or restricted data.
3. Request typed interfaces, failure behavior, tests, and assumptions.
4. Review every generated line and dependency.
5. Run tests independently; do not ask the same model to be the sole judge.
6. Use the assurance API on generated business text or high-risk code snippets.
7. Record prompt/model/policy versions where AI behavior affects the product.

## Pull-request checklist

- [ ] Requirement and business outcome are linked.
- [ ] AI-assisted portions were manually reviewed.
- [ ] Inputs and outputs are schema validated.
- [ ] Authorization is enforced before data reaches the model.
- [ ] Prompt injection, secrets, PII, and unsafe code paths were tested.
- [ ] Unit, integration, negative, and regression tests pass.
- [ ] Logs and traces contain no raw sensitive payloads.
- [ ] Performance/cost impact is measured or explicitly unknown.
- [ ] Deployment, monitoring, support owner, and rollback are documented.

## Agile/Scrum use

- Put the business outcome and validation approach in the story.
- Demo evidence and known limitations during review.
- Add AI failures to the backlog as reproducible regression cases.
- Use retrospectives to compare estimated versus actual acceleration and defects.
- A story is not done until monitoring and support behavior are defined.
