import { cn } from "@/lib/utils";

export function Page({
  title,
  subtitle,
  actions,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <>
      <div className="h-14 shrink-0 border-b border-[hsl(var(--border))] flex items-center justify-between gap-4 px-6">
        <div className="min-w-0">
          <h1 className="text-base font-semibold text-white truncate">{title}</h1>
          {subtitle && <p className="text-xs text-slate-400 truncate">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
      </div>
      <main className={cn("flex-1 overflow-y-auto p-6", className)}>{children}</main>
    </>
  );
}
