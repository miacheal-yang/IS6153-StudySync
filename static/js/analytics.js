const ENV = window.StudySyncEnv || {};

const dom = {
  subjectList: document.getElementById("analyticsSubjectList"),
  subjectEmpty: document.getElementById("analyticsSubjectEmpty"),
  taskBars: document.getElementById("analyticsTaskBars"),
  taskMeta: document.getElementById("analyticsTaskMeta"),
  dayList: document.getElementById("analyticsDayList"),
  dayMeta: document.getElementById("analyticsDayMeta"),
  exportCsvBtn: document.getElementById("analyticsExportCsvBtn"),
  exportPdfBtn: document.getElementById("analyticsExportPdfBtn"),
  exportMsg: document.getElementById("analyticsExportMsg"),
};

const weekDays = ["M", "T", "W", "T", "F", "S", "S"];

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

async function fetchJson(path) {
  const response = await fetch(apiUrl(path), { credentials: "include" });
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) {
    toPage(data.redirect || "/");
    return { error: "unauthorized", data };
  }
  return { response, data };
}

function renderSubjectHours(rows) {
  if (!dom.subjectList) {
    return;
  }

  dom.subjectList.innerHTML = "";
  if (!rows.length) {
    dom.subjectEmpty?.classList.remove("hidden");
    return;
  }

  dom.subjectEmpty?.classList.add("hidden");
  const maxMinutes = Math.max(...rows.map((item) => Number(item.minutes || 0)), 1);
  rows.forEach((item) => {
    const subject = String(item.subject || "General");
    const minutes = Number(item.minutes || 0);
    const hours = Number(item.hours || 0);
    const row = document.createElement("div");
    row.className = "analytics-subject-row";
    row.innerHTML = `
      <span class="analytics-subject-name">${subject}</span>
      <div class="analytics-subject-track"><span class="analytics-subject-fill" style="width:${Math.max(
        10,
        Math.round((minutes / maxMinutes) * 100),
      )}%"></span></div>
      <span class="analytics-subject-value">${hours}h</span>
    `;
    dom.subjectList.appendChild(row);
  });
}

function renderTaskCompletion(taskCompletion) {
  if (!dom.taskBars || !dom.taskMeta) {
    return;
  }
  const total = Number(taskCompletion.total || 0);
  const done = Number(taskCompletion.done || 0);
  const rate = Number(taskCompletion.rate || 0);

  dom.taskBars.innerHTML = "";
  const segments = [20, 40, 60, 80, 100];
  segments.forEach((mark) => {
    const col = document.createElement("span");
    col.className = "analytics-task-col";
    const height = mark <= rate ? 42 + mark * 0.5 : 26;
    col.style.height = `${height}px`;
    col.classList.toggle("active", mark <= rate);
    dom.taskBars.appendChild(col);
  });

  dom.taskMeta.textContent = total
    ? `${done} / ${total} tasks done (${rate}%)`
    : "No task records yet.";
}

function renderProductiveDay(productiveDay) {
  if (!dom.dayList || !dom.dayMeta) {
    return;
  }
  const totals = Array.isArray(productiveDay.weekday_minutes) ? productiveDay.weekday_minutes : [0, 0, 0, 0, 0, 0, 0];
  const max = Number(productiveDay.top_minutes || 0);

  dom.dayList.innerHTML = "";
  weekDays.forEach((label, idx) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "analytics-day-chip";
    chip.innerHTML = `<span class="analytics-day-label">${label}</span><span class="analytics-day-pill"></span>`;
    if (max > 0 && totals[idx] === max) {
      chip.classList.add("active");
    }
    dom.dayList.appendChild(chip);
  });

  if (max <= 0) {
    dom.dayMeta.textContent = "No study history yet.";
    return;
  }
  const names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const topDays = totals
    .map((value, idx) => ({ value, idx }))
    .filter((item) => item.value === max)
    .map((item) => names[item.idx]);
  const topHours = Math.round((max / 60) * 10) / 10;
  dom.dayMeta.textContent = `Top day: ${topDays.join(", ")} (${topHours}h logged)`;
}

function setExportMessage(text, isError = false) {
  if (!dom.exportMsg) {
    return;
  }
  dom.exportMsg.textContent = text || "";
  dom.exportMsg.style.color = isError ? "var(--danger)" : "var(--subtle)";
}

function triggerCsvExport() {
  const url = apiUrl("/api/export/csv");
  window.location.href = url;
}

async function triggerPdfExport() {
  setExportMessage("");
  const result = await fetchJson("/api/export/pdf");
  if (result.error || !result.response || !result.response.ok) {
    setExportMessage(result.data?.error || "Failed to export PDF.", true);
    return;
  }
  setExportMessage(result.data.message || "PDF exported.");
}

async function init() {
  const result = await fetchJson("/api/analytics/view");
  if (result.error) {
    return;
  }
  if (result.response?.status === 403) {
    setExportMessage(result.data?.error || "Premium only.", true);
    return;
  }
  if (!result.response?.ok) {
    setExportMessage("Failed to load analytics data.", true);
    return;
  }
  renderSubjectHours(result.data.subject_hours || []);
  renderTaskCompletion(result.data.task_completion || {});
  renderProductiveDay(result.data.productive_day || {});
}

dom.exportCsvBtn?.addEventListener("click", triggerCsvExport);
dom.exportPdfBtn?.addEventListener("click", triggerPdfExport);

init();
