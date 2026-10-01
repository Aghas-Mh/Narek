// Shared helpers used by the Eleventy config (as filters) and by the page data files.

// Any value that is missing, empty or starts with "TODO" is treated as "still to be filled in".
const TODO_RE = /^\s*TODO\b[:\s]*/i;

export const isTodo = (v) =>
  v === undefined || v === null || v === "" || (typeof v === "string" && TODO_RE.test(v));

export const todoLabel = (v) => (typeof v === "string" ? v.replace(TODO_RE, "") : "");

export const escapeHtml = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Replaces {name} placeholders in translation strings: interp("Narek is {age}", { age: 9 }).
export const interp = (str, vars = {}) =>
  String(str ?? "").replace(/\{(\w+)\}/g, (m, key) => (key in vars ? vars[key] : m));

export function money(amount, currency, locale) {
  if (typeof amount !== "number") return String(amount);
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    currencyDisplay: "narrowSymbol",
    maximumFractionDigits: 0,
  }).format(amount);
}

// "$3.3M", "270 млн ₽", "3,3 մլն $"
export function moneyCompact(amount, currency, locale) {
  if (typeof amount !== "number") return String(amount);
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    currencyDisplay: "narrowSymbol",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount);
}

// Converts an amount stored in the goal currency, using the goal's "approx" figure for `currency`.
// Returns null when there is no conversion for that currency.
export function inCurrency(amount, currency, goal) {
  if (typeof amount !== "number") return null;
  if (currency === goal.currency) return amount;
  const alt = (goal.approx || []).find((a) => a.currency === currency && typeof a.amount === "number");
  return alt ? (amount * alt.amount) / goal.amount : null;
}

// A converted amount is an estimate, so don't pretend to cent precision: 11,166 -> 11,200
const roundEstimate = (n) => (n >= 1000 ? Math.round(n / 100) * 100 : Math.round(n / 10) * 10);

export function formatDate(iso, locale) {
  if (isTodo(iso)) return iso;
  const date = new Date(String(iso).length === 10 ? `${iso}T00:00:00Z` : iso);
  return new Intl.DateTimeFormat(locale, { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(date);
}

export function ageOn(birthIso, now = new Date()) {
  const birth = new Date(`${birthIso}T00:00:00Z`);
  let age = now.getUTCFullYear() - birth.getUTCFullYear();
  const m = now.getUTCMonth() - birth.getUTCMonth();
  if (m < 0 || (m === 0 && now.getUTCDate() < birth.getUTCDate())) age--;
  return age;
}

// "9051345203695885" -> "9051 3452 0369 5885"
export const groupDigits = (n) => String(n).replace(/\s+/g, "").replace(/(\d{4})(?=\d)/g, "$1 ");

export function percent(raised, goal) {
  if (typeof raised !== "number" || typeof goal !== "number" || goal <= 0) return 0;
  const p = Math.min(100, (raised / goal) * 100);
  return p < 10 ? Math.round(p * 10) / 10 : Math.round(p);
}

export const percentLabel = (p, locale) =>
  new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: p < 10 ? 1 : 0 }).format(p / 100);

export function contactHref(kind, value) {
  const v = String(value).trim();
  switch (kind) {
    case "phone":
      return `tel:${v.replace(/[^\d+]/g, "")}`;
    case "whatsapp":
      return `https://wa.me/${v.replace(/\D/g, "")}`;
    case "telegram":
      return `https://t.me/${v.replace(/^@/, "")}`;
    case "email":
      return `mailto:${v}`;
    case "instagram":
      return `https://www.instagram.com/${v.replace(/^@/, "")}/`;
    default:
      return v; // already a full URL (e.g. a Facebook page)
  }
}

// Kept in sync with the same list in src/assets/js/main.js, which rebuilds the links from the live page URL.
export function shareLinks(url, text) {
  const u = encodeURIComponent(url);
  const t = encodeURIComponent(text);
  const tu = encodeURIComponent(`${text} ${url}`);
  return {
    whatsapp: `https://wa.me/?text=${tu}`,
    telegram: `https://t.me/share/url?url=${u}&text=${t}`,
    viber: `viber://forward?text=${tu}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${u}`,
    vk: `https://vk.com/share.php?url=${u}`,
    x: `https://twitter.com/intent/tweet?text=${t}&url=${u}`,
    email: `mailto:?body=${tu}`,
  };
}

// Objects merge key by key; arrays and plain values from `over` replace those in `base`.
export function deepMerge(base, over) {
  if (over === undefined) return base;
  if (Array.isArray(base) || Array.isArray(over)) return over;
  if (base && over && typeof base === "object" && typeof over === "object") {
    const out = { ...base };
    for (const [key, value] of Object.entries(over)) out[key] = deepMerge(base[key], value);
    return out;
  }
  return over;
}

// Lists every "TODO…" string inside a JSON value, with its path (e.g. "payments[0].bank").
export function findTodos(value, trail = "", out = []) {
  if (typeof value === "string") {
    if (TODO_RE.test(value)) out.push({ path: trail, note: todoLabel(value) });
  } else if (Array.isArray(value)) {
    value.forEach((v, i) => findTodos(v, `${trail}[${i}]`, out));
  } else if (value && typeof value === "object") {
    for (const [key, v] of Object.entries(value)) findTodos(v, trail ? `${trail}.${key}` : key, out);
  }
  return out;
}

// Values shared by every page of one language, available in templates as `vars`.
export function pageVars(data, lang) {
  const { campaign } = data;
  const { goal, raised } = campaign;
  const age = ageOn(campaign.child.birthDate);

  // The page's display currency, falling back to the goal currency when there is no conversion for it
  const wanted = lang.currency || goal.currency;
  const currency = inCurrency(goal.amount, wanted, goal) === null ? goal.currency : wanted;
  const converted = currency !== goal.currency;
  const goalIn = inCurrency(goal.amount, currency, goal);
  const raisedIn = inCurrency(raised.amount, currency, goal);

  return {
    age,
    birthDate: formatDate(campaign.child.birthDate, lang.locale),
    currency,
    converted,
    goal: moneyCompact(goalIn, currency, lang.locale),
    goalFull: money(goalIn, currency, lang.locale),
    raised: raisedIn === null ? null : money(converted ? roundEstimate(raisedIn) : raisedIn, currency, lang.locale),
    raisedOriginal: typeof raised.amount === "number" ? money(raised.amount, goal.currency, lang.locale) : null,
    // Position on the "How Duchenne usually progresses" timeline
    stage: age < 5 ? 0 : age < 10 ? 1 : age < 14 ? 2 : 3,
    buildDate: formatDate(new Date().toISOString().slice(0, 10), lang.locale),
  };
}

export const defaultLanguage = (data) =>
  data.languages.find((l) => l.code === data.site.defaultLanguage) ?? data.languages[0];
