import { useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/axios";
import Modal from "../components/Modal.jsx";
import Pager from "../components/Pager.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useApiQuery, invalidate } from "../hooks/useApiQuery";
import { canAccess } from "../utils/authz.js";

const SIZE = 25;

export default function Payments() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canWrite = canAccess(user, { permissions: ["payment:write"] });
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const month = new Date().toISOString().slice(0, 7);
  const [form, setForm] = useState({ student_id: "", amount: "", amount_paid: "", month });

  const { data, refetch } = useApiQuery(
    `payments:${page}`,
    () => api.get("/payments", { params: { page, size: SIZE } }).then((r) => r.data),
    { staleTime: 15000 }
  );
  const { data: studentData } = useApiQuery(
    "students:all",
    () => api.get("/students", { params: { size: 100 } }).then((r) => r.data),
    { staleTime: 60000 }
  );
  const rows = data?.items || [];
  const students = studentData?.items || [];

  const create = async (e) => {
    e.preventDefault();
    await api.post("/payments", {
      student_id: Number(form.student_id),
      amount: Number(form.amount),
      amount_paid: Number(form.amount_paid || 0),
      month: form.month,
    });
    setOpen(false); invalidate("payments"); refetch();
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("payments.title")}</h1>
        {canWrite && (
          <button className="btn-primary" onClick={() => setOpen(true)}>+ {t("payments.add")}</button>
        )}
      </div>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full">
          <thead className="bg-slate-50"><tr>
            <th className="th">{t("payments.student")}</th>
            <th className="th">{t("payments.month")}</th>
            <th className="th">{t("payments.amount")}</th>
            <th className="th">{t("payments.paid")}</th>
            <th className="th">{t("payments.status")}</th>
          </tr></thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td className="td">{p.student_name}</td>
                <td className="td">{p.month}</td>
                <td className="td">{new Intl.NumberFormat().format(p.amount)}</td>
                <td className="td">{new Intl.NumberFormat().format(p.amount_paid)}</td>
                <td className="td"><StatusBadge status={p.status} label={t(`payments.status_${p.status}`)} /></td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td className="td text-slate-400" colSpan={5}>{t("common.no_data")}</td></tr>}
          </tbody>
        </table>
      </div>
      <Pager page={page} size={SIZE} total={data?.total || 0} onPage={setPage} />

      <Modal open={open} title={t("payments.add")} onClose={() => setOpen(false)}>
        <form onSubmit={create} className="space-y-3">
          <select className="input" value={form.student_id} required
                  onChange={(e) => setForm({ ...form, student_id: e.target.value })}>
            <option value="">— {t("payments.student")} —</option>
            {students.map((s) => <option key={s.id} value={s.id}>{s.full_name}</option>)}
          </select>
          <input className="input" type="number" placeholder={t("payments.amount")} value={form.amount}
                 onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          <input className="input" type="number" placeholder={t("payments.paid")} value={form.amount_paid}
                 onChange={(e) => setForm({ ...form, amount_paid: e.target.value })} />
          <input className="input" placeholder="2026-06" value={form.month}
                 onChange={(e) => setForm({ ...form, month: e.target.value })} required />
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setOpen(false)}>{t("common.cancel")}</button>
            <button className="btn-primary">{t("common.create")}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
