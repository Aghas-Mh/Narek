import { interp, pageVars } from "../lib/helpers.js";

// Texts for tools/make-og-image.ps1, per language, with {goal} etc. already formatted
// exactly as the page shows them (same currency, same number format).
export default {
  permalink: "/og-data.json",
  eleventyExcludeFromCollections: true,
  eleventyComputed: {
    ogData: (data) => {
      const out = {};
      // Eleventy first calls this with placeholder data to find dependencies, so guard every step
      for (const lang of Array.isArray(data.languages) ? data.languages : []) {
        if (!lang?.code || !lang?.t?.og || !data.campaign?.child) continue;
        const vars = pageVars(data, lang);
        out[lang.code] = Object.fromEntries(Object.entries(lang.t.og).map(([key, text]) => [key, interp(text, vars)]));
      }
      return out;
    },
  },
};
