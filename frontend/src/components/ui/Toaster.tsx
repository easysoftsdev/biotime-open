"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

type Kind = "success" | "error";
interface Toast {
  id: number;
  kind: Kind;
  message: string;
}

let toasts: Toast[] = [];
let listeners: Array<(t: Toast[]) => void> = [];
let seq = 0;

function emit() {
  listeners.forEach((l) => l([...toasts]));
}

export function toast(kind: Kind, message: string) {
  const id = ++seq;
  toasts = [...toasts, { id, kind, message }];
  emit();
  setTimeout(() => {
    toasts = toasts.filter((t) => t.id !== id);
    emit();
  }, 4500);
}

export function Toaster() {
  const [items, setItems] = useState<Toast[]>([]);

  useEffect(() => {
    listeners.push(setItems);
    return () => {
      listeners = listeners.filter((l) => l !== setItems);
    };
  }, []);

  if (!items.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[60] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
      {items.map((t) => (
        <div
          key={t.id}
          className={cn(
            "card px-3.5 py-3 flex items-start gap-2.5 shadow-xl shadow-black/40 animate-in",
            t.kind === "success" ? "border-emerald-500/30" : "border-red-500/30"
          )}
        >
          {t.kind === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          )}
          <p className="text-xs text-slate-200 flex-1">{t.message}</p>
          <button
            onClick={() => {
              toasts = toasts.filter((x) => x.id !== t.id);
              emit();
            }}
            className="text-slate-500 hover:text-slate-300"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
