"use client";

import { useEffect } from "react";
import i18n, { detectBrowserLanguage } from "./config";

export default function I18nProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Detect browser language AFTER hydration, so the SSR render and first
    // client render agree on the fallback ("en"), avoiding hydration mismatches.
    const detected = detectBrowserLanguage();
    if (detected !== i18n.language) {
      i18n.changeLanguage(detected);
    }
  }, []);
  return <>{children}</>;
}
