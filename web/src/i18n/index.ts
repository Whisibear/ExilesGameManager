import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import zhHans from "./locales/zh-Hans.json";
import ja from "./locales/ja.json";
import de from "./locales/de.json";
import fr from "./locales/fr.json";
import es from "./locales/es.json";
import { DEFAULT_LANGUAGE } from "./languages";

export const LANGUAGE_STORAGE_KEY = "exilesgamemanager:language";

const resources = {
  en: { translation: en },
  "zh-Hans": { translation: zhHans },
  ja: { translation: ja },
  de: { translation: de },
  fr: { translation: fr },
  es: { translation: es },
};

// Remembers the last language shown in this browser so a page reload
// doesn't flash English before the logged-in user's saved preference loads.
const storedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
const initialLanguage = storedLanguage && Object.hasOwn(resources, storedLanguage) ? storedLanguage : DEFAULT_LANGUAGE;

i18n.use(initReactI18next).init({
  resources,
  lng: initialLanguage,
  fallbackLng: DEFAULT_LANGUAGE,
  interpolation: { escapeValue: false },
});

export function setLanguage(code: string): void {
  const language = Object.hasOwn(resources, code) ? code : DEFAULT_LANGUAGE;
  void i18n.changeLanguage(language);
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  document.documentElement.lang = language;
}

document.documentElement.lang = initialLanguage;

export default i18n;
