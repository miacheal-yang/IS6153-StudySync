const ENV = window.StudySyncEnv || {};

const state = {
  selectedPriority: "low",
  subjects: [],
  tasks: [],
  filter: "all",
  view: "tasks",
  selectedDateKey: "",
  swipe: { id: null, startX: 0 },
};

const dom = {
  root: document.getElementById("tasksPageRoot"),
  form: document.getElementById("taskCreateForm"),
  subject: document.getElementById("taskSubject"),
  subjectDatalist: document.getElementById("taskSubjectDatalist"),
  title: document.getElementById("taskTitle"),
  deadline: document.getElementById("taskDeadline"),
  description: document.getElementById("taskDescription"),
  error: document.getElementById("taskFormError"),
  saveBtn: document.getElementById("saveTaskBtn"),
  priorityButtons: Array.from(document.querySelectorAll(".task-priority-btn")),
  taskList: document.getElementById("taskList"),
  taskListEmpty: document.getElementById("taskListEmpty"),
  filterTabs: Array.from(document.querySelectorAll(".task-filter-tab[data-filter]")),
  viewMenuBtn: document.getElementById("taskViewMenuBtn"),
  viewMenu: document.getElementById("taskViewMenu"),
  viewMenuItems: Array.from(document.querySelectorAll(".task-view-menu-item[data-view]")),
  taskListFilters: document.querySelector(".task-list-filters"),
  swipeHint: document.querySelector(".task-list-swipe-hint"),
  calendarWeekHeader: document.getElementById("taskCalendarWeekHeader"),
  calendarWeekGrid: document.getElementById("taskCalendarWeekGrid"),
  calendarSelectedDate: document.getElementById("taskCalendarSelectedDate"),
  calendarDayCardTitle: document.getElementById("taskCalendarDayCardTitle"),
  calendarDayCardMeta: document.getElementById("taskCalendarDayCardMeta"),
  calendarAddSessionBtn: document.getElementById("taskCalendarAddSessionBtn"),
  openModalBtn: document.getElementById("openAddTaskModal"),
  modal: document.getElementById("taskAddModal"),
  modalBackdrop: document.getElementById("taskAddModalBackdrop"),
  closeModalBtn: document.getElementById("closeAddTaskModal"),
};

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

function toTasksView(view) {
  const safeView = view === "calendar" ? "calendar" : "tasks";
  if (ENV.IS_PREVIEW && typeof ENV.templateUrl === "function") {
    window.location.href = ENV.templateUrl("/tasks", `?view=${safeView}`);
    return;
  }
  toPage(`/tasks?view=${safeView}`);
}

async function fetchJson(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    credentials: "include",
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) {
    toPage(data.redirect || "/");
    return { error: "unauthorized" };
  }
  return { response, data };
}

function toDateKey(value) {
  const d = value instanceof Date ? value : new Date(value);
  if (!d || Number.isNaN(d.getTime())) {
    return "";
  }
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function renderSubjects() {
  const dl = dom.subjectDatalist;
  if (!dl) {
    return;
  }
  const previous = String(dom.subject?.value || "").trim();
  dl.innerHTML = "";
  state.subjects.forEach((subject) => {
    const opt = document.createElement("option");
    opt.value = subject.name;
    dl.appendChild(opt);
  });
  if (previous && dom.subject) {
    dom.subject.value = previous;
  }
}

function subjectExistsInState(name) {
  const k = String(name).trim().toLowerCase();
  if (!k) {
    return false;
  }
  return state.subjects.some((s) => String(s.name).trim().toLowerCase() === k);
}

async function ensureSubjectOnServer(name) {
  const trimmed = String(name || "").trim();
  if (!trimmed) {
    return { ok: false, error: "Subject name is required." };
  }
  const result = await fetchJson("/api/subjects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: trimmed }),
  });
  if (result.error || !result.response.ok) {
    return { ok: false, error: result.data?.error || "Could not save subject." };
  }
  const savedName = result.data?.subject?.name || trimmed;
  return { ok: true, name: savedName };
}

async function loadSubjects() {
  const result = await fetchJson("/api/subjects");
  if (result.error || !result.response.ok) {
    return;
  }
  state.subjects = result.data.subjects || [];
  renderSubjects();
}

async function loadTasks() {
  const result = await fetchJson(`/api/tasks/view?filter=${encodeURIComponent(state.filter)}`);
  if (result.error || !result.response.ok) {
    return;
  }
  state.tasks = result.data.tasks || [];
  renderTaskList();
}

