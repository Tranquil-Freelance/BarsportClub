"use client";

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import it from "./locales/it.json";
import es from "./locales/es.json";
import fr from "./locales/fr.json";
import de from "./locales/de.json";

/** localStorage key used to persist the user's language choice. */
export const STORAGE_KEY = "barsport_lang";

if (!i18n.isInitialized) {
  i18n
    .use(initReactI18next)
    .init({
      resources: {
        en: { translation: en },
        it: { translation: it },
        es: { translation: es },
        fr: { translation: fr },
        de: { translation: de },
      },
      fallbackLng: "en",
      supportedLngs: ["en", "it", "es", "fr", "de"],
      // Use a deterministic fallback language ("en") at init so that
      // SSR and the first client render (hydration) always agree.
      // Browser-language detection runs after hydration in I18nProvider.
      lng: "en",
      interpolation: {
        escapeValue: false,
      },
    });
}

/**
 * Detect the user's preferred language from browser APIs.
 * Called after hydration in I18nProvider.
 */
export function detectBrowserLanguage(): string {
  if (typeof window === "undefined") return "en";

  // 1. Check localStorage cache (set by language switcher)
  try {
    const cached = localStorage.getItem(STORAGE_KEY);
    if (cached && ["en", "it", "es", "fr", "de"].includes(cached)) return cached;
  } catch { /* localStorage unavailable */ }

  // 2. Fall back to navigator language
  try {
    const navLang = (navigator.language || "").slice(0, 2);
    if (["en", "it", "es", "fr", "de"].includes(navLang)) return navLang;
  } catch { /* navigator unavailable */ }

  return "en";
}

export default i18n;
