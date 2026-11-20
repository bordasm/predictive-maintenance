const config = window.PREDMAINT_CONFIG || {};
const SUPPORTED_LANGUAGES = ["en", "hu"];
const DEFAULT_LANGUAGE = "en";
const MODEL_LABELS = {
  hist_gradient_boosting: "HistGradientBoosting",
  lstm: "LSTM",
  transformer: "Transformer",
};

const translations = {
  en: {
    brand: {
      home: "RailSense home",
      name: "RailSense - not only for railways (this is a demo)",
    },
    language: { selector: "Language", english: "English", hungarian: "Hungarian" },
    nav: { signOut: "Sign out" },
    common: { close: "Close" },
    logout: {
      eyebrow: "CONFIRM SIGN OUT",
      title: "Do you really want to sign out?",
      body: "Your inference history for this browser session will be cleared.",
      yes: "Yes",
      no: "No",
    },
    details: {
      eyebrow: "INPUT EXPLAINER",
      title: "What input does the selected model receive?",
      intro: "The selected endpoint is a feature-engineered snapshot for one machine. The exact model input depends on the selected inference model.",
      oneRowTitle: "Why only one row?",
      oneRowBody: "HistGradientBoosting scores the displayed endpoint row. LSTM and Transformer receive a complete 48-hour sequence ending at that same row.",
      measuredTitle: "Direct measurements",
      measuredBody: "Voltage, rotational speed, pressure and vibration are sensor readings measured at the observation time.",
      calculatedTitle: "Calculated features",
      calculatedBody: "These include 3-hour and 24-hour rolling means and standard deviations, error counts from the preceding 24 hours, and days since each component was maintained.",
      contextTitle: "Machine context",
      contextBody: "Machine age and model category provide additional context. The machine ID and observation time are used for traceability, not as model features.",
      allFeatures: "Panel 04, “Observation features”, shows every value in the endpoint row. For LSTM and Transformer, the REST request additionally contains the preceding 47 hourly rows.",
    },
    status: { secure: "Secure model workspace", online: "Inference models online" },
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
      noAccount: "Don't have an account yet?",
      securityNote: "Credentials are verified by Google Identity Platform.",
    },
    guest: {
      tryDemo: "Try demo",
      eyebrow: "PUBLIC DEMO",
      title: "Try RailSense as a guest",
      intro: "A temporary guest session lets you explore the held-out test data and all three inference models without an account.",
      limitDuration: "The session expires after 1 hour.",
      limitBatch: "You can evaluate up to 10 observations in one run.",
      limitTotal: "You can evaluate 30 observations during the session.",
      limitSessions: "One source address can start up to 3 guest sessions per hour.",
      limitData: "Only the held-out demonstration dataset is available.",
      registeredBenefit: "Administrator-approved registered accounts do not have these guest-mode limits.",
      start: "Start guest session",
      bannerTitle: "Guest demo session",
      remaining: "{count} of 30 observations remaining",
      viewLimits: "View limits",
      sampleSelection: "Guest observation selection",
      selectionHelp: "Select up to 10 observations for one inference run.",
      signedIn: "Temporary guest session",
    },
    access: {
      eyebrow: "REQUEST DEMO ACCESS",
      title: "Ask for a user account",
      guidance: "If you would like an account, enter your email address and tell us who you are and why you want to try the demo—for example, personal curiosity or an interest in developing a business solution. Then select “Request access”.",
      email: "Email address",
      message: "Message",
      remaining: "{count} characters remaining",
      submit: "Request access",
      successTitle: "Request received",
      successBody: "Your request has been recorded. If it is approved, Bordás Márton will reply from bordas.marton@gmail.com. You will set your own password through a secure Firebase link; no password is sent by email.",
    },
    dashboard: {
      eyebrow: "SELECTABLE MODELS · LIVE INFERENCE",
      cockpit: "Machine health cockpit",
      modelStatus: "MODEL STATUS",
      ready: "Ready",
      champion: "Selected model",
      loading: "Loading…",
      version: "Version",
      threshold: "Decision threshold",
      validation: "Validation PR-AUC",
      selectObservation: "Select held-out observation",
      testSplit: "TEST SPLIT",
      machineObservation: "Machine observation",
      selectModel: "Inference model",
      details: "Details",
      runInference: "Run inference",
      inferenceResult: "Inference result",
      waiting: "WAITING",
      failureProbability: "failure probability",
      decision24h: "Prediction for the next 24 hours",
      noInference: "No inference yet",
      decisionHelp: "Run inference to see whether the model expects a failure in the next 24 hours.",
      selectToCompare: "Select a test observation to compare prediction and outcome.",
      sessionDashboard: "Session dashboard",
      zeroRuns: "0 RUNS",
      correctDecisions: "Correct decisions",
      alerts: "Alerts",
      meanProbability: "Mean probability",
      historyEmpty: "Inference results will appear here.",
      observationFeatures: "Observation features",
      showAll: "Show all",
      rowInput: "One engineered feature row",
      windowInput: "48 consecutive hourly feature rows",
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
      failureExpected24h: "A failure is expected within the next 24 hours.",
      noFailureExpected24h: "No failure is expected within the next 24 hours.",
      aboveThreshold: "The predicted failure probability meets or exceeds the decision threshold, so the model raises a maintenance alert for the 24-hour horizon.",
      belowThreshold: "The predicted failure probability is below the decision threshold, so the model does not raise a maintenance alert for the 24-hour horizon.",
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
      accessRequestInvalid: "Check the email address and message, then try again.",
      accessRequestLimited: "A request has already been sent recently. Please try again later.",
      accessRequestUnavailable: "The request could not be sent right now. Please try again later.",
      guestUnavailable: "Guest mode is temporarily unavailable. Please try again later.",
      guestLimited: "The guest-session limit has been reached. Please try again later or request a registered account.",
      guestSelection: "Select between 1 and 10 observations.",
      guestQuota: "This guest session has reached its inference limit.",
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
    brand: {
      home: "RailSense kezdőlap",
      name: "RailSense – nem csak vasutakhoz (ez egy demó)",
    },
    language: { selector: "Nyelv", english: "Angol", hungarian: "Magyar" },
    nav: { signOut: "Kijelentkezés" },
    common: { close: "Bezárás" },
    logout: {
      eyebrow: "KIJELENTKEZÉS MEGERŐSÍTÉSE",
      title: "Valóban ki akar lépni?",
      body: "A jelenlegi böngésző-munkamenet inference-előzményei törlődnek.",
      yes: "Igen",
      no: "Nem",
    },
    details: {
      eyebrow: "BEMENETI ADATOK MAGYARÁZATA",
      title: "Milyen bemenetet kap a kiválasztott modell?",
      intro: "A kiválasztott végpont egy gép adott időpontra vonatkozó, előkészített feature-pillanatképe. A tényleges modellbemenet a kiválasztott modelltől függ.",
      oneRowTitle: "Miért csak egy sor?",
      oneRowBody: "A HistGradientBoosting a megjelenített végponti sort értékeli. Az LSTM és a Transformer az ugyanennél a sornál végződő, teljes 48 órás sorozatot kapja.",
      measuredTitle: "Közvetlenül mért adatok",
      measuredBody: "A feszültség, a fordulatszám, a nyomás és a rezgés a megfigyelés időpontjában mért szenzoradat.",
      calculatedTitle: "Számított jellemzők",
      calculatedBody: "Ide tartoznak a 3 és 24 órás gördülő átlagok és szórások, az előző 24 óra hibaszámlálói, valamint az egyes komponensek karbantartása óta eltelt napok.",
      contextTitle: "Gépkontextus",
      contextBody: "A gép életkora és modellkategóriája további kontextust ad. A gépazonosító és a megfigyelési idő a nyomon követést szolgálja, nem modell-feature.",
      allFeatures: "A 04-es, „A megfigyelés jellemzői” panel a végponti sor összes értékét mutatja. Az LSTM és a Transformer REST-kérése ezen felül az előző 47 órás sort is tartalmazza.",
    },
    status: { secure: "Biztonságos modell-munkatér", online: "Az inference modellek elérhetők" },
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
      noAccount: "Nincs még felhasználója?",
      securityNote: "A hitelesítő adatokat a Google Identity Platform ellenőrzi.",
    },
    guest: {
      tryDemo: "Demo kipróbálása",
      eyebrow: "NYILVÁNOS DEMÓ",
      title: "Próbáld ki a RailSense-t vendégként",
      intro: "Az ideiglenes vendégmunkamenettel fiók nélkül kipróbálhatod az elkülönített tesztadatokat és mindhárom inference modellt.",
      limitDuration: "A munkamenet 1 óra után lejár.",
      limitBatch: "Egy futásban legfeljebb 10 megfigyelést értékelhetsz.",
      limitTotal: "A munkamenet alatt összesen 30 megfigyelést értékelhetsz.",
      limitSessions: "Egy forráscím óránként legfeljebb 3 vendégmunkamenetet indíthat.",
      limitData: "Csak az elkülönített demonstrációs adatkészlet érhető el.",
      registeredBenefit: "Az adminisztrátor által jóváhagyott regisztrált fiókokra ezek a vendégmód-korlátok nem vonatkoznak.",
      start: "Vendégmunkamenet indítása",
      bannerTitle: "Vendég demómunkamenet",
      remaining: "30 megfigyelésből még {count} értékelhető",
      viewLimits: "Korlátok megtekintése",
      sampleSelection: "Vendég megfigyelésválasztás",
      selectionHelp: "Válassz ki 1–10 megfigyelést egy inference-futtatáshoz.",
      signedIn: "Ideiglenes vendégmunkamenet",
    },
    access: {
      eyebrow: "DEMÓ-HOZZÁFÉRÉS KÉRÉSE",
      title: "Felhasználó kérése",
      guidance: "Ha szeretne felhasználót kérni, adja meg az e-mail-címét, az üzenetben pedig írja le, hogy ki Ön, és milyen célból szeretné kipróbálni a felületet – például személyes kíváncsiságból, vagy mert üzleti megoldást szeretne kifejlesztetni. Ezután kattintson a „Felhasználó kérése” gombra.",
      email: "E-mail-cím",
      message: "Üzenet",
      remaining: "Még {count} karakter írható be",
      submit: "Felhasználó kérése",
      successTitle: "A kérelem megérkezett",
      successBody: "A kérelmet rögzítettük. Jóváhagyás esetén Bordás Márton válaszol a bordas.marton@gmail.com címről. A jelszavát Ön állítja majd be egy biztonságos Firebase-linken; jelszót nem küldünk e-mailben.",
    },
    dashboard: {
      eyebrow: "VÁLASZTHATÓ MODELLEK · ÉLŐ INFERENCE",
      cockpit: "Gépállapot-irányítópult",
      modelStatus: "MODELLÁLLAPOT",
      ready: "Üzemkész",
      champion: "Kiválasztott modell",
      loading: "Betöltés…",
      version: "Verzió",
      threshold: "Döntési küszöb",
      validation: "Validációs PR-AUC",
      selectObservation: "Válassz elkülönített tesztmegfigyelést",
      testSplit: "TESZTHALMAZ",
      machineObservation: "Gépmegfigyelés",
      selectModel: "Inference modell",
      details: "Részletek",
      runInference: "Inference futtatása",
      inferenceResult: "Inference eredménye",
      waiting: "VÁRAKOZÁS",
      failureProbability: "meghibásodási valószínűség",
      decision24h: "Előrejelzés a következő 24 órára",
      noInference: "Még nincs inference",
      decisionHelp: "Futtass inference-t annak megállapításához, hogy a modell vár-e hibát a következő 24 órában.",
      selectToCompare: "Válassz tesztmegfigyelést a predikció és a tényleges eredmény összehasonlításához.",
      sessionDashboard: "Munkamenet-irányítópult",
      zeroRuns: "0 FUTÁS",
      correctDecisions: "Helyes döntések",
      alerts: "Riasztások",
      meanProbability: "Átlagos valószínűség",
      historyEmpty: "Az inference eredményei itt jelennek meg.",
      observationFeatures: "A megfigyelés jellemzői",
      showAll: "Összes megjelenítése",
      rowInput: "Egy előkészített feature-sor",
      windowInput: "48 egymást követő órás feature-sor",
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
      failureExpected24h: "A következő 24 órában hiba várható.",
      noFailureExpected24h: "A következő 24 órában nem várható hiba.",
      aboveThreshold: "A becsült meghibásodási valószínűség eléri vagy meghaladja a döntési küszöböt, ezért a modell karbantartási riasztást ad a 24 órás időhorizontra.",
      belowThreshold: "A becsült meghibásodási valószínűség a döntési küszöb alatt marad, ezért a modell nem ad karbantartási riasztást a 24 órás időhorizontra.",
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
      accessRequestInvalid: "Ellenőrizze az e-mail-címet és az üzenetet, majd próbálja újra.",
      accessRequestLimited: "Erről a címről nemrég már érkezett kérelem. Próbálja újra később.",
      accessRequestUnavailable: "A kérelmet most nem sikerült elküldeni. Próbálja újra később.",
      guestUnavailable: "A vendégmód átmenetileg nem érhető el. Próbáld újra később.",
      guestLimited: "A vendégmunkamenetek korlátját elérted. Próbáld újra később, vagy kérj regisztrált fiókot.",
      guestSelection: "Válassz ki 1–10 megfigyelést.",
      guestQuota: "Ez a vendégmunkamenet elérte az inference-korlátját.",
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
  isGuest: sessionStorage.getItem("predmaint.isGuest") === "true",
  guestRemaining: Number(sessionStorage.getItem("predmaint.guestRemaining") || 30),
  language: storedLanguage(),
  samples: [],
  history: [],
  showAllFeatures: false,
  model: null,
  models: [],
  dataset: null,
  loginError: null,
  inferenceError: null,
  accessRequestError: null,
  guestError: null,
};

const $ = (id) => document.getElementById(id);
let activeModal = null;
let modalReturnFocus = null;

function modalFocusableElements(modal) {
  return [...modal.querySelectorAll(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )].filter((element) => !element.classList.contains("hidden"));
}

function openModal(id, trigger = document.activeElement) {
  const modal = $(id);
  if (!modal) return;
  if (activeModal && activeModal !== modal) closeModal(activeModal.id, false);
  modalReturnFocus = trigger;
  activeModal = modal;
  modal.classList.remove("hidden");
  document.body.classList.add("modal-open");
  modalFocusableElements(modal)[0]?.focus();
}

function closeModal(id = activeModal?.id, restoreFocus = true) {
  const modal = id ? $(id) : activeModal;
  if (!modal) return;
  modal.classList.add("hidden");
  document.body.classList.remove("modal-open");
  activeModal = null;
  const returnTarget = modalReturnFocus;
  modalReturnFocus = null;
  if (restoreFocus && returnTarget?.isConnected) returnTarget.focus();
}

function handleModalKeydown(event) {
  if (!activeModal) return;
  if (event.key === "Escape") {
    event.preventDefault();
    closeModal();
    return;
  }
  if (event.key !== "Tab") return;
  const focusable = modalFocusableElements(activeModal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

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

function updateCharacterCounters() {
  const emailRemaining = 100 - $("request-email").value.length;
  const messageRemaining = 1000 - $("request-message").value.length;
  $("request-email-counter").textContent = t("access.remaining", { count: emailRemaining });
  $("request-message-counter").textContent = t("access.remaining", { count: messageRemaining });
}

function resetAccessRequestForm() {
  $("access-request-form").reset();
  $("request-email").value = $("email").value.trim();
  state.accessRequestError = null;
  $("access-request-error").textContent = "";
  $("access-request-form-view").classList.remove("hidden");
  $("access-request-success").classList.add("hidden");
  $("submit-access-request").disabled = false;
  updateCharacterCounters();
}

async function submitAccessRequest() {
  const response = await fetch("/access-requests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: $("request-email").value.trim(),
      message: $("request-message").value.trim(),
      locale: state.language,
      website: $("request-website").value,
    }),
  });
  if (response.ok) return;
  if (response.status === 422) throw localizedError("errors.accessRequestInvalid");
  if (response.status === 429) throw localizedError("errors.accessRequestLimited");
  throw localizedError("errors.accessRequestUnavailable");
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

function modelLabel(name) {
  return MODEL_LABELS[name] ?? String(name || "—").replaceAll("_", " ");
}

function setSession(payload, email, { isGuest = false, storeRefreshToken = true } = {}) {
  state.token = payload.idToken;
  state.refreshToken = storeRefreshToken ? payload.refreshToken : null;
  state.expiresAt = Date.now() + Number(payload.expiresIn || 3600) * 1000;
  state.email = email;
  state.isGuest = isGuest;
  sessionStorage.setItem("predmaint.idToken", state.token);
  if (state.refreshToken) sessionStorage.setItem("predmaint.refreshToken", state.refreshToken);
  else sessionStorage.removeItem("predmaint.refreshToken");
  sessionStorage.setItem("predmaint.expiresAt", String(state.expiresAt));
  sessionStorage.setItem("predmaint.email", email);
  sessionStorage.setItem("predmaint.isGuest", String(isGuest));
  sessionStorage.setItem("predmaint.guestRemaining", String(state.guestRemaining));
}

function clearSession() {
  state.token = null;
  state.refreshToken = null;
  state.expiresAt = 0;
  state.email = null;
  state.isGuest = false;
  state.guestRemaining = 30;
  sessionStorage.removeItem("predmaint.idToken");
  sessionStorage.removeItem("predmaint.refreshToken");
  sessionStorage.removeItem("predmaint.expiresAt");
  sessionStorage.removeItem("predmaint.email");
  sessionStorage.removeItem("predmaint.isGuest");
  sessionStorage.removeItem("predmaint.guestRemaining");
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
  setSession(payload, email, { isGuest: false });
}

async function startGuestSession() {
  const sessionResponse = await fetch("/guest-session", { method: "POST" });
  const sessionPayload = await sessionResponse.json().catch(() => ({}));
  if (!sessionResponse.ok) {
    throw localizedError(
      sessionResponse.status === 429 ? "errors.guestLimited" : "errors.guestUnavailable",
    );
  }
  const endpoint = `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${encodeURIComponent(config.firebaseApiKey)}`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token: sessionPayload.customToken, returnSecureToken: true }),
  });
  const payload = await response.json();
  if (!response.ok) throw localizedError("errors.guestUnavailable");
  state.guestRemaining = Number(sessionPayload.maxObservations || 30);
  setSession(payload, "guest", { isGuest: true, storeRefreshToken: false });
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
    { isGuest: false },
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
    if (response.status === 429 && state.isGuest) {
      throw localizedError("errors.guestQuota");
    }
    throw localizedError("errors.apiRequest", { status: response.status });
  }
  return payload;
}

