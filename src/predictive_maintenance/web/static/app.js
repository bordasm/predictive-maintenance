const config = window.PREDMAINT_CONFIG || {};
const SUPPORTED_LANGUAGES = ["en", "hu"];
const DEFAULT_LANGUAGE = "en";

const translations = {
  en: {
    brand: { home: "RailSense home" },
    language: { selector: "Language", english: "English", hungarian: "Hungarian" },
    nav: { signOut: "Sign out" },
    status: { secure: "Secure model workspace", online: "Champion model online" },
    login: {
      eyebrow: "CONDITION INTELLIGENCE",
      headlineLine1: "See the failure",
      headlineLine2: "before it arrives.",
      summary: "Explore a production-style predictive-maintenance system using a champion model and machine observations held out from training.",
      capabilities: "Demo capabilities",
      predictionHorizon: "prediction horizon",
      modelFeatures: "model features",
      protectedInference: "protected inference",
      restrictedDemo: "RESTRICTED DEMO",
      controlRoom: "Enter the control room",
      accountHelp: "Use an account provisioned by the project administrator.",
      email: "Email",
      password: "Password",
      authenticate: "Authenticate",
      securityNote: "Credentials are verified by Google Identity Platform.",
    },
    dashboard: {
      eyebrow: "CHAMPION MODEL · LIVE INFERENCE",
      cockpit: "Machine health cockpit",
      modelStatus: "MODEL STATUS",
      ready: "Ready",
      champion: "Champion",
      loading: "Loading…",
      version: "Version",
      threshold: "Decision threshold",
      validation: "Validation PR-AUC",
      selectObservation: "Select held-out observation",
      testSplit: "TEST SPLIT",
      machineObservation: "Machine observation",
      runInference: "Run champion inference",
      inferenceResult: "Inference result",
      waiting: "WAITING",
      failureProbability: "failure probability",
      decision24h: "24-hour decision",
      noInference: "No inference yet",
      selectToCompare: "Select a test observation to compare prediction and outcome.",
      sessionDashboard: "Session dashboard",
      zeroRuns: "0 RUNS",
      correctDecisions: "Correct decisions",
      alerts: "Alerts",
      meanProbability: "Mean probability",
      historyEmpty: "Inference results will appear here.",
      observationFeatures: "Observation features",
      showAll: "Show all",
    },
    dynamic: {
      signedInAs: "Authenticated as {email}",
      machineOption: "Machine {machine} · {date} · {outcome}",
      failure: "failure",
      healthy: "healthy",
      dataset: "{split} · {count} SAMPLES",
      test: "TEST",
      machine: "Machine",
      observed: "Observed",
      heldOutOutcome: "Held-out outcome",
      failureInHorizon: "Failure in horizon",
      noFailureInHorizon: "No failure in horizon",
      showLess: "Show less",
      showAllCount: "Show all {count}",
      maintenanceAlert: "Maintenance alert",
      continueOperation: "Continue operation",
      decisionMatch: "The decision matches the held-out outcome.",
      decisionMismatch: "The decision differs from the held-out outcome.",
      match: "MATCH",
      mismatch: "MISMATCH",
      runsOne: "{count} RUN",
      runsMany: "{count} RUNS",
    },
    errors: {
      sessionExpired: "Your session has expired. Please sign in again.",
      sessionInvalid: "Your session is no longer valid. Please sign in again.",
      authenticationRequired: "Authentication required",
      authenticationFailed: "Authentication failed. Check your email and password.",
      invalidEmail: "Enter a valid email address.",
      userDisabled: "This account has been disabled.",
      tooManyAttempts: "Too many attempts. Please try again later.",
      apiRequest: "API request failed ({status}).",
      missingConfig: "This deployment is missing its Google Cloud runtime configuration.",
    },
    features: {
      volt: "Voltage",
      rotate: "Rotational speed",
      pressure: "Pressure",
      vibration: "Vibration",
      volt_mean_3h: "Voltage mean · 3 h",
      volt_std_3h: "Voltage deviation · 3 h",
      rotate_mean_3h: "Rotational speed mean · 3 h",
      rotate_std_3h: "Rotational speed deviation · 3 h",
      pressure_mean_3h: "Pressure mean · 3 h",
      pressure_std_3h: "Pressure deviation · 3 h",
      vibration_mean_3h: "Vibration mean · 3 h",
      vibration_std_3h: "Vibration deviation · 3 h",
      volt_mean_24h: "Voltage mean · 24 h",
      volt_std_24h: "Voltage deviation · 24 h",
      rotate_mean_24h: "Rotational speed mean · 24 h",
      rotate_std_24h: "Rotational speed deviation · 24 h",
      pressure_mean_24h: "Pressure mean · 24 h",
      pressure_std_24h: "Pressure deviation · 24 h",
      vibration_mean_24h: "Vibration mean · 24 h",
      vibration_std_24h: "Vibration deviation · 24 h",
      error1_count_24h: "Error 1 count · 24 h",
      error2_count_24h: "Error 2 count · 24 h",
      error3_count_24h: "Error 3 count · 24 h",
      error4_count_24h: "Error 4 count · 24 h",
      error5_count_24h: "Error 5 count · 24 h",
      days_since_comp1_maintenance: "Days since component 1 maintenance",
      days_since_comp2_maintenance: "Days since component 2 maintenance",
      days_since_comp3_maintenance: "Days since component 3 maintenance",
      days_since_comp4_maintenance: "Days since component 4 maintenance",
      age: "Machine age",
      model: "Machine model",
    },
  },
  hu: {
    brand: { home: "RailSense kezdőlap" },
    language: { selector: "Nyelv", english: "Angol", hungarian: "Magyar" },
    nav: { signOut: "Kijelentkezés" },
    status: { secure: "Biztonságos modell-munkatér", online: "A champion modell elérhető" },
    login: {
      eyebrow: "ÁLLAPOTINTELLIGENCIA",
      headlineLine1: "Lásd előre a hibát",
      headlineLine2: "mielőtt bekövetkezik.",
      summary: "Fedezz fel egy éles rendszert mintázó prediktív karbantartási megoldást champion modellel és a tanítástól elkülönített gépmegfigyelésekkel.",
      capabilities: "A demó képességei",
      predictionHorizon: "előrejelzési horizont",
      modelFeatures: "modelljellemző",
      protectedInference: "védett inference",
      restrictedDemo: "KORLÁTOZOTT DEMÓ",
      controlRoom: "Lépj be a vezérlőközpontba",
      accountHelp: "Használj a projekt adminisztrátora által létrehozott fiókot.",
      email: "E-mail",
      password: "Jelszó",
      authenticate: "Bejelentkezés",
      securityNote: "A hitelesítő adatokat a Google Identity Platform ellenőrzi.",
    },
    dashboard: {
      eyebrow: "CHAMPION MODELL · ÉLŐ INFERENCE",
      cockpit: "Gépállapot-irányítópult",
      modelStatus: "MODELLÁLLAPOT",
      ready: "Üzemkész",
      champion: "Champion",
      loading: "Betöltés…",
      version: "Verzió",
      threshold: "Döntési küszöb",
      validation: "Validációs PR-AUC",
      selectObservation: "Válassz elkülönített tesztmegfigyelést",
      testSplit: "TESZTHALMAZ",
      machineObservation: "Gépmegfigyelés",
      runInference: "Champion inference futtatása",
      inferenceResult: "Inference eredménye",
      waiting: "VÁRAKOZÁS",
      failureProbability: "meghibásodási valószínűség",
      decision24h: "24 órás döntés",
      noInference: "Még nincs inference",
      selectToCompare: "Válassz tesztmegfigyelést a predikció és a tényleges eredmény összehasonlításához.",
      sessionDashboard: "Munkamenet-irányítópult",
      zeroRuns: "0 FUTÁS",
      correctDecisions: "Helyes döntések",
      alerts: "Riasztások",
      meanProbability: "Átlagos valószínűség",
      historyEmpty: "Az inference eredményei itt jelennek meg.",
      observationFeatures: "A megfigyelés jellemzői",
      showAll: "Összes megjelenítése",
    },
    dynamic: {
      signedInAs: "Bejelentkezve: {email}",
      machineOption: "{machine}. gép · {date} · {outcome}",
      failure: "meghibásodás",
      healthy: "egészséges",
      dataset: "{split} · {count} MINTA",
      test: "TESZT",
      machine: "Gép",
      observed: "Megfigyelés ideje",
      heldOutOutcome: "Tényleges teszteredmény",
      failureInHorizon: "Meghibásodás a horizonton belül",
      noFailureInHorizon: "Nincs meghibásodás a horizonton belül",
      showLess: "Kevesebb megjelenítése",
      showAllCount: "Mind a(z) {count} megjelenítése",
      maintenanceAlert: "Karbantartási riasztás",
      continueOperation: "Üzem folytatása",
      decisionMatch: "A döntés egyezik a tényleges teszteredménnyel.",
      decisionMismatch: "A döntés eltér a tényleges teszteredménytől.",
      match: "EGYEZÉS",
      mismatch: "ELTÉRÉS",
      runsOne: "{count} FUTÁS",
      runsMany: "{count} FUTÁS",
    },
    errors: {
      sessionExpired: "A munkamenet lejárt. Jelentkezz be újra.",
      sessionInvalid: "A munkamenet már nem érvényes. Jelentkezz be újra.",
      authenticationRequired: "Bejelentkezés szükséges",
      authenticationFailed: "A bejelentkezés sikertelen. Ellenőrizd az e-mail-címet és a jelszót.",
      invalidEmail: "Adj meg érvényes e-mail-címet.",
      userDisabled: "Ezt a fiókot letiltották.",
      tooManyAttempts: "Túl sok próbálkozás történt. Próbáld újra később.",
      apiRequest: "Az API-kérés sikertelen ({status}).",
      missingConfig: "Ebből a deploymentből hiányzik a Google Cloud futásidejű konfigurációja.",
    },
    features: {
      volt: "Feszültség",
      rotate: "Fordulatszám",
      pressure: "Nyomás",
      vibration: "Rezgés",
      volt_mean_3h: "Feszültségátlag · 3 óra",
      volt_std_3h: "Feszültség szórása · 3 óra",
      rotate_mean_3h: "Fordulatszám átlaga · 3 óra",
      rotate_std_3h: "Fordulatszám szórása · 3 óra",
      pressure_mean_3h: "Nyomásátlag · 3 óra",
      pressure_std_3h: "Nyomás szórása · 3 óra",
      vibration_mean_3h: "Rezgésátlag · 3 óra",
      vibration_std_3h: "Rezgés szórása · 3 óra",
      volt_mean_24h: "Feszültségátlag · 24 óra",
      volt_std_24h: "Feszültség szórása · 24 óra",
      rotate_mean_24h: "Fordulatszám átlaga · 24 óra",
      rotate_std_24h: "Fordulatszám szórása · 24 óra",
      pressure_mean_24h: "Nyomásátlag · 24 óra",
      pressure_std_24h: "Nyomás szórása · 24 óra",
      vibration_mean_24h: "Rezgésátlag · 24 óra",
      vibration_std_24h: "Rezgés szórása · 24 óra",
      error1_count_24h: "1. hiba száma · 24 óra",
      error2_count_24h: "2. hiba száma · 24 óra",
      error3_count_24h: "3. hiba száma · 24 óra",
      error4_count_24h: "4. hiba száma · 24 óra",
      error5_count_24h: "5. hiba száma · 24 óra",
      days_since_comp1_maintenance: "Az 1. komponens karbantartása óta eltelt napok",
      days_since_comp2_maintenance: "A 2. komponens karbantartása óta eltelt napok",
      days_since_comp3_maintenance: "A 3. komponens karbantartása óta eltelt napok",
      days_since_comp4_maintenance: "A 4. komponens karbantartása óta eltelt napok",
      age: "Gép életkora",
      model: "Gépmodell",
    },
  },
};

