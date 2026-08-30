const ENV = window.StudySyncEnv || {};

const dashboardGreeting = document.getElementById("dashboardGreeting");
const pressureRange = document.getElementById("pressureRange");
const upcomingDeadlineList = document.getElementById("upcomingDeadlineList");
const upcomingEmpty = document.getElementById("upcomingEmpty");
const smartRecommendationText = document.getElementById("smartRecommendationText");
const quickLogBtn = document.querySelector(".dashboard-quick-log-btn");

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
    return { error: "unauthorized" };
  }
  return { response, data };
}

function renderDeadlines(tasks) {
  upcomingDeadlineList.innerHTML = "";
  if (!tasks.length) {
    upcomingEmpty.classList.remove("hidden");
    return;
  }
  upcomingEmpty.classList.add("hidden");

  tasks.slice(0, 2).forEach((task) => {
    const card = document.createElement("article");
    card.className = "dashboard-deadline-card";
    card.innerHTML = `
      <p class="dashboard-deadline-title">${task.title || "Untitled task"}</p>
      <div class="dashboard-deadline-row">
        <span class="dashboard-due-text">${task.due_text || "No due date"}</span>
        <span class="dashboard-priority-pill ${task.urgency_class || "medium"}">${task.urgency_text || "Medium"}</span>
      </div>
    `;
    upcomingDeadlineList.appendChild(card);
  });
}

async function initDashboard() {
  quickLogBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    toPage("/log");
  });

  const meResult = await fetchJson("/api/auth/me");
  if (meResult.error || !meResult.response?.ok) {
    return;
  }

  const user = meResult.data.user || {};
  const firstName = String(user.full_name || "User").trim().split(/\s+/)[0];
  dashboardGreeting.textContent = `Hi ${firstName}`;

  const summaryResult = await fetchJson("/api/dashboard/summary");
  if (summaryResult.error || !summaryResult.response?.ok) {
    return;
  }
  const summary = summaryResult.data || {};
  const upcomingTasks = summary.upcoming_tasks || [];
  pressureRange.value = String(summary.pressure_score || 10);
  renderDeadlines(upcomingTasks);
  smartRecommendationText.textContent = summary.smart_text || "No recommendation yet.";
}

initDashboard();
