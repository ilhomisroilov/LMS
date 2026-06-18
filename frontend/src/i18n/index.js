import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import uz from "./locales/uz.json";
import en from "./locales/en.json";

const saved = localStorage.getItem("lang") || "uz";

i18n.use(initReactI18next).init({
  resources: { uz: { translation: uz }, en: { translation: en } },
  lng: saved,
  fallbackLng: "uz",
  interpolation: { escapeValue: false },
});

export default i18n;
