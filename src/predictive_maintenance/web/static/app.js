const config = window.PREDMAINT_CONFIG || {};
const state = {
  token: sessionStorage.getItem("predmaint.idToken"),
  refreshToken: sessionStorage.getItem("predmaint.refreshToken"),
  expiresAt: Number(sessionStorage.getItem("predmaint.expiresAt") || 0),
  email: sessionStorage.getItem("predmaint.email"),
  samples: [],
  history: [],
  showAllFeatures: false,
};

const $ = (id) => document.getElementById(id);

function setSession(payload, email) {
  state.token = payload.idToken;
  state.refreshToken = payload.refreshToken;
  state.expiresAt = Date.now() + Number(payload.expiresIn || 3600) * 1000;
  state.email = email;
  sessionStorage.setItem("predmaint.idToken", state.token);
  sessionStorage.setItem("predmaint.refreshToken", state.refreshToken);
  sessionStorage.setItem("predmaint.expiresAt", String(state.expiresAt));
  sessionStorage.setItem("predmaint.email", email);
}

function clearSession() {
  state.token = null;
  state.refreshToken = null;
  state.expiresAt = 0;
  state.email = null;
  sessionStorage.removeItem("predmaint.idToken");
  sessionStorage.removeItem("predmaint.refreshToken");
  sessionStorage.removeItem("predmaint.expiresAt");
  sessionStorage.removeItem("predmaint.email");
}

async function signIn(email, password) {
  const endpoint = `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${encodeURIComponent(config.firebaseApiKey)}`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, returnSecureToken: true }),
  });
  const payload = await response.json();
  if (!response.ok) {
    const code = payload?.error?.message || "AUTHENTICATION_FAILED";
    throw new Error(code.replaceAll("_", " ").toLowerCase());
  }
  setSession(payload, email);
}

async function ensureToken() {
  if (state.token && Date.now() < state.expiresAt - 60_000) return state.token;
  if (!state.refreshToken) throw new Error("Your session has expired. Please sign in again.");
  const endpoint = `https://securetoken.googleapis.com/v1/token?key=${encodeURIComponent(config.firebaseApiKey)}`;
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    refresh_token: state.refreshToken,
  });
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const payload = await response.json();
  if (!response.ok) {
    clearSession();
    throw new Error("Your session has expired. Please sign in again.");
  }
  setSession(
    {
      idToken: payload.id_token,
      refreshToken: payload.refresh_token,
      expiresIn: payload.expires_in,
    },
    state.email,
  );
  return state.token;
}

async function apiFetch(path, options = {}) {
  const token = await ensureToken();
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  if (response.status === 401) {
    clearSession();
    showLogin("Your session is no longer valid. Please sign in again.");
    throw new Error("Authentication required");
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `API request failed (${response.status})`);
  return payload;
}

function showLogin(message = "") {
  $("login-view").classList.remove("hidden");
  $("dashboard-view").classList.add("hidden");
  $("logout-button").classList.add("hidden");
  $("login-error").textContent = message;
}

function showDashboard() {
  $("login-view").classList.add("hidden");
  $("dashboard-view").classList.remove("hidden");
  $("logout-button").classList.remove("hidden");
  $("signed-in-as").textContent = `Authenticated as ${state.email}`;
}

function renderModel(model) {
  $("model-cards").classList.remove("skeleton-grid");
  $("model-cards").innerHTML = `
    <article><span>Champion</span><strong>${model.model.replaceAll("_", " ")}</strong></article>
    <article><span>Version</span><strong>${model.model_version}</strong></article>
    <article><span>Decision threshold</span><strong>${(model.threshold * 100).toFixed(1)}%</strong></article>
    <article><span>Validation PR-AUC</span><strong>${(model.selection_value * 100).toFixed(2)}%</strong></article>`;
  state.model = model;
}

function sampleLabel(sample) {
  const outcome = sample.actual_failure_within_horizon ? "failure" : "healthy";
  return `Machine ${sample.machine_id} · ${new Date(sample.observed_at).toLocaleString()} · ${outcome}`;
}

function renderSampleOptions(dataset) {
  state.samples = dataset.samples;
  $("dataset-badge").textContent = `${dataset.split.toUpperCase()} · ${dataset.samples.length} SAMPLES`;
  $("sample-select").innerHTML = dataset.samples
    .map((sample, index) => `<option value="${index}">${sampleLabel(sample)}</option>`)
    .join("");
  renderSelectedSample();
}

function selectedSample() {
  return state.samples[Number($("sample-select").value || 0)];
}

function renderSelectedSample() {
  const sample = selectedSample();
  if (!sample) return;
  const outcome = sample.actual_failure_within_horizon ? "Failure in horizon" : "No failure in horizon";
  $("sample-meta").innerHTML = `
    <div><span>Machine</span><strong>#${sample.machine_id}</strong></div>
    <div><span>Observed</span><strong>${new Date(sample.observed_at).toLocaleString()}</strong></div>
    <div><span>Held-out outcome</span><strong class="${sample.actual_failure_within_horizon ? "warn" : "ok"}">${outcome}</strong></div>`;
  renderFeatures(sample.features);
}

