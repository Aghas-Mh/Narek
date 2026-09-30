// Root address: go to the visitor's saved language, else their browser language, else the default.
(() => {
  const root = document.documentElement;
  const available = (root.dataset.languages || "").split(",").filter(Boolean);
  let pick = root.dataset.default;

  let saved = null;
  try { saved = localStorage.getItem("lang"); } catch {}

  if (saved && available.includes(saved)) {
    pick = saved;
  } else {
    for (const pref of navigator.languages || [navigator.language || ""]) {
      const code = pref.toLowerCase().split("-")[0];
      if (available.includes(code)) { pick = code; break; }
    }
  }
  location.replace(`/${pick}/${location.search}${location.hash}`);
})();
