// Small progressive enhancements. The page works without JavaScript.
(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const live = $("[data-live]");
  const announce = (msg) => { if (live) { live.textContent = ""; setTimeout(() => (live.textContent = msg), 50); } };

  // The canonical link resolves to an absolute URL even while site.url is not set yet.
  const pageUrl = () => $('link[rel="canonical"]')?.href || location.origin + location.pathname;

  // ---- Copy buttons (card numbers, page link) ----
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;top:0;left:0;opacity:0";
      document.body.append(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand("copy"); } catch {}
      ta.remove();
      return ok;
    }
  }

  document.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-copy]");
    if (!btn) return;
    const text = "copyPage" in btn.dataset ? pageUrl() : btn.dataset.copy;
    const ok = await copyText(text);
    const label = $("[data-label]", btn) || btn;
    label.dataset.original ??= label.textContent;
    label.textContent = ok ? btn.dataset.done : btn.dataset.fail;
    btn.classList.toggle("is-done", ok);
    announce(label.textContent);
    clearTimeout(btn._reset);
    btn._reset = setTimeout(() => {
      label.textContent = label.dataset.original;
      btn.classList.remove("is-done");
    }, 2200);
  });

  // ---- Share links: rebuilt from the live page URL (same list as lib/helpers.js) ----
  const share = $("[data-share]");
  if (share) {
    const url = pageUrl();
    const text = share.dataset.shareText;
    const u = encodeURIComponent(url);
    const t = encodeURIComponent(text);
    const tu = encodeURIComponent(`${text} ${url}`);
    const links = {
      whatsapp: `https://wa.me/?text=${tu}`,
      telegram: `https://t.me/share/url?url=${u}&text=${t}`,
      viber: `viber://forward?text=${tu}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${u}`,
      vk: `https://vk.com/share.php?url=${u}`,
      x: `https://twitter.com/intent/tweet?text=${t}&url=${u}`,
      email: `mailto:?body=${tu}`,
    };
    $$("[data-network]", share).forEach((a) => (a.href = links[a.dataset.network]));

    const native = $("[data-native-share]", share);
    if (native && navigator.share) {
      native.hidden = false;
      native.addEventListener("click", () => {
        navigator.share({ title: share.dataset.shareTitle, text, url }).catch(() => {});
      });
    }
  }

  // ---- Document viewer ----
  const dialog = $("#lightbox");
  if (dialog && typeof dialog.showModal === "function") {
    const img = $(".lightbox__img", dialog);
    const caption = $(".lightbox__caption", dialog);
    const open = $(".lightbox__open", dialog);

    document.addEventListener("click", (e) => {
      const link = e.target.closest("[data-lightbox]");
      if (!link || e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      img.src = link.getAttribute("href");
      img.alt = link.dataset.caption || "";
      caption.textContent = link.dataset.caption || "";
      open.href = link.getAttribute("href");
      dialog.showModal();
      dialog.scrollTop = 0;
    });
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
    $("[data-close]", dialog).addEventListener("click", () => dialog.close());
  }

  // ---- Sticky "Donate" bar on phones: shown once the hero is scrolled away, hidden at the donate section ----
  const bar = $("[data-sticky-donate]");
  const hero = $(".hero");
  const donate = $("#donate");
  if (bar && hero && donate && "IntersectionObserver" in window) {
    const seen = new Map();
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => seen.set(en.target, en.isIntersecting));
      bar.classList.toggle("is-visible", !seen.get(hero) && !seen.get(donate));
    });
    io.observe(hero);
    io.observe(donate);
  }

  // ---- Remember the chosen language for the root address ----
  $$("[data-lang]").forEach((a) =>
    a.addEventListener("click", () => {
      try { localStorage.setItem("lang", a.dataset.lang); } catch {}
    }),
  );
})();
