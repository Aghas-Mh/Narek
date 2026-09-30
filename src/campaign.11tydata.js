import { pageVars } from "../lib/helpers.js";

export default {
  eleventyComputed: {
    t: (data) => data.lang.t,
    vars: (data) => pageVars(data, data.lang),
  },
};
