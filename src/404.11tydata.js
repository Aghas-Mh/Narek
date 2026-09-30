import { defaultLanguage, pageVars } from "../lib/helpers.js";

export default {
  eleventyComputed: {
    lang: (data) => defaultLanguage(data),
    t: (data) => defaultLanguage(data).t,
    vars: (data) => pageVars(data, defaultLanguage(data)),
    title: (data) => defaultLanguage(data).t.notFound.title,
  },
};
