(() => {
  const setExpanded = (button, expanded) => {
    const id = button.getAttribute("data-menu-toggle");
    const panel = id ? document.getElementById(id) : null;
    if (!panel) return;
    button.setAttribute("aria-expanded", expanded ? "true" : "false");
    panel.hidden = !expanded;
  };


  let shareNoticeTimer;
  const showShareNotice = (message) => {
    let notice = document.querySelector(".ir-share-notice");
    if (!notice) {
      notice = document.createElement("div");
      notice.className = "ir-share-notice";
      notice.setAttribute("role", "status");
      notice.setAttribute("aria-live", "polite");
      document.body.appendChild(notice);
    }
    notice.textContent = message;
    clearTimeout(shareNoticeTimer);
    shareNoticeTimer = setTimeout(() => notice.remove(), 2600);
  };

  const sharePage = async (button) => {
    const canonical = document.querySelector('link[rel~="canonical"]');
    const url = canonical ? canonical.href : window.location.href;
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: document.title, url });
        return;
      } catch (error) {
        if (error && error.name === "AbortError") return;
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      showShareNotice(button.dataset.shareCopied);
    } catch (error) {
      window.prompt(button.dataset.shareCopyPrompt, url);
    }
  };

  // A direct click handler cannot be blocked by another element's bubbling listener.
  document.querySelectorAll("[data-share-page]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      sharePage(button);
    });
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-menu-toggle]");
    if (!button) return;
    const expanded = button.getAttribute("aria-expanded") === "true";
    setExpanded(button, !expanded);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    document.querySelectorAll('[data-menu-toggle][aria-expanded="true"]').forEach((button) => {
      setExpanded(button, false);
    });
  });
})();