function showLogin(error = null) {
  if (activeModal) closeModal(activeModal.id, false);
  state.loginError = error;
  $("login-view").classList.remove("hidden");
  $("dashboard-view").classList.add("hidden");
  $("logout-button").classList.add("hidden");
  $("guest-banner").classList.add("hidden");
  $("login-error").textContent = errorMessage(error);
}

function showDashboard() {
  state.loginError = null;
  $("login-view").classList.add("hidden");
  $("dashboard-view").classList.remove("hidden");
  $("logout-button").classList.remove("hidden");
  $("signed-in-as").textContent = state.isGuest
    ? t("guest.signedIn")
    : t("dynamic.signedInAs", { email: state.email });
  $("guest-banner").classList.toggle("hidden", !state.isGuest);
  updateGuestRemaining();
}

function updateGuestRemaining() {
  $("guest-remaining").textContent = t("guest.remaining", { count: state.guestRemaining });
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

function renderModelOptions(registry) {
  state.models = registry.models;
  const select = $("model-select");
  select.innerHTML = registry.models.map((model) =>
    `<option value="${model.model}">${model.model.replaceAll("_", " ")}${model.is_default ? " ★" : ""}</option>`
  ).join("");
  select.value = state.model?.model || registry.default_model;
  selectModel(select.value);
}

function selectModel(name) {
  const model = state.models.find((item) => item.model === name);
  if (!model) return;
  renderModel(model);
  $("model-input-help").textContent = t(
    model.input_type === "sequence_window" ? "dashboard.windowInput" : "dashboard.rowInput",
  );
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
  select.classList.toggle("hidden", state.isGuest);
  $("guest-sample-list").classList.toggle("hidden", !state.isGuest);
  $("guest-selection-help").classList.toggle("hidden", !state.isGuest);
  if (state.isGuest) {
    $("guest-sample-list").innerHTML = dataset.samples.map((sample, index) => `
      <label class="guest-sample-option">
        <input type="checkbox" value="${index}" ${index === 0 ? "checked" : ""} />
        <span>${sampleLabel(sample)}</span>
      </label>`).join("");
  }
  renderSelectedSample();
}

function selectedSampleIndexes() {
  if (!state.isGuest) return [Number($("sample-select").value || 0)];
  return [...$("guest-sample-list").querySelectorAll('input[type="checkbox"]:checked')]
    .map((input) => Number(input.value));
}

function selectedSamples() {
  return selectedSampleIndexes().map((index) => state.samples[index]).filter(Boolean);
}

function selectedSample() {
  return selectedSamples()[0];
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

function renderResult(sample, prediction, model) {
  const probability = prediction.failure_probability;
  const degrees = Math.max(0, Math.min(360, probability * 360));
  $("probability-gauge").style.setProperty("--probability", `${degrees}deg`);
  $("probability-value").textContent = formatPercentage(probability);
  $("result-model").textContent = modelLabel(model);
  $("alert-value").textContent = t(
    prediction.alert ? "dynamic.failureExpected24h" : "dynamic.noFailureExpected24h",
  );
  $("alert-value").className = prediction.alert ? "warn" : "ok";
  $("decision-explanation").textContent = t(
    prediction.alert ? "dynamic.aboveThreshold" : "dynamic.belowThreshold",
  );
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
        <span>M${item.sample.machine_id} · ${modelLabel(item.model)}</span>
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
    $("signed-in-as").textContent = state.isGuest
      ? t("guest.signedIn")
      : t("dynamic.signedInAs", { email: state.email });
  }
  updateGuestRemaining();
  if (state.model) renderModel(state.model);
  if (state.models.length) selectModel(state.model?.model || state.models[0].model);
  if (state.dataset) renderSampleOptions(state.dataset);
  if (state.history.length) {
    const latest = state.history[state.history.length - 1];
    renderResult(latest.sample, latest.prediction, latest.model);
  }
  renderHistory();
  $("login-error").textContent = errorMessage(state.loginError);
  $("inference-error").textContent = errorMessage(state.inferenceError);
  $("access-request-error").textContent = errorMessage(state.accessRequestError);
  $("guest-error").textContent = errorMessage(state.guestError);
  updateCharacterCounters();
}

function setLanguage(language) {
  if (!SUPPORTED_LANGUAGES.includes(language)) return;
  state.language = language;
  localStorage.setItem("predmaint.language", language);
  applyTranslations();
}

async function loadWorkspace() {
  showDashboard();
  const [registry, dataset] = await Promise.all([
    apiFetch("/v1/models"),
    apiFetch("/v1/demo-samples"),
  ]);
  renderModelOptions(registry);
  renderSampleOptions(dataset);
  $("service-status").textContent = t("status.online");
}

document.querySelectorAll(".language-button").forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.language));
});

