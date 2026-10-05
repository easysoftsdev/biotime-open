"use client";

import { cn } from "@/lib/utils";

export function Field({
  label,
  required,
  hint,
  error,
  children,
  className,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label className="text-xs font-medium text-slate-400">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
      {hint && !error && <p className="text-[11px] text-slate-500">{hint}</p>}
      {error && <p className="text-[11px] text-red-400">{error}</p>}
    </div>
  );
}

export function Row({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("grid gap-4", className)}>{children}</div>;
}
