import { useTranslation } from "react-i18next";

/** Minimal Prev/Next pager shown only when there is more than one page. */
export default function Pager({ page, size, total, onPage }) {
  const { t } = useTranslation();
  const pages = Math.max(1, Math.ceil((total || 0) / size));
  if (pages <= 1) return null;
  return (
    <div className="mt-3 flex items-center justify-end gap-2 text-sm">
      <button className="btn-ghost px-3 py-1" disabled={page <= 1}
              onClick={() => onPage(page - 1)}>←</button>
      <span className="text-slate-500">{page} / {pages}</span>
      <button className="btn-ghost px-3 py-1" disabled={page >= pages}
              onClick={() => onPage(page + 1)}>→</button>
    </div>
  );
}