document.addEventListener("keydown", handleModalKeydown);

document.querySelectorAll("[data-close-modal]").forEach((button) => {
  button.addEventListener("click", () => closeModal(button.dataset.closeModal));
});

document.querySelectorAll(".modal-backdrop").forEach((modal) => {
  modal.addEventListener("mousedown", (event) => {
    if (event.target === modal) closeModal(modal.id);
  });
});

$("input-details-button").addEventListener("click", (event) => {
  openModal("input-details-modal", event.currentTarget);
});

$("open-guest-mode").addEventListener("click", (event) => {
  state.guestError = null;
  $("guest-error").textContent = "";
  openModal("guest-limits-modal", event.currentTarget);
});

$("guest-limits-button").addEventListener("click", (event) => {
  state.guestError = null;
  $("guest-error").textContent = "";
  openModal("guest-limits-modal", event.currentTarget);
});

$("start-guest-session").addEventListener("click", async () => {
  state.guestError = null;
  $("guest-error").textContent = "";
  $("start-guest-session").disabled = true;
  try {
    await startGuestSession();
    closeModal("guest-limits-modal", false);
    await loadWorkspace();
  } catch (error) {
    state.guestError = error;
    $("guest-error").textContent = errorMessage(error);
  } finally {
    $("start-guest-session").disabled = false;
  }
});

