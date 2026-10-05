import { ChevronLeft, ChevronRight, Inbox } from "lucide-react";

export function EmptyState({
  title = "No data",
  message,
  action,
}: {
  title?: string;
  message?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <div className="w-11 h-11 rounded-xl bg-[hsl(var(--muted))] flex items-center justify-center mb-3">
        <Inbox className="w-5 h-5 text-slate-500" />
      </div>
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {message && <p className="text-xs text-slate-500 mt-1 max-w-sm">{message}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(total, page * pageSize);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-[hsl(var(--border))]">
      <p className="text-xs text-slate-500">
        Showing {from}–{to} of {total}
      </p>
      <div className="flex items-center gap-1">
        <button
          className="btn-ghost p-1.5 disabled:opacity-40"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-xs text-slate-400 px-2">
          {page} / {pages}
        </span>
        <button
          className="btn-ghost p-1.5 disabled:opacity-40"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
