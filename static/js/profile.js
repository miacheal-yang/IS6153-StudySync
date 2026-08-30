const ENV = window.StudySyncEnv || {};

const state = {
  user: null,
  draftAvatarUrl: "",
};

const dom = {
  avatarView: document.getElementById("avatarView"),
  profileName: document.getElementById("profileName"),
  profileMajor: document.getElementById("profileMajor"),
  profileSemester: document.getElementById("profileSemester"),
  profileView: document.getElementById("profileView"),
  profileEditForm: document.getElementById("profileEditForm"),
  fullNameInput: document.getElementById("fullNameInput"),
  majorInput: document.getElementById("majorInput"),
  semesterInput: document.getElementById("semesterInput"),
  avatarFileInput: document.getElementById("avatarFileInput"),
  profileMessage: document.getElementById("profileMessage"),
  editProfileBtn: document.getElementById("editProfileBtn"),
  cancelProfileBtn: document.getElementById("cancelProfileBtn"),
  defaultReminderSelect: document.getElementById("defaultReminderSelect"),
  saveReminderBtn: document.getElementById("saveReminderBtn"),
  logoutBtn: document.getElementById("logoutBtn"),
  logoutBtnTop: document.getElementById("logoutBtnTop"),
  notificationSettingBtn: document.getElementById("notificationSettingBtn"),
  notificationSettingPanel: document.getElementById("notificationSettingPanel"),
  helpBtn: document.getElementById("helpBtn"),
  helpPanel: document.getElementById("helpPanel"),
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

function setMessage(text, isError = false) {
  dom.profileMessage.textContent = text || "";
  dom.profileMessage.style.color = isError ? "var(--danger)" : "var(--subtle)";
}

function renderAvatar(user) {
  const avatarUrl = String(user.avatar_url || "").trim();
  const initial = (user.full_name || "U").trim().charAt(0).toUpperCase() || "U";
  if (avatarUrl) {
    dom.avatarView.innerHTML = `<img src="${avatarUrl}" alt="Avatar" class="avatar-image" />`;
  } else {
    dom.avatarView.textContent = initial;
  }
}

function renderProfile() {
  const user = state.user;
  if (!user) {
    return;
  }
  dom.profileName.textContent = user.full_name || "Unnamed";
  dom.profileMajor.textContent = `Major: ${user.major || "-"}`;
  dom.profileSemester.textContent = `Current Semester: ${user.semester || "-"}`;
  dom.defaultReminderSelect.value = String(user.default_reminder ?? "0");
  renderAvatar(user);
}

function startEditing() {
  if (!state.user) {
    return;
  }
  dom.fullNameInput.value = state.user.full_name || "";
  dom.majorInput.value = state.user.major || "";
  dom.semesterInput.value = state.user.semester || "";
  dom.avatarFileInput.value = "";
  state.draftAvatarUrl = state.user.avatar_url || "";
  dom.profileView.classList.add("hidden");
  dom.profileEditForm.classList.remove("hidden");
  setMessage("");
}

function cancelEditing() {
  dom.profileEditForm.classList.add("hidden");
  dom.profileView.classList.remove("hidden");
  state.draftAvatarUrl = "";
  setMessage("");
}

function togglePanel(panel) {
  panel.classList.toggle("hidden");
}

async function saveProfile(event) {
  event.preventDefault();
  const payload = {
    full_name: dom.fullNameInput.value.trim(),
    major: dom.majorInput.value.trim(),
    semester: dom.semesterInput.value.trim(),
    avatar_url: state.draftAvatarUrl,
  };
  const result = await fetchJson("/api/auth/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (result.error || !result.response.ok) {
    setMessage(result.data.error || "Failed to save profile.", true);
    return;
  }
  state.user = result.data.user;
  renderProfile();
  cancelEditing();
  setMessage("Profile updated.");
}

async function saveReminderDefault() {
  const result = await fetchJson("/api/auth/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ default_reminder: dom.defaultReminderSelect.value }),
  });
  if (result.error || !result.response.ok) {
    setMessage(result.data.error || "Failed to save notification settings.", true);
    return;
  }
  state.user = result.data.user;
  renderProfile();
  setMessage("Default reminder saved.");
}

async function logout() {
  const ok = window.confirm("Are you sure you want to log out?");
  if (!ok) {
    return;
  }
  await fetch(apiUrl("/api/auth/logout"), { method: "POST", credentials: "include" });
  toPage("/");
}

function handleAvatarChange(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    state.draftAvatarUrl = typeof reader.result === "string" ? reader.result : "";
    if (state.draftAvatarUrl) {
      dom.avatarView.innerHTML = `<img src="${state.draftAvatarUrl}" alt="Avatar preview" class="avatar-image" />`;
    }
  };
  reader.readAsDataURL(file);
}

async function init() {
  const result = await fetchJson("/api/auth/me");
  if (result.error || !result.response.ok) {
    return;
  }
  state.user = result.data.user;
  renderProfile();
}

dom.editProfileBtn?.addEventListener("click", startEditing);
dom.cancelProfileBtn?.addEventListener("click", cancelEditing);
dom.profileEditForm?.addEventListener("submit", saveProfile);
dom.avatarFileInput?.addEventListener("change", handleAvatarChange);
dom.saveReminderBtn?.addEventListener("click", saveReminderDefault);
dom.notificationSettingBtn?.addEventListener("click", () => togglePanel(dom.notificationSettingPanel));
dom.helpBtn?.addEventListener("click", () => togglePanel(dom.helpPanel));
dom.logoutBtn?.addEventListener("click", logout);
dom.logoutBtnTop?.addEventListener("click", logout);

init();