function renderTaskList() {
  if (!dom.taskList) {
    return;
  }
  const filtered = state.tasks;
  dom.taskList.innerHTML = "";

  if (!filtered.length) {
    dom.taskListEmpty.classList.remove("hidden");
    return;
  }
  dom.taskListEmpty.classList.add("hidden");

  filtered.forEach((task) => {
    const card = document.createElement("article");
    card.className = "task-list-card";
    card.dataset.taskId = String(task.id);

    const title = document.createElement("h3");
    title.className = "task-list-card-title";
    title.textContent = task.title || "Untitled task";
    if (task.is_done) {
      title.classList.add("task-list-card-title--done");
    }
    card.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "task-list-card-meta";

    if (task.is_done) {
      const row = document.createElement("p");
      row.className = "task-list-done-row";
      row.innerHTML =
        '<span class="task-list-done-icon" aria-hidden="true">\u2713</span><span>Completed</span>';
      meta.appendChild(row);
    } else {
      const dueEl = document.createElement("p");
      dueEl.className = `task-list-due ${task.due_class || ""}`;
      dueEl.textContent = task.due_text || "No due date";
      meta.appendChild(dueEl);

      const pillEl = document.createElement("span");
      pillEl.className = `task-list-pill ${task.pill_class || "task-list-pill--low"}`;
      pillEl.textContent = task.pill_text || "Low";
      meta.appendChild(pillEl);
    }

    card.appendChild(meta);
    dom.taskList.appendChild(card);

    if (!task.is_done) {
      attachSwipeToComplete(card, task.id);
    }
  });
}

async function loadCalendarWeek(dateKey) {
  if (!dom.calendarWeekGrid) {
    return;
  }
  const query = dateKey ? `?date=${encodeURIComponent(dateKey)}` : "";
  const result = await fetchJson(`/api/tasks/calendar/week${query}`);
  if (result.error || !result.response.ok) {
    return;
  }
  const payload = result.data || {};
  state.selectedDateKey = payload.selected_date || toDateKey(new Date());

  dom.calendarWeekHeader.innerHTML = "";
  (payload.days || []).forEach((day) => {
    const label = document.createElement("span");
    label.className = "task-calendar-weekday";
    label.textContent = day.label || "";
    dom.calendarWeekHeader.appendChild(label);
  });

  dom.calendarWeekGrid.innerHTML = "";
  (payload.days || []).forEach((day) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "task-calendar-day-btn";
    button.textContent = String(day.day || "");
    if (day.is_selected) {
      button.classList.add("selected");
    }
    if (day.has_study) {
      button.classList.add("has-study");
    }
    if (day.has_deadline) {
      button.classList.add("has-deadline");
    }
    button.addEventListener("click", () => {
      loadCalendarWeek(day.date);
    });
    dom.calendarWeekGrid.appendChild(button);
  });

  dom.calendarSelectedDate.textContent = payload.selected_title || "";
  const deadlines = payload.deadlines || [];
  if (!deadlines.length) {
    dom.calendarDayCardTitle.textContent = "No deadline tasks on this day";
    dom.calendarDayCardMeta.textContent = payload.has_study ? "Study session recorded." : "Tap another date.";
  } else {
    const first = deadlines[0];
    dom.calendarDayCardTitle.textContent = first.title || "Untitled task";
    dom.calendarDayCardMeta.textContent =
      deadlines.length > 1 ? `+${deadlines.length - 1} more tasks due` : "Tap to view task details";
  }
}

