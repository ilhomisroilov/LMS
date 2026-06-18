import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";
import LanguageSwitcher from "../components/LanguageSwitcher.jsx";
import { defaultPathForUser } from "../utils/authz.js";

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [phone, setPhone] = useState("+998901112233");
  const [password, setPassword] = useState("Admin12345");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const user = await login(phone, password);
      navigate(defaultPathForUser(user));
    } catch {
      setError(t("auth.error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-sm card">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-brand">{t("app.name")}</div>
            <div className="text-xs text-slate-400">{t("auth.title")}</div>
          </div>
          <LanguageSwitcher />
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">{t("auth.phone")}</label>
            <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">{t("auth.password")}</label>
            <input type="password" className="input" value={password}
                   onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? "..." : t("auth.signin")}
          </button>
        </form>
      </div>
    </div>
  );
}
