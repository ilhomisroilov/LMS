import { useTranslation } from "react-i18next";
import api from "../api/axios";
import StatCard from "../components/StatCard.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useApiQuery } from "../hooks/useApiQuery";
import { canAccess } from "../utils/authz.js";

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canReadPayments = canAccess(user, { permissions: ["payment:read"] });
  // Cached for 30s and shown instantly on revisit (stale-while-revalidate).
  const { data: s } = useApiQuery(
    "dashboard:stats",
    () => api.get("/dashboard/stats").then((r) => r.data),
    { staleTime: 30000 }
  );

  if (!s) return <div className="text-slate-500">{t("common.loading")}</div>;
  const money = (n) => new Intl.NumberFormat().format(n);

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">{t("dashboard.title")}</h1>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t("dashboard.total_students")} value={s.total_students} />
        <StatCard label={t("dashboard.active_students")} value={s.active_students} accent="text-green-600" />
        <StatCard label={t("dashboard.teachers")} value={s.total_teachers} />
        <StatCard label={t("dashboard.active_groups")} value={s.active_groups} />
        <StatCard label={t("dashboard.courses")} value={s.total_courses} />
        {canReadPayments && (
          <StatCard label={t("dashboard.revenue")} value={money(s.revenue_this_month)} accent="text-green-600" />
        )}
        {canReadPayments && (
          <StatCard label={t("dashboard.debt")} value={money(s.debt_total)} accent="text-red-600" />
        )}
        <StatCard label={t("dashboard.attendance_rate")} value={`${s.attendance_rate}%`} />
      </div>
    </div>
  );
}
