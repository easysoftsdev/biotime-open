import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateTime(dt: string | null | undefined): string {
  if (!dt) return "—";
  return format(new Date(dt), "dd MMM yyyy, HH:mm");
}

export function formatDate(dt: string | null | undefined): string {
  if (!dt) return "—";
  return format(new Date(dt), "dd MMM yyyy");
}

export function formatTime(dt: string | null | undefined): string {
  if (!dt) return "—";
  return format(new Date(dt), "HH:mm");
}

export function timeAgo(dt: string | null | undefined): string {
  if (!dt) return "never";
  return formatDistanceToNow(new Date(dt), { addSuffix: true });
}

export function minutesToHHMM(minutes: number): string {
  if (!minutes) return "0h 0m";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    online:    "text-emerald-400",
    offline:   "text-red-400",
    unknown:   "text-slate-400",
    disabled:  "text-slate-500",
    present:   "text-emerald-400",
    absent:    "text-red-400",
    half_day:  "text-amber-400",
    on_leave:  "text-blue-400",
    holiday:   "text-purple-400",
    pending:   "text-amber-400",
    approved:  "text-emerald-400",
    rejected:  "text-red-400",
    sent:      "text-emerald-400",
    failed:    "text-red-400",
    queued:    "text-amber-400",
    retrying:  "text-blue-400",
  };
  return map[status?.toLowerCase()] ?? "text-slate-400";
}

export function statusBg(status: string): string {
  const map: Record<string, string> = {
    online:   "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    offline:  "bg-red-500/10 text-red-400 border-red-500/20",
    present:  "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    absent:   "bg-red-500/10 text-red-400 border-red-500/20",
    half_day: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    pending:  "bg-amber-500/10 text-amber-400 border-amber-500/20",
    approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    rejected: "bg-red-500/10 text-red-400 border-red-500/20",
    sent:     "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    failed:   "bg-red-500/10 text-red-400 border-red-500/20",
    queued:   "bg-amber-500/10 text-amber-400 border-amber-500/20",
  };
  return map[status?.toLowerCase()] ?? "bg-slate-500/10 text-slate-400 border-slate-500/20";
}

export function apiErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  const anyErr = err as {
    response?: { data?: { detail?: unknown } };
    message?: string;
  };
  const detail = anyErr?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d: { msg?: string }) => d?.msg ?? JSON.stringify(d)).join(", ");
  }
  if (detail && typeof detail === "object" && "msg" in detail) {
    return String((detail as { msg: string }).msg);
  }
  if (anyErr?.message) return anyErr.message;
  return fallback;
}
