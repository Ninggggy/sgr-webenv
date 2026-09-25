"use strict";
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("mathjax_toggle");
  if (!toggle) return;
  toggle.addEventListener("click", event => {
    event.preventDefault();
    const disabled = document.cookie.split(";").some(x => x.trim() === "arxiv_mathjax=disabled");
    document.cookie = "arxiv_mathjax=" + (disabled ? "enabled" : "disabled") + "; Path=/; Max-Age=31536000; SameSite=Lax";
    location.reload();
  });
});
