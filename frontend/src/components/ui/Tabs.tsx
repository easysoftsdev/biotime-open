"use client";

import { cn } from "@/lib/utils";

export interface TabItem {
  key: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: TabItem[];
  active: string;
  onChange: (key: string) => void;
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="flex items-center gap-1 border-b border-[hsl(var(--border))] mb-5">
      {tabs.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={cn(
            "px-3.5 py-2.5 text-sm transition-colors border-b-2 -mb-px",
            active === t.key
              ? "border-blue-500 text-blue-400 font-medium"
              : "border-transparent text-slate-400 hover:text-slate-200"
          )}
        >
          {t.label}
          {typeof t.count === "number" && (
            <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-700/60 text-slate-300">
              {t.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
