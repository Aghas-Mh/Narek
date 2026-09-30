import fs from "node:fs";
import path from "node:path";
import * as h from "./lib/helpers.js";

const DATA_DIR = "src/_data";

export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy({ "src/assets": "assets", "src/_headers": "_headers" });

  eleventyConfig.addFilter("isTodo", h.isTodo);
  eleventyConfig.addFilter("interp", h.interp);
  eleventyConfig.addFilter("money", h.money);
  eleventyConfig.addFilter("formatDate", h.formatDate);
  eleventyConfig.addFilter("groupDigits", h.groupDigits);
  eleventyConfig.addFilter("percent", h.percent);
  eleventyConfig.addFilter("percentLabel", h.percentLabel);
  eleventyConfig.addFilter("contactHref", (value, kind) => h.contactHref(kind, value));
  eleventyConfig.addFilter("shareLinks", h.shareLinks);
  // Absolute URL once site.url is set; relative until then.
  eleventyConfig.addFilter("absUrl", (p, siteUrl) => (h.isTodo(siteUrl) ? p : new URL(p, siteUrl).href));
  // Per-language social preview image, falling back to the English one.
  eleventyConfig.addFilter("ogImage", (code) =>
    fs.existsSync(`src/assets/img/og/og-${code}.jpg`) ? `/assets/img/og/og-${code}.jpg` : "/assets/img/og/og-en.jpg",
  );

  // {% fill value %} prints the value, or a highlighted placeholder while it is still "TODO: …".
  eleventyConfig.addShortcode("fill", (value) =>
    h.isTodo(value)
      ? `<span class="todo">${h.escapeHtml(h.todoLabel(value) || "to be added")}</span>`
      : h.escapeHtml(value),
  );

  // After every build, list the details that still have to be filled in.
  eleventyConfig.on("eleventy.after", () => {
    const files = [
      ...fs.readdirSync(DATA_DIR).filter((f) => f.endsWith(".json")),
      ...fs.readdirSync(path.join(DATA_DIR, "i18n")).map((f) => `i18n/${f}`),
    ];
    const lines = [];
    for (const file of files) {
      const json = JSON.parse(fs.readFileSync(path.join(DATA_DIR, file), "utf8"));
      for (const { path: p, note } of h.findTodos(json)) lines.push(`  ${file.padEnd(16)} ${p}\n  ${"".padEnd(16)} → ${note}`);
    }
    if (lines.length) {
      console.log(`\n⚠  ${lines.length} details still to fill in (search for "TODO" in ${DATA_DIR}):\n${lines.join("\n")}\n`);
    } else {
      console.log("\n✓ No TODOs left — ready to publish.\n");
    }
  });

  return {
    dir: { input: "src", output: "_site" },
    templateFormats: ["njk"],
    htmlTemplateEngine: "njk",
  };
}
