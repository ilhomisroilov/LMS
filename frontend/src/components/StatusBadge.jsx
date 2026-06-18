const COLORS = {
  active: "bg-green-100 text-green-700", frozen: "bg-amber-100 text-amber-700",
  graduated: "bg-slate-100 text-slate-600",
  paid: "bg-green-100 text-green-700", unpaid: "bg-red-100 text-red-700",
  partial: "bg-amber-100 text-amber-700",
  present: "bg-green-100 text-green-700", absent: "bg-red-100 text-red-700",
  late: "bg-amber-100 text-amber-700",
};
export default function StatusBadge({ status, label }) {
  return <span className={`badge ${COLORS[status] || "bg-slate-100 text-slate-600"}`}>{label || status}</span>;
}