async function markTaskDone(taskId) {
  const result = await fetchJson(`/api/tasks/${taskId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "done" }),
  });
  if (result.error || !result.response.ok) {
    return;
  }
  await loadTasks();
}

function attachSwipeToComplete(card, taskId) {
  card.addEventListener(
    "touchstart",
    (e) => {
      const t = e.changedTouches[0];
      state.swipe = { id: taskId, startX: t.clientX };
    },
    { passive: true },
  );
  card.addEventListener(
    "touchend",
    (e) => {
      if (state.swipe.id !== taskId) {
        return;
      }
      const t = e.changedTouches[0];
      const delta = state.swipe.startX - t.clientX;
      if (delta > 56) {
        if ("vibrate" in navigator) {
          navigator.vibrate(12);
        }
        markTaskDone(taskId);
      }
      state.swipe = { id: null, startX: 0 };
    },
    { passive: true },
  );
}

function setFilter(next) {
  state.filter = next;
  dom.filterTabs.forEach((tab) => {
    const on = tab.dataset.filter === next;
    tab.classList.toggle("task-filter-tab--on", on);
    tab.setAttribute("aria-selected", on ? "true" : "false");
  });
  loadTasks();
}

function openAddTaskModal() {
  if (!dom.modal) {
    return;
  }
  dom.modal.classList.remove("hidden");
  dom.modal.setAttribute("aria-hidden", "false");
  dom.closeModalBtn?.focus();
}

function closeAddTaskModal() {
  if (!dom.modal) {
    return;
  }
  dom.modal.classList.add("hidden");
  dom.modal.setAttribute("aria-hidden", "true");
  dom.openModalBtn?.focus();
}

function setPriority(nextPriority) {
  state.selectedPriority = nextPriority;
  dom.priorityButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.priority === nextPriority);
  });
}

function mapPriorityValue() {
  return state.selectedPriority;
}

async function submitTask(event) {
  event.preventDefault();
  dom.error.textContent = "";
  dom.saveBtn.disabled = true;
  try {
    const rawSubject = String(dom.subject?.value || "").trim();
    if (!rawSubject) {
      dom.error.textContent = "Please select or type a subject.";
      return;
    }
    let subject = rawSubject;
    if (!subjectExistsInState(rawSubject)) {
      const ensured = await ensureSubjectOnServer(rawSubject);
      if (!ensured.ok) {
        dom.error.textContent = ensured.error;
        return;
      }
      subject = ensured.name || rawSubject;
      await loadSubjects();
      if (dom.subject) {
        dom.subject.value = subject;
      }
    }

    const payload = {
      subject,
      title: String(dom.title.value || "").trim(),
      deadline: String(dom.deadline.value || "").trim(),
      priority: mapPriorityValue(),
      description: String(dom.description.value || "").trim(),
      reminder: "Same day",
      reminder_offset_days: 0,
    };

    if (!payload.title) {
      dom.error.textContent = "Task name is required.";
      return;
    }

    const result = await fetchJson("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (result.error || !result.response.ok) {
      dom.error.textContent = result.data.error || "Unable to save task.";
      return;
    }

    dom.form.reset();
    setPriority("low");
    if (dom.subject) {
      dom.subject.value = "";
    }
    closeAddTaskModal();
    await loadTasks();
  } finally {
    dom.saveBtn.disabled = false;
  }
}

dom.priorityButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    setPriority(btn.dataset.priority || "low");
  });
});

dom.form?.addEventListener("submit", submitTask);

dom.filterTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    setFilter(tab.dataset.filter || "all");
  });
});

function openViewMenu() {
  dom.viewMenu?.classList.remove("hidden");
  dom.viewMenuBtn?.setAttribute("aria-expanded", "true");
}

function closeViewMenu() {
  dom.viewMenu?.classList.add("hidden");
  dom.viewMenuBtn?.setAttribute("aria-expanded", "false");
}

dom.viewMenuBtn?.addEventListener("click", () => {
  const isHidden = dom.viewMenu?.classList.contains("hidden");
  if (isHidden) {
    openViewMenu();
  } else {
    closeViewMenu();
  }
});

dom.viewMenuItems.forEach((item) => {
  item.addEventListener("click", () => {
    toTasksView(item.dataset.view || "tasks");
  });
});

dom.openModalBtn?.addEventListener("click", () => {
  openAddTaskModal();
});

dom.closeModalBtn?.addEventListener("click", () => {
  closeAddTaskModal();
});

dom.modalBackdrop?.addEventListener("click", () => {
  closeAddTaskModal();
});

dom.calendarAddSessionBtn?.addEventListener("click", () => {
  const key = state.selectedDateKey || toDateKey(new Date());
  toPage(`/log?date=${encodeURIComponent(key)}`);
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && dom.viewMenu && !dom.viewMenu.classList.contains("hidden")) {
    closeViewMenu();
    return;
  }
  if (e.key === "Escape" && dom.modal && !dom.modal.classList.contains("hidden")) {
    closeAddTaskModal();
  }
});

document.addEventListener("click", (e) => {
  if (!dom.viewMenu || !dom.viewMenuBtn) {
    return;
  }
  if (dom.viewMenu.classList.contains("hidden")) {
    return;
  }
  if (dom.viewMenu.contains(e.target) || dom.viewMenuBtn.contains(e.target)) {
    return;
  }
  closeViewMenu();
});

async function init() {
  state.view = String(dom.root?.dataset.view || "tasks").toLowerCase() === "calendar" ? "calendar" : "tasks";
  if (state.view === "calendar") {
    state.selectedDateKey = toDateKey(new Date());
    await loadCalendarWeek(state.selectedDateKey);
    return;
  }
  await loadSubjects();
  await loadTasks();
}

init();
