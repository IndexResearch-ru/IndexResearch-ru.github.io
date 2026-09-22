(() => {
  const setExpanded = (button, expanded) => {
    const id = button.getAttribute("data-menu-toggle");
    const panel = id ? document.getElementById(id) : null;
    if (!panel) return;
    button.setAttribute("aria-expanded", expanded ? "true" : "false");
    panel.hidden = !expanded;
  };

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
