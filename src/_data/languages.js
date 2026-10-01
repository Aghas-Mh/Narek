import fs from "node:fs";
import { deepMerge } from "../../lib/helpers.js";

// To add a language: copy i18n/en.json to i18n/<code>.json, translate it, then set enabled: true below.
// Any string missing from a translation falls back to English, so a partial translation still builds.
// `currency`: how the goal and the amount raised are shown on that page. Amounts are stored in the
// goal currency (campaign.json) and converted with the goal's own "approx" figure for that currency.
const LANGUAGES = [
  { code: "en", name: "English", locale: "en-GB", currency: "USD", enabled: true },
  { code: "hy", name: "Հայերեն", locale: "hy-AM", currency: "USD", enabled: true },
  { code: "ru", name: "Русский", locale: "ru-RU", currency: "RUB", enabled: true },
];

const read = (code) => {
  const file = new URL(`./i18n/${code}.json`, import.meta.url);
  if (!fs.existsSync(file)) throw new Error(`Language "${code}" is enabled but src/_data/i18n/${code}.json does not exist.`);
  return JSON.parse(fs.readFileSync(file, "utf8"));
};

export default function () {
  const en = read("en");
  return LANGUAGES.filter((l) => l.enabled).map(({ enabled, ...l }) => ({
    ...l,
    t: l.code === "en" ? en : deepMerge(en, read(l.code)),
  }));
}
