import { useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/axios";
import Modal from "../components/Modal.jsx";
import Pager from "../components/Pager.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useApiQuery, invalidate } from "../hooks/useApiQuery";
import { canAccess } from "../utils/authz.js";

const EMPTY = { full_name: "", phone: "", salary: "", subjects: "", password: "teacher123" };
const SIZE = 25;

export default function Teachers() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canWrite = canAccess(user, { permissions: ["teacher:write"] });
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");

  const { data, refetch } = useApiQuery(
    `teachers:${page}`,
    () => api.get("/teachers", { params: { page, size: SIZE } }).then((r) => r.data),
    { staleTime: 15000 }
  );
  const rows = data?.items || [];

  const create = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/teachers", { ...form, salary: form.salary ? Number(form.salary) : null });
      setOpen(false); setForm(EMPTY); invalidate("teachers"); refetch();
    } catch (err) {
      setError(err.response?.status === 409
        ? (err.response.data?.detail || t("common.already_exists"))
        : t("common.create"));
    }
  };
  const remove = async (id) => {
    if (!window.confirm(t("common.confirm_delete"))) return;
    await api.delete(`/teachers/${id}`); invalidate("teachers"); refetch();
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("teachers.title")}</h1>
        {canWrite && (
          <button className="btn-primary" onClick={() => { setError(""); setOpen(true); }}>+ {t("teachers.add")}</button>
        )}
      </div>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full">
          <thead className="bg-slate-50"><tr>
            <th className="th">{t("teachers.name")}</th>
            <th className="th">{t("teachers.phone")}</th>
            <th className="th">{t("teachers.salary")}</th>
            <th className="th">{t("teachers.subjects")}</th>
            <th className="th">{t("common.actions")}</th>
          </tr></thead>
          <tbody>
            {rows.map((x) => (
              <tr key={x.id}>
                <td className="td font-medium">{x.full_name}</td>
                <td className="td">{x.phone}</td>
                <td className="td">{x.salary ? new Intl.NumberFormat().format(x.salary) : "-"}</td>
                <td className="td">{x.subjects || "-"}</td>
                <td className="td">
                  {canWrite && (
                    <button onClick={() => remove(x.id)} className="text-red-600 hover:underline">{t("common.delete")}</button>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td className="td text-slate-400" colSpan={5}>{t("common.no_data")}</td></tr>}
          </tbody>
        </table>
      </div>
      <Pager page={page} size={SIZE} total={data?.total || 0} onPage={setPage} />

      <Modal open={open} title={t("teachers.add")} onClose={() => setOpen(false)}>
        <form onSubmit={create} className="space-y-3">
          {error && <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
          <input className="input" placeholder={t("teachers.name")} value={form.full_name}
                 onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          <input className="input" placeholder={t("teachers.phone")} value={form.phone}
                 onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <input className="input" placeholder={t("teachers.salary")} value={form.salary}
                 onChange={(e) => setForm({ ...form, salary: e.target.value })} />
          <input className="input" placeholder={t("teachers.subjects")} value={form.subjects}
                 onChange={(e) => setForm({ ...form, subjects: e.target.value })} />
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>{t("common.cancel")}</button>
            <button className="btn-primary">{t("common.create")}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
