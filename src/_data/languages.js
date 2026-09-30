import fs from "node:fs";
import { deepMerge } from "../../lib/helpers.js";

// To add a language: copy i18n/en.json to i18n/<code>.json, translate it, then set enabled: true below.
// Any string missing from a translation falls back to English, so a partial translation still builds.
const LANGUAGES = [
  { code: "en", name: "English", locale: "en-GB", enabled: true },
  { code: "hy", name: "Հայերեն", locale: "hy-AM", enabled: true },
  { code: "ru", name: "Русский", locale: "ru-RU", enabled: true },
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
