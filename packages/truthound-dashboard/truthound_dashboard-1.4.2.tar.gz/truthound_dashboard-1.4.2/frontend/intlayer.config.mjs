import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

/** @type {import('intlayer').IntlayerConfig} */
const config = {
  internationalization: {
    // Currently translated languages
    locales: [
      "en",  // English
      "ko",  // Korean
    ],
    defaultLocale: "en",
  },
  content: {
    baseDir: __dirname,
    contentDir: [resolve(__dirname, "./src")],
    fileExtensions: [".content.ts", ".content.tsx"],
  },
};

export default config;