$("open-access-request").addEventListener("click", (event) => {
  resetAccessRequestForm();
  openModal("access-request-modal", event.currentTarget);
  $("request-email").focus();
});

$("request-email").addEventListener("input", updateCharacterCounters);
$("request-message").addEventListener("input", updateCharacterCounters);

$("access-request-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  state.accessRequestError = null;
  $("access-request-error").textContent = "";
  $("submit-access-request").disabled = true;
  try {
    await submitAccessRequest();
    $("access-request-form-view").classList.add("hidden");
    $("access-request-success").classList.remove("hidden");
    $("access-request-success").querySelector("button").focus();
  } catch (error) {
    state.accessRequestError = error;
    $("access-request-error").textContent = errorMessage(error);
  } finally {
    $("submit-access-request").disabled = false;
  }
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
  openModal("logout-modal", $("logout-button"));
});

$("cancel-logout-button").addEventListener("click", () => {
  closeModal("logout-modal");
});

$("confirm-logout-button").addEventListener("click", () => {
  closeModal("logout-modal", false);
  clearSession();
  state.history = [];
  state.inferenceError = null;
  showLogin();
  applyTranslations();
});

$("sample-select").addEventListener("change", renderSelectedSample);
$("guest-sample-list").addEventListener("change", (event) => {
  if (event.target.type !== "checkbox") return;
  const selected = selectedSampleIndexes();
  if (selected.length > 10) {
    event.target.checked = false;
    state.inferenceError = localizedError("errors.guestSelection");
    $("inference-error").textContent = errorMessage(state.inferenceError);
    return;
  }
  renderSelectedSample();
});
$("model-select").addEventListener("change", (event) => selectModel(event.target.value));

