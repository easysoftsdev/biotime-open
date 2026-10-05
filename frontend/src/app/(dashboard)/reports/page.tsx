"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Monitor, Link2, FileBarChart, Play } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { employeesApi, reportsApi } from "@/lib/api";
import { apiErrorMessage } from "@/lib/utils";

const DEVICE_COLORS: Record<string, string> = {
  online: "text-emerald-400",
  offline: "text-red-400",
  unknown: "text-slate-400",
  disabled: "text-slate-500",
};

const PUSH_COLORS: Record<string, string> = {
  sent: "text-emerald-400",
  failed: "text-red-400",
  queued: "text-amber-400",
  retrying: "text-blue-400",
  dead: "text-red-400",
};

export default function ReportsPage() {
  const [range, setRange] = useState({ start_date: "", end_date: "" });
  const [result, setResult] = useState<{ task_id: string; message: string } | null>(null);

  const deviceHealth = useQuery({
    queryKey: ["reports", "device-health"],
    queryFn: async () => (await reportsApi.deviceHealth()).data as Record<string, number>,
  });

  const hrmHealth = useQuery({
    queryKey: ["reports", "hrm-push"],
    queryFn: async () => (await reportsApi.hrmPush()).data as Record<string, number>,
  });

  const employees = useQuery({
    queryKey: ["employees", "total"],
    queryFn: async () => (await employeesApi.list({ page: 1, page_size: 1 })).data as { total: number },
  });

  const run = useMutation({
    mutationFn: () => reportsApi.attendance(range),
    onSuccess: (res) => {
      setResult(res.data);
      toast("success", "Report generation started");
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const totalDevices = Object.values(deviceHealth.data ?? {}).reduce((a, b) => a + b, 0);
  const totalPush = Object.values(hrmHealth.data ?? {}).reduce((a, b) => a + b, 0);

  return (
    <Page title="Reports" subtitle="Operational insights and export jobs">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Employees"
          value={employees.data?.total ?? 0}
          subtitle="Active workforce"
          icon={FileBarChart}
          iconColor="text-blue-400"
        />
        <StatCard
          title="Devices"
          value={totalDevices}
          subtitle={`${deviceHealth.data?.online ?? 0} online`}
          icon={Monitor}
          iconColor="text-emerald-400"
        />
        <StatCard
          title="Push jobs"
          value={totalPush}
          subtitle={`${hrmHealth.data?.sent ?? 0} delivered`}
          icon={Link2}
          iconColor="text-indigo-400"
        />
        <StatCard
          title="Failed deliveries"
          value={(hrmHealth.data?.failed ?? 0) + (hrmHealth.data?.dead ?? 0)}
          subtitle="Needs attention"
          icon={Link2}
          iconColor="text-red-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileBarChart className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-white">Attendance report</h2>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            Generates a per-employee summary for a date range. The job runs in the background and
            the result is stored as a report artifact.
          </p>

          <div className="flex flex-wrap items-end gap-3">
            <Field label="From" required>
              <input
                type="date"
                className="input w-44"
                value={range.start_date}
                onChange={(e) => setRange({ ...range, start_date: e.target.value })}
              />
            </Field>
            <Field label="To" required>
              <input
                type="date"
                className="input w-44"
                min={range.start_date}
                value={range.end_date}
                onChange={(e) => setRange({ ...range, end_date: e.target.value })}
              />
            </Field>
            <button
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
              disabled={run.isPending || !range.start_date || !range.end_date}
              onClick={() => run.mutate()}
            >
              <Play className="w-4 h-4" />
              {run.isPending ? "Starting…" : "Generate"}
            </button>
          </div>

          {result && (
            <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-emerald-300">{result.message}</p>
                  <p className="text-[11px] text-emerald-400/70 font-mono mt-0.5">
                    task_id: {result.task_id}
                  </p>
                </div>
                <Badge variant="success">running</Badge>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-5">
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-4">Device health</h2>
            {deviceHealth.isLoading ? (
              <PageSpinner />
            ) : !Object.keys(deviceHealth.data ?? {}).length ? (
              <EmptyState title="No devices" message="Register a device to see health stats." />
            ) : (
              <ul className="space-y-3">
                {Object.entries(deviceHealth.data ?? {}).map(([status, count]) => (
                  <li key={status} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300 capitalize">{status}</span>
                    <span className={`text-sm font-semibold ${DEVICE_COLORS[status] ?? "text-slate-400"}`}>
                      {count}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-4">HRM push outcomes</h2>
            {hrmHealth.isLoading ? (
              <PageSpinner />
            ) : !Object.keys(hrmHealth.data ?? {}).length ? (
              <EmptyState title="No push jobs" message="Add a target to start pushing events." />
            ) : (
              <ul className="space-y-3">
                {Object.entries(hrmHealth.data ?? {}).map(([status, count]) => (
                  <li key={status} className="flex items-center justify-between">
                    <span className="text-sm text-slate-300 capitalize">{status}</span>
                    <span className={`text-sm font-semibold ${PUSH_COLORS[status] ?? "text-slate-400"}`}>
                      {count}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </Page>
  );
}