function renderFeatures(features) {
  const entries = Object.entries(features);
  const visible = state.showAllFeatures ? entries : entries.slice(0, 10);
  $("feature-table").innerHTML = visible
    .map(([name, value]) => `<div><span>${name.replaceAll("_", " ")}</span><strong>${typeof value === "number" ? Number(value).toFixed(3) : value}</strong></div>`)
    .join("");
  $("toggle-features").textContent = state.showAllFeatures ? "Show less" : `Show all ${entries.length}`;
}

function renderResult(sample, prediction) {
  const probability = prediction.failure_probability;
  const degrees = Math.max(0, Math.min(360, probability * 360));
  $("probability-gauge").style.setProperty("--probability", `${degrees}deg`);
  $("probability-value").textContent = `${(probability * 100).toFixed(1)}%`;
  $("alert-value").textContent = prediction.alert ? "Maintenance alert" : "Continue operation";
  $("alert-value").className = prediction.alert ? "warn" : "ok";
  const correct = prediction.alert === sample.actual_failure_within_horizon;
  $("ground-truth").textContent = correct
    ? "The decision matches the held-out outcome."
    : "The decision differs from the held-out outcome.";
  $("result-state").textContent = correct ? "MATCH" : "MISMATCH";
  $("result-state").className = `tag ${correct ? "success" : "danger"}`;
}

function renderHistory() {
  const history = state.history;
  const correct = history.filter((item) => item.correct).length;
  const alerts = history.filter((item) => item.prediction.alert).length;
  const mean = history.length
    ? history.reduce((sum, item) => sum + item.prediction.failure_probability, 0) / history.length
    : 0;
  $("run-count").textContent = `${history.length} RUN${history.length === 1 ? "" : "S"}`;
  $("correct-count").textContent = String(correct);
  $("alert-count").textContent = String(alerts);
  $("mean-probability").textContent = `${(mean * 100).toFixed(1)}%`;
  if (!history.length) return;
  $("history-chart").innerHTML = history
    .slice(-12)
    .map((item) => {
      const percentage = item.prediction.failure_probability * 100;
      return `<div class="history-row">
        <span>M${item.sample.machine_id}</span>
        <div><i style="width:${Math.max(2, percentage)}%" class="${item.prediction.alert ? "alert-bar" : "healthy-bar"}"></i></div>
        <strong>${percentage.toFixed(1)}%</strong>
      </div>`;
    })
    .join("");
}

async function loadWorkspace() {
  showDashboard();
  const [model, dataset] = await Promise.all([
    apiFetch("/v1/model-info"),
    apiFetch("/v1/demo-samples"),
  ]);
  renderModel(model);
  renderSampleOptions(dataset);
  $("service-status").textContent = "Champion model online";
}

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("login-error").textContent = "";
  $("login-button").disabled = true;
  try {
    await signIn($("email").value.trim(), $("password").value);
    $("password").value = "";
    await loadWorkspace();
  } catch (error) {
    showLogin(error.message);
  } finally {
    $("login-button").disabled = false;
  }
});

$("logout-button").addEventListener("click", () => {
  clearSession();
  state.history = [];
  showLogin();
});

$("sample-select").addEventListener("change", renderSelectedSample);

$("toggle-features").addEventListener("click", () => {
  state.showAllFeatures = !state.showAllFeatures;
  const sample = selectedSample();
  if (sample) renderFeatures(sample.features);
});

$("predict-button").addEventListener("click", async () => {
  const sample = selectedSample();
  if (!sample) return;
  $("inference-error").textContent = "";
  $("predict-button").disabled = true;
  try {
    const observationId = `${sample.sample_id}-${crypto.randomUUID()}`;
    const payload = await apiFetch("/v1/predict", {
      method: "POST",
      body: JSON.stringify({
        observations: [{
          observation_id: observationId,
          machine_id: sample.machine_id,
          observed_at: sample.observed_at,
          features: sample.features,
        }],
      }),
    });
    const prediction = payload.predictions[0];
    state.history.push({
      sample,
      prediction,
      correct: prediction.alert === sample.actual_failure_within_horizon,
    });
    renderResult(sample, prediction);
    renderHistory();
  } catch (error) {
    $("inference-error").textContent = error.message;
  } finally {
    $("predict-button").disabled = false;
  }
});

if (!config.firebaseApiKey || !config.firebaseProjectId || !config.apiBaseUrl) {
  showLogin("This deployment is missing its Google Cloud runtime configuration.");
} else if (state.token || state.refreshToken) {
  loadWorkspace().catch((error) => showLogin(error.message));
} else {
  showLogin();
}