function storedLanguage() {
  const stored = localStorage.getItem("predmaint.language");
  return SUPPORTED_LANGUAGES.includes(stored) ? stored : DEFAULT_LANGUAGE;
}

const state = {
  token: sessionStorage.getItem("predmaint.idToken"),
  refreshToken: sessionStorage.getItem("predmaint.refreshToken"),
  expiresAt: Number(sessionStorage.getItem("predmaint.expiresAt") || 0),
  email: sessionStorage.getItem("predmaint.email"),
  language: storedLanguage(),
  samples: [],
  history: [],
  showAllFeatures: false,
  model: null,
  dataset: null,
  loginError: null,
  inferenceError: null,
};

const $ = (id) => document.getElementById(id);

function translationValue(language, key) {
  return key.split(".").reduce((value, part) => value?.[part], translations[language]);
}

function t(key, variables = {}) {
  const template = translationValue(state.language, key)
    ?? translationValue(DEFAULT_LANGUAGE, key)
    ?? key;
  return Object.entries(variables).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    template,
  );
}

function localizedError(key, variables = {}) {
  const error = new Error(t(key, variables));
  error.translationKey = key;
  error.translationVariables = variables;
  return error;
}

function errorMessage(error) {
  if (!error) return "";
  if (error.translationKey) {
    return t(error.translationKey, error.translationVariables);
  }
  return error.message || t("errors.authenticationFailed");
}

