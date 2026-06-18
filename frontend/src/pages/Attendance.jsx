import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/axios";
import StatusBadge from "../components/StatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { canAccess } from "../utils/authz.js";

export default function Attendance() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canWrite = canAccess(user, { permissions: ["attendance:write"] });
  const [groups, setGroups] = useState([]);
  const [groupId, setGroupId] = useState("");
  const [students, setStudents] = useState([]);
  const [records, setRecords] = useState({});
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api.get("/groups", { params: { size: 100 } }).then((r) => setGroups(r.data.items));
  }, []);

  useEffect(() => {
    if (!groupId) return;
    api.get(`/groups/${groupId}/students`).then((r) => {
      setStudents(r.data);
      setRecords(Object.fromEntries(r.data.map((s) => [s.id, "present"])));
    });
    api.get(`/attendance/group/${groupId}`).then((r) => setHistory(r.data));
  }, [groupId]);

  const submit = async () => {
    await api.post("/attendance", {
      group_id: Number(groupId),
      lesson_date: date,
      records: Object.entries(records).map(([student_id, status]) => ({ student_id: Number(student_id), status })),
    });
    const r = await api.get(`/attendance/group/${groupId}`);
    setHistory(r.data);
  };

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">{t("attendance.title")}</h1>
      <div className="mb-4 flex flex-wrap gap-3">
        <select className="input max-w-xs" value={groupId} onChange={(e) => setGroupId(e.target.value)}>
          <option value="">— {t("attendance.select_group")} —</option>
          {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
        <input type="date" className="input max-w-[180px]" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      {students.length > 0 && (
        <div className="card mb-6">
          <table className="w-full">
            <thead><tr>
              <th className="th">{t("attendance.student")}</th>
              <th className="th">{t("attendance.status")}</th>
            </tr></thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id}>
                  <td className="td">{s.full_name}</td>
                  <td className="td">
                    <select className="input max-w-[160px]" value={records[s.id] || "present"}
                            onChange={(e) => setRecords({ ...records, [s.id]: e.target.value })}>
                      <option value="present">{t("attendance.present")}</option>
                      <option value="late">{t("attendance.late")}</option>
                      <option value="absent">{t("attendance.absent")}</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {canWrite && <button className="btn-primary mt-4" onClick={submit}>{t("common.save")}</button>}
        </div>
      )}

      {history.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full">
            <thead className="bg-slate-50"><tr>
              <th className="th">{t("attendance.date")}</th>
              <th className="th">{t("attendance.student")}</th>
              <th className="th">{t("attendance.status")}</th>
            </tr></thead>
            <tbody>
              {history.map((a) => (
                <tr key={a.id}>
                  <td className="td">{a.lesson_date}</td>
                  <td className="td">{a.student_name}</td>
                  <td className="td"><StatusBadge status={a.status} label={t(`attendance.${a.status}`)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
