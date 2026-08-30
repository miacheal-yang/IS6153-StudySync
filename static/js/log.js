const ENV = window.StudySyncEnv || {};
const logForm = document.getElementById("logForm");
const subjectSelect = document.getElementById("subjectSelect");
const hoursInput = document.getElementById("hoursInput");
const minutesSelect = document.getElementById("minutesSelect");
const dateTimeInput = document.getElementById("dateTimeInput");
const noteInput = document.getElementById("noteInput");
const saveEntryBtn = document.getElementById("saveEntryBtn");
const logError = document.getElementById("logError");
const logSuccess = document.getElementById("logSuccess");
const starButtons = Array.from(document.querySelectorAll(".log-star-btn"));

let selectedMood = "";
let selectedRating = 4;
let currentSubjects = [];

function apiUrl(path) {
  return typeof ENV.apiUrl === "function" ? ENV.apiUrl(path) : path;
}

function toPage(path) {
  if (typeof ENV.toPage === "function") {
    ENV.toPage(path);
    return;
  }
  window.location.href = path;
}

function setError(message) {
  logError.textContent = message || "";
}

function setSuccess(message) {
  logSuccess.textContent = message || "";
  logSuccess.classList.toggle("hidden", !message);
}

function parseHours() {
  const parsed = Number.parseInt(hoursInput.value || "0", 10);
  if (Number.isNaN(parsed)) {
    return 0;
  }
  return Math.min(12, Math.max(0, parsed));
}

function parseMinutes() {
  const parsed = Number.parseInt(minutesSelect.value || "0", 10);
  if (Number.isNaN(parsed)) {
    return 0;
  }
  return parsed;
}

function selectedSubjectName() {
  return String(subjectSelect.value || "").trim();
}

function totalDurationMinutes() {
  return parseHours() * 60 + parseMinutes();
}

function refreshSaveState() {
  const subjectOk = selectedSubjectName();
  const durationOk = totalDurationMinutes() > 0;
  saveEntryBtn.disabled = !(subjectOk && durationOk);
}

function setRating(nextRating) {
  selectedRating = nextRating;
  selectedMood = nextRating >= 4 ? "focused" : nextRating >= 3 ? "neutral" : "low";
  starButtons.forEach((btn) => {
    const value = Number(btn.dataset.rating || "0");
    const isActive = value <= nextRating;
    btn.classList.toggle("active", isActive);
    btn.textContent = isActive ? "★" : "☆";
    btn.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

async function requestJson(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    credentials: "include",
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  return { response, data };
}

function renderSubjectOptions(subjects, selected = "") {
  subjectSelect.innerHTML = "";

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Select a subject";
  subjectSelect.appendChild(placeholder);

  subjects.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.name;
    option.textContent = item.name;
    subjectSelect.appendChild(option);
  });

  if (selected && subjects.some((item) => item.name === selected)) {
    subjectSelect.value = selected;
  } else {
    subjectSelect.value = "";
  }
  refreshSaveState();
}

async function loadSubjects(selected = "") {
  const { response, data } = await requestJson("/api/subjects");
  if (!response.ok) {
    setError(data.error || "Failed to load subjects.");
    return;
  }
  currentSubjects = data.subjects || [];
  renderSubjectOptions(currentSubjects, selected);
}

function applyPrefillFromQuery() {
  const query = new URLSearchParams(window.location.search);
  const subject = String(query.get("subject") || "").trim();
  const duration = Number.parseInt(query.get("duration") || "0", 10);
  const date = String(query.get("date") || "").trim();

  if (subject) {
    if (!currentSubjects.some((item) => item.name.toLowerCase() === subject.toLowerCase())) {
      currentSubjects.push({ id: "", name: subject });
    }
    currentSubjects = currentSubjects.sort((a, b) => a.name.localeCompare(b.name));
    renderSubjectOptions(currentSubjects, subject);
  }

  if (!Number.isNaN(duration) && duration > 0) {
    const hours = Math.min(12, Math.floor(duration / 60));
    const minutes = duration % 60;
    hoursInput.value = String(hours);
    if ([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55].includes(minutes)) {
      minutesSelect.value = String(minutes);
    }
  }

  if (date && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
    dateTimeInput.value = `${date}T09:00`;
  }
}

async function saveEntry() {
  setError("");
  setSuccess("");

  const subject = selectedSubjectName();
  const hours = parseHours();
  const minutes = parseMinutes();

  if (!subject) {
    setError("Please select a subject.");
    return;
  }
  if (hours === 0 && minutes === 0) {
    setError("Please enter a duration.");
    return;
  }

  saveEntryBtn.disabled = true;
  const selectedDateTime = String(dateTimeInput.value || "").trim();
  const fallbackDateTime = new Date().toISOString();
  const { response, data } = await requestJson("/api/logs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      date: (selectedDateTime || fallbackDateTime).slice(0, 10),
      subject,
      hours,
      minutes,
      mood: selectedMood || "neutral",
      note: String(noteInput.value || "").trim(),
    }),
  });
  if (!response.ok) {
    setError(data.error || "Failed to save log.");
    refreshSaveState();
    return;
  }

  setSuccess(`Saved successfully. Current streak: ${data.streak_days || 0} day(s).`);
  noteInput.value = "";
  hoursInput.value = "1";
  minutesSelect.value = "30";
  dateTimeInput.value = "";
  setRating(4);
  renderSubjectOptions(currentSubjects, "");
  refreshSaveState();

  setTimeout(() => {
    toPage("/dashboard");
  }, 900);
}

subjectSelect.addEventListener("change", () => {
  refreshSaveState();
});

hoursInput.addEventListener("input", () => {
  hoursInput.value = String(parseHours());
  refreshSaveState();
});

minutesSelect.addEventListener("change", refreshSaveState);
dateTimeInput.addEventListener("change", () => setError(""));
noteInput.addEventListener("input", () => setError(""));
logForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  saveEntry();
});

starButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    setRating(Number(btn.dataset.rating || "4"));
  });
});

async function init() {
  await loadSubjects();
  applyPrefillFromQuery();
  setRating(4);
  refreshSaveState();
}

init();
