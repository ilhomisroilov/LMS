import { useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/axios";
import Modal from "../components/Modal.jsx";
import Pager from "../components/Pager.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useApiQuery, useDebounced, invalidate } from "../hooks/useApiQuery";
import { canAccess } from "../utils/authz.js";

const EMPTY = { full_name: "", phone: "", parent_phone: "", status: "active", password: "student123" };
const SIZE = 25;

export default function Students() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canWrite = canAccess(user, { permissions: ["student:write"] });
  const [q, setQ] = useState("");
  const dq = useDebounced(q, 300);          // debounce search -> one request after typing stops
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");

  const { data, refetch } = useApiQuery(
    `students:${page}:${dq}`,
    () => api.get("/students", { params: { q: dq || undefined, page, size: SIZE } }).then((r) => r.data),
    { staleTime: 15000 }
  );
  const rows = data?.items || [];

  const create = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/students", form);
      setOpen(false); setForm(EMPTY); invalidate("students"); refetch();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 409) {
        setError(typeof detail === "string" ? detail : t("students.phone_exists"));
      } else {
        setError(t("students.create_error"));
      }
    }
  };
  const remove = async (id) => {
    if (!window.confirm(t("common.confirm_delete"))) return;
    await api.delete(`/students/${id}`); invalidate("students"); refetch();
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("students.title")}</h1>
        {canWrite && (
          <button className="btn-primary" onClick={() => { setError(""); setOpen(true); }}>+ {t("students.add")}</button>
        )}
      </div>
      <input className="input mb-4 max-w-xs" placeholder={t("students.search")}
             value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className="th">{t("students.name")}</th>
              <th className="th">{t("students.phone")}</th>
              <th className="th">{t("students.parent_phone")}</th>
              <th className="th">{t("students.status")}</th>
              <th className="th">{t("students.groups")}</th>
              <th className="th">{t("common.actions")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <td className="td font-medium">{s.full_name}</td>
                <td className="td">{s.phone}</td>
                <td className="td">{s.parent_phone || "-"}</td>
                <td className="td"><StatusBadge status={s.status} label={t(`students.${s.status}`)} /></td>
                <td className="td">{s.group_ids?.length || 0}</td>
                <td className="td">
                  {canWrite && (
                    <button onClick={() => remove(s.id)} className="text-red-600 hover:underline">
                      {t("common.delete")}
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td className="td text-slate-400" colSpan={6}>{t("common.no_data")}</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <Pager page={page} size={SIZE} total={data?.total || 0} onPage={setPage} />

      <Modal open={open} title={t("students.add")} onClose={() => { setError(""); setOpen(false); }}>
        <form onSubmit={create} className="space-y-3">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}
          {["full_name", "phone", "parent_phone"].map((f) => (
            <input key={f} className="input" placeholder={t(`students.${f === "full_name" ? "name" : f}`)}
                   value={form[f]} onChange={(e) => setForm({ ...form, [f]: e.target.value })}
                   required={f !== "parent_phone"} />
          ))}
          <select className="input" value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="active">{t("students.active")}</option>
            <option value="frozen">{t("students.frozen")}</option>
            <option value="graduated">{t("students.graduated")}</option>
          </select>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>{t("common.cancel")}</button>
            <button className="btn-primary">{t("common.create")}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
