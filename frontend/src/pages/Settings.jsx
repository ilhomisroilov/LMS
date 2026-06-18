import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";

export default function Settings() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const change = (lng) => { i18n.changeLanguage(lng); localStorage.setItem("lang", lng); };

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">{t("settings.title")}</h1>
      <div className="card max-w-md space-y-4">
        <div>
          <div className="mb-2 text-sm font-medium">{t("settings.language")}</div>
          <div className="flex gap-2">
            {[["uz", t("settings.uz")], ["en", t("settings.en")]].map(([lng, label]) => (
              <button key={lng} onClick={() => change(lng)}
                      className={i18n.language === lng ? "btn-primary" : "btn-ghost"}>{label}</button>
            ))}
          </div>
        </div>
        <div className="border-t border-slate-100 pt-4 text-sm text-slate-500">
          <div>{user?.full_name}</div>
          <div>{user?.phone} · {user?.role}</div>
        </div>
      </div>
    </div>
  );
}
