import { useState } from "react";
import { Menu, X } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";
import LanguageSwitcher from "../components/LanguageSwitcher.jsx";
import { canAccess } from "../utils/authz.js";

const LINKS = [
  { key: "dashboard", path: "/", permissions: ["analytics:read"] },
  { key: "students", path: "/students", permissions: ["student:read"] },
  { key: "teachers", path: "/teachers", permissions: ["teacher:read"] },
  { key: "groups", path: "/groups", permissions: ["group:read"] },
  { key: "attendance", path: "/attendance", permissions: ["attendance:read"] },
  { key: "payments", path: "/payments", permissions: ["payment:read"] },
  { key: "lms", path: "/lms", roles: ["admin", "manager", "teacher", "student"] },
  { key: "parent", path: "/parent", roles: ["parent"] },
  { key: "settings", path: "/settings" },
];

export default function DashboardLayout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const links = LINKS.filter((link) => canAccess(user, link));

  const handleLogout = async () => {
    setMenuOpen(false);
    await logout();
  };

  return (
    <div className="min-h-screen bg-slate-50 md:flex">
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 md:hidden">
        <button
          type="button"
          className="rounded p-2 text-slate-600 hover:bg-slate-100"
          aria-label="Menyuni ochish"
          title="Menyuni ochish"
          onClick={() => setMenuOpen(true)}
        >
          <Menu size={21} />
        </button>
        <div className="font-bold text-brand">{t("app.name")}</div>
        <LanguageSwitcher />
      </header>

      {menuOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-slate-950/40 md:hidden"
          aria-label="Menyuni yopish"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-slate-200 bg-white transition-transform md:static md:z-auto md:translate-x-0 ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-start justify-between px-5 py-5">
          <div>
            <div className="text-xl font-bold text-brand">{t("app.name")}</div>
            <div className="text-xs text-slate-400">{t("app.tagline")}</div>
          </div>
          <button
            type="button"
            className="rounded p-1 text-slate-500 hover:bg-slate-100 md:hidden"
            aria-label="Menyuni yopish"
            title="Menyuni yopish"
            onClick={() => setMenuOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        <div className="px-5 pb-3 text-xs text-slate-500">
          {user?.full_name} / {user?.role}
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3">
          {links.map((link) => (
            <NavLink
              key={link.key}
              to={link.path}
              end={link.path === "/"}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-brand-light text-brand-dark" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {t(`nav.${link.key}`)}
            </NavLink>
          ))}
        </nav>
        <button onClick={handleLogout} className="m-3 btn-ghost text-red-600">
          {t("nav.logout")}
        </button>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="hidden items-center justify-between border-b border-slate-200 bg-white px-6 py-3 md:flex">
          <div className="text-sm text-slate-500">{user?.full_name} / {user?.role}</div>
          <LanguageSwitcher />
        </header>
        <main className="min-w-0 flex-1 overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
