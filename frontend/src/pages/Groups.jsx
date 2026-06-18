import { useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/axios";
import Modal from "../components/Modal.jsx";
import Pager from "../components/Pager.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useApiQuery, invalidate } from "../hooks/useApiQuery";
import { canAccess } from "../utils/authz.js";

const EMPTY = { name: "", course_id: "", teacher_id: "", schedule_days: "", schedule_time: "" };
const SIZE = 25;

export default function Groups() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canWrite = canAccess(user, { permissions: ["group:write"] });
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);

  const { data, refetch } = useApiQuery(
    `groups:${page}`,
    () => api.get("/groups", { params: { page, size: SIZE } }).then((r) => r.data),
    { staleTime: 15000 }
  );
  // Dropdown sources are stable — cache them for longer and reuse across pages.
  const { data: teacherData } = useApiQuery(
    "teachers:all",
    () => api.get("/teachers", { params: { size: 100 } }).then((r) => r.data),
    { staleTime: 60000 }
  );
  const { data: courseData } = useApiQuery(
    "courses:all",
    () => api.get("/courses", { params: { size: 100 } }).then((r) => r.data),
    { staleTime: 60000 }
  );
  const rows = data?.items || [];
  const teachers = teacherData?.items || [];
  const courses = courseData?.items || [];

  const create = async (e) => {
    e.preventDefault();
    await api.post("/groups", {
      ...form,
      course_id: form.course_id ? Number(form.course_id) : null,
      teacher_id: form.teacher_id ? Number(form.teacher_id) : null,
    });
    setOpen(false); setForm(EMPTY); invalidate("groups"); refetch();
  };
  const remove = async (id) => {
    if (!window.confirm(t("common.confirm_delete"))) return;
    await api.delete(`/groups/${id}`); invalidate("groups"); refetch();
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("groups.title")}</h1>
        {canWrite && (
          <button className="btn-primary" onClick={() => setOpen(true)}>+ {t("groups.add")}</button>
        )}
      </div>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full">
          <thead className="bg-slate-50"><tr>
            <th className="th">{t("groups.name")}</th>
            <th className="th">{t("groups.course")}</th>
            <th className="th">{t("groups.teacher")}</th>
            <th className="th">{t("groups.schedule")}</th>
            <th className="th">{t("groups.students")}</th>
            <th className="th">{t("common.actions")}</th>
          </tr></thead>
          <tbody>
            {rows.map((g) => (
              <tr key={g.id}>
                <td className="td font-medium">{g.name}</td>
                <td className="td">{g.course_name || "-"}</td>
                <td className="td">{g.teacher_name || "-"}</td>
                <td className="td">{[g.schedule_days, g.schedule_time].filter(Boolean).join(" ")}</td>
                <td className="td">{g.student_count}</td>
                <td className="td">
                  {canWrite && (
                    <button onClick={() => remove(g.id)} className="text-red-600 hover:underline">{t("common.delete")}</button>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td className="td text-slate-400" colSpan={6}>{t("common.no_data")}</td></tr>}
          </tbody>
        </table>
      </div>
      <Pager page={page} size={SIZE} total={data?.total || 0} onPage={setPage} />

      <Modal open={open} title={t("groups.add")} onClose={() => setOpen(false)}>
        <form onSubmit={create} className="space-y-3">
          <input className="input" placeholder={t("groups.name")} value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <select className="input" value={form.course_id}
                  onChange={(e) => setForm({ ...form, course_id: e.target.value })}>
            <option value="">— {t("groups.course")} —</option>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select className="input" value={form.teacher_id}
                  onChange={(e) => setForm({ ...form, teacher_id: e.target.value })}>
            <option value="">— {t("groups.teacher")} —</option>
            {teachers.map((x) => <option key={x.id} value={x.id}>{x.full_name}</option>)}
          </select>
          <input className="input" placeholder="Mon,Wed,Fri" value={form.schedule_days}
                 onChange={(e) => setForm({ ...form, schedule_days: e.target.value })} />
          <input className="input" placeholder="18:00-19:30" value={form.schedule_time}
                 onChange={(e) => setForm({ ...form, schedule_time: e.target.value })} />
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>{t("common.cancel")}</button>
            <button className="btn-primary">{t("common.create")}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
