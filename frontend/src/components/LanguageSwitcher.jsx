import { useTranslation } from "react-i18next";

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const change = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem("lang", lng);
  };
  return (
    <div className="flex gap-1 rounded-lg border border-slate-300 bg-white p-0.5 text-xs">
      {["uz", "en"].map((lng) => (
        <button
          key={lng}
          onClick={() => change(lng)}
          className={`rounded-md px-2 py-1 font-medium uppercase ${
            i18n.language === lng ? "bg-brand text-white" : "text-slate-600"
          }`}
        >
          {lng}
        </button>
      ))}
    </div>
  );
}
