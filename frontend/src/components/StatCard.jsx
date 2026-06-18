export default function StatCard({ label, value, accent = "text-brand" }) {
  return (
    <div className="card">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-2 text-3xl font-bold ${accent}`}>{value}</div>
    </div>
  );
}
