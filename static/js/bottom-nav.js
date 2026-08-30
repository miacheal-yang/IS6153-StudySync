(function initBottomNav() {
  const ENV = window.StudySyncEnv || {};

  document.querySelectorAll(".bottom-nav-item").forEach((node) => {
    const path = node.getAttribute("data-path");
    if (!path) {
      return;
    }
    let target = path;
    if (ENV.IS_PREVIEW && typeof ENV.templateUrl === "function") {
      target = ENV.templateUrl(path);
    }
    node.setAttribute("href", target);
    node.addEventListener("click", (event) => {
      event.preventDefault();
      if (typeof ENV.toPage === "function") {
        ENV.toPage(path);
        return;
      }
      window.location.assign(target);
    });
  });
})();
