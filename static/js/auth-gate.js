(function initAuthGate() {
  const ENV = window.StudySyncEnv || {};

  function toPage(path) {
    if (typeof ENV.toPage === "function") {
      ENV.toPage(path);
      return;
    }
    window.location.href = path;
  }

  async function verifyAuth() {
    try {
      const url = typeof ENV.apiUrl === "function" ? ENV.apiUrl("/api/auth/me") : "/api/auth/me";
      const response = await fetch(url, { credentials: "include" });
      if (response.ok) {
        return;
      }
      // Unauthenticated users should always go to the first-entry home page.
      toPage("/");
    } catch (error) {
      toPage("/");
    }
  }

  verifyAuth();
})();
