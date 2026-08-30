(function initStudySyncEnv() {
  const rawBase = String(localStorage.getItem("studytrackr_api_base") || "").trim().replace(/\/$/, "");
  const isPreview = window.location.port === "63342";
  const baseFromStorage = rawBase ? rawBase.replace(/\/api(?:\/.*)?$/i, "") : "";

  function isLocalHostBase(base) {
    return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(base);
  }

  function isPreviewPortBase(base) {
    if (!base) {
      return false;
    }
    try {
      const parsed = new URL(base);
      return parsed.port === "63342";
    } catch (_) {
      return false;
    }
  }

  // In preview mode, prioritize local backend to avoid stale remote base values from localStorage.
  // Outside preview mode, never use 63342 as the app base.
  const safeStoredBase = !isPreview && isPreviewPortBase(baseFromStorage) ? "" : baseFromStorage;
  const apiBase = isPreview
    ? (isLocalHostBase(baseFromStorage) ? baseFromStorage : "http://localhost:5000")
    : (safeStoredBase || "");
  const pageBase = isPreview ? "" : safeStoredBase;
  const pageMap = {
    "/": "landing.html",
    "/login": "login.html",
    "/register": "register.html",
    "/dashboard": "dashboard.html",
    "/log": "log.html",
    "/tasks": "tasks.html",
    "/profile": "profile.html",
    "/notifications": "notifications.html",
    "/analytics": "analytics.html",
  };
  const reversePageMap = Object.fromEntries(Object.entries(pageMap).map(([route, file]) => [file, route]));

  function routeFromCurrentPreviewPath() {
    const path = window.location.pathname || "/";
    const match = path.match(/\/templates\/([^/]+\.html)$/i);
    if (!match) {
      return "/";
    }
    const fileName = match[1];
    return reversePageMap[fileName] || "/";
  }

  // If opened via static preview (63342), send users to Flask backend for full rendering/features.
  if (isPreview) {
    const targetRoute = routeFromCurrentPreviewPath();
    const targetUrl = `http://127.0.0.1:5000${targetRoute}${window.location.search || ""}`;
    window.location.replace(targetUrl);
    return;
  }

  function rootPathFromTemplates() {
    return window.location.pathname.replace(/\/templates\/[^/]*$/i, "");
  }

  function templateUrl(path, querySuffix = "") {
    const fileName = pageMap[path] || pageMap["/"];
    const rootPath = rootPathFromTemplates();
    return `${window.location.origin}${rootPath}/templates/${fileName}${querySuffix}`;
  }

  function toPage(path) {
    if (isPreview) {
      const query = path === "/register" ? "?mode=register" : "";
      window.location.href = templateUrl(path, query);
      return;
    }
    if (!pageBase) {
      window.location.href = path;
      return;
    }
    window.location.href = `${pageBase}${path}`;
  }

  function apiUrl(path) {
    return apiBase ? `${apiBase}${path}` : path;
  }

  window.StudySyncEnv = {
    IS_PREVIEW: isPreview,
    API_BASE: apiBase,
    PAGE_BASE: pageBase,
    PAGE_MAP: pageMap,
    apiUrl,
    toPage,
    templateUrl,
  };
})();
