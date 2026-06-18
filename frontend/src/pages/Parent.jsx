import { useEffect, useMemo, useState } from "react";
import { BookOpen, CalendarCheck, CreditCard, TrendingUp } from "lucide-react";
import { useTranslation } from "react-i18next";
import api from "../api/axios";
import { useApiQuery } from "../hooks/useApiQuery";

function Metric({ icon: Icon, label, value, tone = "text-slate-700" }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center gap-2 text-sm text-slate-500">
        <Icon size={18} aria-hidden="true" />
        <span>{label}</span>
      </div>
      <div className={`text-2xl font-bold ${tone}`}>{value}</div>
    </div>
  );
}

export default function Parent() {
  const { t } = useTranslation();
  const [childId, setChildId] = useState(null);
  const { data: children = [], loading, error } = useApiQuery(
    "parent:children",
    () => api.get("/me/children").then((response) => response.data)
  );

  useEffect(() => {
    if (!childId && children.length) setChildId(children[0].id);
  }, [childId, children]);

  const enabled = Boolean(childId);
  const { data: attendance = [] } = useApiQuery(
    `parent:${childId}:attendance`,
    () => api.get(`/me/children/${childId}/attendance`).then((response) => response.data),
    { enabled }
  );
  const { data: payments = [] } = useApiQuery(
    `parent:${childId}:payments`,
    () => api.get(`/me/children/${childId}/payments`).then((response) => response.data),
    { enabled }
  );
  const { data: lessons = [] } = useApiQuery(
    `parent:${childId}:lessons`,
    () => api.get(`/me/children/${childId}/lessons`).then((response) => response.data),
    { enabled }
  );

  const metrics = useMemo(() => {
    const present = attendance.filter((item) => item.status === "present").length;
    const attendanceRate = attendance.length
      ? Math.round((present / attendance.length) * 100)
      : 0;
    const debt = payments.reduce(
      (sum, item) => sum + Math.max(0, item.amount - item.amount_paid),
      0
    );
    const completed = lessons.filter((item) => item.completed).length;
    const progress = lessons.length ? Math.round((completed / lessons.length) * 100) : 0;
    return { attendanceRate, debt, completed, progress };
  }, [attendance, lessons, payments]);

  if (loading) return <div className="text-slate-500">{t("common.loading")}</div>;
  if (error) return <div className="text-red-600">{t("parent.load_error")}</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("parent.title")}</h1>
        <p className="mt-1 text-sm text-slate-500">{t("parent.subtitle")}</p>
      </div>

      {children.length > 0 ? (
        <div className="flex flex-wrap gap-2" role="group" aria-label={t("parent.select_child")}>
          {children.map((child) => (
            <button
              key={child.id}
              type="button"
              onClick={() => setChildId(child.id)}
              className={`rounded-lg border px-4 py-2 text-sm font-medium ${
                child.id === childId
                  ? "border-brand bg-brand text-white"
                  : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              {child.full_name}
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white p-5 text-slate-500">
          {t("parent.no_children")}
        </div>
      )}

      {enabled && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metric icon={CalendarCheck} label={t("parent.attendance")} value={`${metrics.attendanceRate}%`} tone="text-green-700" />
            <Metric icon={BookOpen} label={t("parent.completed_lessons")} value={`${metrics.completed}/${lessons.length}`} />
            <Metric icon={TrendingUp} label={t("parent.progress")} value={`${metrics.progress}%`} tone="text-brand-dark" />
            <Metric icon={CreditCard} label={t("parent.debt")} value={new Intl.NumberFormat().format(metrics.debt)} tone={metrics.debt ? "text-red-700" : "text-green-700"} />
          </div>

          <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <h2 className="border-b border-slate-200 px-4 py-3 text-base font-semibold">{t("parent.recent_results")}</h2>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px]">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="th">{t("attendance.date")}</th>
                    <th className="th">{t("attendance.status")}</th>
                    <th className="th">{t("groups.title")}</th>
                  </tr>
                </thead>
                <tbody>
                  {attendance.slice(0, 10).map((item) => (
                    <tr key={item.id}>
                      <td className="td">{item.lesson_date}</td>
                      <td className="td">{t(`attendance.${item.status}`)}</td>
                      <td className="td">#{item.group_id}</td>
                    </tr>
                  ))}
                  {attendance.length === 0 && (
                    <tr><td className="td text-slate-400" colSpan="3">{t("common.no_data")}</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