function locale() {
  return state.language === "hu" ? "hu-HU" : "en-GB";
}

function formatDate(value) {
  return new Intl.DateTimeFormat(locale(), {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatPercentage(value, digits = 1) {
  return new Intl.NumberFormat(locale(), {
    style: "percent",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function featureLabel(name) {
  const key = `features.${name}`;
  const translated = translationValue(state.language, key);
  return translated ?? name.replaceAll("_", " ");
}

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

function firebaseError(code) {
  const errorKeys = {
    EMAIL_NOT_FOUND: "errors.authenticationFailed",
    INVALID_LOGIN_CREDENTIALS: "errors.authenticationFailed",
    INVALID_PASSWORD: "errors.authenticationFailed",
    INVALID_EMAIL: "errors.invalidEmail",
    USER_DISABLED: "errors.userDisabled",
    TOO_MANY_ATTEMPTS_TRY_LATER: "errors.tooManyAttempts",
  };
  return localizedError(errorKeys[code] || "errors.authenticationFailed");
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
    throw firebaseError(payload?.error?.message || "AUTHENTICATION_FAILED");
  }
  setSession(payload, email);
}

async function ensureToken() {
  if (state.token && Date.now() < state.expiresAt - 60_000) return state.token;
  if (!state.refreshToken) throw localizedError("errors.sessionExpired");
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
    throw localizedError("errors.sessionExpired");
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
    const error = localizedError("errors.sessionInvalid");
    showLogin(error);
    throw error;
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw localizedError("errors.apiRequest", { status: response.status });
  }
  return payload;
}

function showLogin(error = null) {
  state.loginError = error;
  $("login-view").classList.remove("hidden");
  $("dashboard-view").classList.add("hidden");
  $("logout-button").classList.add("hidden");
  $("login-error").textContent = errorMessage(error);
}

function showDashboard() {
  state.loginError = null;
  $("login-view").classList.add("hidden");
  $("dashboard-view").classList.remove("hidden");
  $("logout-button").classList.remove("hidden");
  $("signed-in-as").textContent = t("dynamic.signedInAs", { email: state.email });
}

function renderModel(model) {
  state.model = model;
  $("model-cards").classList.remove("skeleton-grid");
  $("model-cards").innerHTML = `
    <article><span>${t("dashboard.champion")}</span><strong>${model.model.replaceAll("_", " ")}</strong></article>
    <article><span>${t("dashboard.version")}</span><strong>${model.model_version}</strong></article>
    <article><span>${t("dashboard.threshold")}</span><strong>${formatPercentage(model.threshold)}</strong></article>
    <article><span>${t("dashboard.validation")}</span><strong>${formatPercentage(model.selection_value, 2)}</strong></article>`;
}

function sampleLabel(sample) {
  return t("dynamic.machineOption", {
    machine: sample.machine_id,
    date: formatDate(sample.observed_at),
    outcome: t(sample.actual_failure_within_horizon ? "dynamic.failure" : "dynamic.healthy"),
  });
}

function renderSampleOptions(dataset, selectedIndex = null) {
  state.dataset = dataset;
  state.samples = dataset.samples;
  const split = dataset.split.toLowerCase() === "test"
    ? t("dynamic.test")
    : dataset.split.toUpperCase();
  $("dataset-badge").textContent = t("dynamic.dataset", {
    split,
    count: dataset.samples.length,
  });
  const select = $("sample-select");
  const previousIndex = selectedIndex ?? Number(select.value || 0);
  select.innerHTML = dataset.samples
    .map((sample, index) => `<option value="${index}">${sampleLabel(sample)}</option>`)
    .join("");
  select.value = String(Math.min(previousIndex, Math.max(dataset.samples.length - 1, 0)));
  renderSelectedSample();
}

function selectedSample() {
  return state.samples[Number($("sample-select").value || 0)];
}

function renderSelectedSample() {
  const sample = selectedSample();
  if (!sample) return;
  const outcome = t(
    sample.actual_failure_within_horizon
      ? "dynamic.failureInHorizon"
      : "dynamic.noFailureInHorizon",
  );
  $("sample-meta").innerHTML = `
    <div><span>${t("dynamic.machine")}</span><strong>#${sample.machine_id}</strong></div>
    <div><span>${t("dynamic.observed")}</span><strong>${formatDate(sample.observed_at)}</strong></div>
    <div><span>${t("dynamic.heldOutOutcome")}</span><strong class="${sample.actual_failure_within_horizon ? "warn" : "ok"}">${outcome}</strong></div>`;
  renderFeatures(sample.features);
}

function renderFeatures(features) {
  const entries = Object.entries(features);
  const visible = state.showAllFeatures ? entries : entries.slice(0, 10);
  $("feature-table").innerHTML = visible
    .map(([name, value]) => {
      const formatted = typeof value === "number"
        ? Number(value).toLocaleString(locale(), { minimumFractionDigits: 3, maximumFractionDigits: 3 })
        : value;
      return `<div><span>${featureLabel(name)}</span><strong>${formatted}</strong></div>`;
    })
    .join("");
  $("toggle-features").textContent = state.showAllFeatures
    ? t("dynamic.showLess")
    : t("dynamic.showAllCount", { count: entries.length });
}

function renderResult(sample, prediction) {
  const probability = prediction.failure_probability;
  const degrees = Math.max(0, Math.min(360, probability * 360));
  $("probability-gauge").style.setProperty("--probability", `${degrees}deg`);
  $("probability-value").textContent = formatPercentage(probability);
  $("alert-value").textContent = t(
    prediction.alert ? "dynamic.maintenanceAlert" : "dynamic.continueOperation",
  );
  $("alert-value").className = prediction.alert ? "warn" : "ok";
  const correct = prediction.alert === sample.actual_failure_within_horizon;
  $("ground-truth").textContent = t(
    correct ? "dynamic.decisionMatch" : "dynamic.decisionMismatch",
  );
  $("result-state").textContent = t(correct ? "dynamic.match" : "dynamic.mismatch");
  $("result-state").className = `tag ${correct ? "success" : "danger"}`;
}

function renderHistory() {
  const history = state.history;
  const correct = history.filter((item) => item.correct).length;
  const alerts = history.filter((item) => item.prediction.alert).length;
  const mean = history.length
    ? history.reduce((sum, item) => sum + item.prediction.failure_probability, 0) / history.length
    : 0;
  $("run-count").textContent = t(
    history.length === 1 ? "dynamic.runsOne" : "dynamic.runsMany",
    { count: history.length },
  );
  $("correct-count").textContent = String(correct);
  $("alert-count").textContent = String(alerts);
  $("mean-probability").textContent = formatPercentage(mean);
  if (!history.length) {
    $("history-chart").innerHTML = `<p class="empty-state">${t("dashboard.historyEmpty")}</p>`;
    return;
  }
  $("history-chart").innerHTML = history
    .slice(-12)
    .map((item) => {
      const percentage = item.prediction.failure_probability * 100;
      return `<div class="history-row">
        <span>M${item.sample.machine_id}</span>
        <div><i style="width:${Math.max(2, percentage)}%" class="${item.prediction.alert ? "alert-bar" : "healthy-bar"}"></i></div>
        <strong>${formatPercentage(item.prediction.failure_probability)}</strong>
      </div>`;
    })
    .join("");
}

function applyTranslations() {
  document.documentElement.lang = state.language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
  document.querySelectorAll(".language-button").forEach((button) => {
    const active = button.dataset.language === state.language;
    const languageName = t(
      button.dataset.language === "en" ? "language.english" : "language.hungarian",
    );
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
    button.setAttribute("aria-label", languageName);
    button.title = languageName;
  });
  $("service-status").textContent = t(state.model ? "status.online" : "status.secure");
  if (state.email && !$("dashboard-view").classList.contains("hidden")) {
    $("signed-in-as").textContent = t("dynamic.signedInAs", { email: state.email });
  }
  if (state.model) renderModel(state.model);
  if (state.dataset) renderSampleOptions(state.dataset);
  if (state.history.length) {
    const latest = state.history[state.history.length - 1];
    renderResult(latest.sample, latest.prediction);
  }
  renderHistory();
  $("login-error").textContent = errorMessage(state.loginError);
  $("inference-error").textContent = errorMessage(state.inferenceError);
}

function setLanguage(language) {
  if (!SUPPORTED_LANGUAGES.includes(language)) return;
  state.language = language;
  localStorage.setItem("predmaint.language", language);
  applyTranslations();
}

async function loadWorkspace() {
  showDashboard();
  const [model, dataset] = await Promise.all([
    apiFetch("/v1/model-info"),
    apiFetch("/v1/demo-samples"),
  ]);
  renderModel(model);
  renderSampleOptions(dataset);
  $("service-status").textContent = t("status.online");
}

document.querySelectorAll(".language-button").forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.language));
});

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  state.loginError = null;
  $("login-error").textContent = "";
  $("login-button").disabled = true;
  try {
    await signIn($("email").value.trim(), $("password").value);
    $("password").value = "";
    await loadWorkspace();
  } catch (error) {
    showLogin(error);
  } finally {
    $("login-button").disabled = false;
  }
});

$("logout-button").addEventListener("click", () => {
  clearSession();
  state.history = [];
  state.inferenceError = null;
  showLogin();
  applyTranslations();
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
  state.inferenceError = null;
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
    state.inferenceError = error;
    $("inference-error").textContent = errorMessage(error);
  } finally {
    $("predict-button").disabled = false;
  }
});

applyTranslations();

if (!config.firebaseApiKey || !config.firebaseProjectId || !config.apiBaseUrl) {
  showLogin(localizedError("errors.missingConfig"));
} else if (state.token || state.refreshToken) {
  loadWorkspace().catch((error) => showLogin(error));
} else {
  showLogin();
}
