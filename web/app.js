const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

function toast(message, error = false) {
  const element = document.getElementById("toast");
  element.textContent = message;
  element.classList.toggle("error", error);
  element.classList.add("show");
  setTimeout(() => element.classList.remove("show"), 3200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed: ${response.status}`);
  return body;
}

function switchView(name) {
  document.querySelectorAll(".view").forEach((item) => item.classList.remove("active"));
  document.querySelectorAll("nav button").forEach((item) => item.classList.remove("active"));
  document.getElementById(`view-${name}`).classList.add("active");
  document.querySelector(`[data-view="${name}"]`).classList.add("active");
  if (name === "audit") loadAudit();
}

document.querySelectorAll("[data-view]").forEach((button) =>
  button.addEventListener("click", () => switchView(button.dataset.view)),
);
document.querySelectorAll("[data-go]").forEach((button) =>
  button.addEventListener("click", () => switchView(button.dataset.go)),
);

function setSubmitting(form, busy) {
  const button = form.querySelector(".submit");
  if (!button.dataset.label) button.dataset.label = button.textContent;
  button.textContent = busy ? "Running checks…" : button.dataset.label;
  button.disabled = busy;
}

document.getElementById("assure-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  setSubmitting(form, true);
  try {
    const split = (id) =>
      document
        .getElementById(id)
        .value.split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    const result = await api("/v1/assure", {
      method: "POST",
      body: JSON.stringify({
        use_case: document.getElementById("use-case").value,
        prompt: document.getElementById("prompt").value,
        authorized_context: document.getElementById("context").value,
        output: document.getElementById("output").value,
        generated_code: document.getElementById("generated-code").value || null,
        required_terms: split("required-terms"),
        forbidden_terms: split("forbidden-terms"),
        external_action: document.getElementById("external-action").checked,
      }),
    });
    document.getElementById("assure-result").innerHTML = `
      <div class="result-head">
        <span class="verdict ${escapeHtml(result.verdict)}">${escapeHtml(result.verdict.replaceAll("_", " "))}</span>
        <span class="meta"><code>${escapeHtml(result.request_id)}</code> · ${escapeHtml(result.latency_ms)} ms</span>
      </div>
      <div class="score"><strong>${escapeHtml(result.assurance_score)}/100</strong><span>Policy assurance score · ${escapeHtml(result.policy_version)}</span></div>
      <h2>${result.findings.length ? "Findings and remediation" : "All configured checks passed"}</h2>
      ${result.findings
        .map(
          (finding) => `
            <div class="finding">
              <div class="result-head"><h3>${escapeHtml(finding.category.replaceAll("_", " "))}</h3><span class="verdict ${escapeHtml(finding.severity === "critical" || finding.severity === "high" ? "fail" : "unknown")}">${escapeHtml(finding.severity)}</span></div>
              <p>${escapeHtml(finding.message)}</p>
              <p><strong>Evidence:</strong> ${escapeHtml(finding.evidence)}</p>
              <p><strong>Fix:</strong> ${escapeHtml(finding.remediation)}</p>
            </div>`,
        )
        .join("")}
      <div class="finding"><h3>Checks executed</h3><p>${result.checks_run.map(escapeHtml).join(" · ")}</p></div>`;
    toast(`Decision: ${result.verdict}`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setSubmitting(form, false);
  }
});

document.getElementById("critique-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  setSubmitting(form, true);
  try {
    const result = await api("/v1/critique", {
      method: "POST",
      body: JSON.stringify({
        question: document.getElementById("critique-question").value,
        answer: document.getElementById("critique-answer").value,
        authorized_evidence: document.getElementById("critique-evidence").value,
      }),
    });
    document.getElementById("critique-result").innerHTML = `
      <div class="result-head">
        <span class="verdict review_required">human review</span>
        <span class="meta">${escapeHtml(result.provider)} · ${escapeHtml(result.model)}</span>
      </div>
      <h2>${escapeHtml(result.summary)}</h2>
      <p class="meta">Prompt ${escapeHtml(result.prompt_version)} · ${escapeHtml(result.latency_ms)} ms · <code>${escapeHtml(result.request_id)}</code></p>
      ${result.categories
        .map(
          (category) => `
            <div class="category">
              <div class="result-head"><h3>${escapeHtml(category.name.replaceAll("_", " "))}</h3><span class="verdict ${escapeHtml(category.status)}">${escapeHtml(category.status)}</span></div>
              <p>${escapeHtml(category.reason)}</p>
              ${category.evidence ? `<p><strong>Evidence:</strong> ${escapeHtml(category.evidence)}</p>` : ""}
            </div>`,
        )
        .join("")}`;
    toast(`Critique completed with ${result.provider}`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setSubmitting(form, false);
  }
});

document.getElementById("promotion-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  setSubmitting(form, true);
  const read = (id) => Number(document.getElementById(id).value);
  try {
    const result = await api("/v1/promotion-check", {
      method: "POST",
      body: JSON.stringify({
        baseline: {
          name: "distilgpt2-base",
          category_coverage: read("base-coverage"),
          structured_output_pct: read("base-structure"),
          error_detection_pct: read("base-detection"),
          avg_latency_seconds: read("base-latency"),
        },
        candidate: {
          name: "distilgpt2-critique-lora",
          category_coverage: read("candidate-coverage"),
          structured_output_pct: read("candidate-structure"),
          error_detection_pct: read("candidate-detection"),
          avg_latency_seconds: read("candidate-latency"),
        },
        max_latency_regression_pct: 25,
      }),
    });
    document.getElementById("promotion-result").innerHTML = `
      <div class="result-head">
        <span class="verdict ${escapeHtml(result.decision)}">${escapeHtml(result.decision)}</span>
        <span class="meta">${escapeHtml(result.policy_version)}</span>
      </div>
      <h2>${result.promoted ? "Candidate cleared every non-regression gate" : "Candidate is not safe to release"}</h2>
      <div class="score">
        <strong>${result.promoted ? "PROMOTE" : "REJECT"}</strong>
        <span>Evidence-based release decision</span>
      </div>
      <div class="finding"><h3>Decision rationale</h3>${result.reasons.map((reason) => `<p>${escapeHtml(reason)}</p>`).join("")}</div>
      <div class="finding"><h3>Metric deltas</h3>${Object.entries(result.metric_deltas).map(([key, value]) => `<p><strong>${escapeHtml(key.replaceAll("_", " "))}:</strong> ${escapeHtml(value)}</p>`).join("")}</div>`;
    toast(`Release decision: ${result.decision}`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setSubmitting(form, false);
  }
});

async function loadAudit() {
  const table = document.getElementById("audit-body");
  table.innerHTML = '<tr><td colspan="8">Loading events…</td></tr>';
  try {
    const result = await api("/v1/audit?limit=40");
    table.innerHTML = result.events.length
      ? result.events
          .map(
            (event) => `
              <tr>
                <td><code>${escapeHtml(event.request_id)}</code></td>
                <td>${escapeHtml(event.event_type)}</td>
                <td>${escapeHtml(event.use_case)}</td>
                <td><span class="verdict ${escapeHtml(event.decision)}">${escapeHtml(event.decision)}</span></td>
                <td>${escapeHtml(event.score ?? "—")}</td>
                <td>${escapeHtml(event.finding_count)}</td>
                <td>${escapeHtml(event.latency_ms)} ms</td>
                <td>${escapeHtml(new Date(event.created_at).toLocaleString("en-IN"))}</td>
              </tr>`,
          )
          .join("")
      : '<tr><td colspan="8">No audit events yet.</td></tr>';
  } catch (error) {
    table.innerHTML = `<tr><td colspan="8">${escapeHtml(error.message)}</td></tr>`;
  }
}

document.getElementById("refresh-audit").addEventListener("click", loadAudit);

api("/health")
  .then((health) => {
    document.getElementById("health-dot").classList.add("online");
    document.getElementById("health-text").textContent = `Ready · ${health.policy_version}`;
  })
  .catch(() => {
    document.getElementById("health-text").textContent = "Unavailable";
  });