$("toggle-features").addEventListener("click", () => {
  state.showAllFeatures = !state.showAllFeatures;
  const sample = selectedSample();
  if (sample) renderFeatures(sample.features);
});

$("predict-button").addEventListener("click", async () => {
  const samples = selectedSamples();
  if (!samples.length || (state.isGuest && samples.length > 10)) {
    state.inferenceError = localizedError("errors.guestSelection");
    $("inference-error").textContent = errorMessage(state.inferenceError);
    return;
  }
  state.inferenceError = null;
  $("inference-error").textContent = "";
  $("predict-button").disabled = true;
  try {
    const payload = await apiFetch("/v1/predict", {
      method: "POST",
      body: JSON.stringify({
        model: state.model.model,
        observations: samples.map((sample) => ({
          observation_id: `${sample.sample_id}-${crypto.randomUUID()}`,
          machine_id: sample.machine_id,
          observed_at: sample.observed_at,
          features: sample.features,
          ...(state.model.input_type === "sequence_window" ? { sequence: sample.sequence } : {}),
        })),
      }),
    });
    payload.predictions.forEach((prediction, index) => {
      const sample = samples[index];
      state.history.push({
        sample,
        prediction,
        model: payload.model,
        correct: prediction.alert === sample.actual_failure_within_horizon,
      });
    });
    if (state.isGuest && payload.guest_observations_remaining != null) {
      state.guestRemaining = Number(payload.guest_observations_remaining);
      sessionStorage.setItem("predmaint.guestRemaining", String(state.guestRemaining));
      updateGuestRemaining();
    }
    renderResult(samples[0], payload.predictions[0], payload.model);
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
