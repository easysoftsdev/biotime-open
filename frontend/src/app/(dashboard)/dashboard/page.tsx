"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import {
  UserCheck,
  UserX,
  Clock3,
  WifiOff,
  Monitor,
  Users,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { Page } from "@/components/layout/Page";
import { StatCard } from "@/components/ui/StatCard";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { toast } from "@/components/ui/Toaster";
import { attendanceApi, devicesApi, employeesApi, leaveApi, reportsApi } from "@/lib/api";
import { apiErrorMessage, formatTime, statusBg, timeAgo } from "@/lib/utils";
import type { AttendanceEvent, Device, LeaveRequest } from "@/types";

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const today = format(new Date(), "yyyy-MM-dd");

  const summary = useQuery({
    queryKey: ["attendance", "summary", today],
    queryFn: async () => (await attendanceApi.summary(today)).data,
  });

  const employees = useQuery({
    queryKey: ["employees", "total"],
    queryFn: async () => (await employeesApi.list({ page: 1, page_size: 1 })).data,
  });

  const deviceHealth = useQuery({
    queryKey: ["reports", "device-health"],
    queryFn: async () => (await reportsApi.deviceHealth()).data as Record<string, number>,
  });

  const devices = useQuery({
    queryKey: ["devices", "all"],
    queryFn: async () => (await devicesApi.list()).data as Device[],
  });

  const live = useQuery({
    queryKey: ["attendance", "live", 12],
    queryFn: async () => (await attendanceApi.live(12)).data as AttendanceEvent[],
  });

  const pendingLeave = useQuery({
    queryKey: ["leave", "requests", "pending"],
    queryFn: async () => (await leaveApi.requests({ req_status: "pending" })).data as LeaveRequest[],
  });

  const decide = useMutation({
    mutationFn: ({ id, approve }: { id: string; approve: boolean }) =>
      leaveApi.approve(id, { approve, rejection_reason: approve ? null : "Rejected from dashboard" }),
    onSuccess: (_d, vars) => {
      toast("success", vars.approve ? "Leave request approved" : "Leave request rejected");
      queryClient.invalidateQueries({ queryKey: ["leave", "requests"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const online = deviceHealth.data?.online ?? 0;
  const offline = deviceHealth.data?.offline ?? 0;
  const totalDevices = (online + offline + (deviceHealth.data?.unknown ?? 0)) || (devices.data?.length ?? 0);

  if (summary.isLoading) return <PageSpinner />;

  return (
    <Page title="Dashboard" subtitle="Today at a glance — attendance, devices and approvals">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Present"
          value={summary.data?.present ?? 0}
          subtitle={`${summary.data?.total_records ?? 0} records today`}
          icon={UserCheck}
          iconColor="text-emerald-400"
        />
        <StatCard
          title="Absent"
          value={summary.data?.absent ?? 0}
          subtitle="No punch recorded"
          icon={UserX}
          iconColor="text-red-400"
        />
        <StatCard
          title="Late arrivals"
          value={summary.data?.late ?? 0}
          subtitle="Past grace period"
          icon={Clock3}
          iconColor="text-amber-400"
        />
        <StatCard
          title="Employees"
          value={employees.data?.total ?? 0}
          subtitle={`${online}/${totalDevices} devices online`}
          icon={Users}
          iconColor="text-blue-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Live feed */}
        <div className="card lg:col-span-2 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-[hsl(var(--border))]">
            <div>
              <h2 className="text-sm font-semibold text-white">Live punch feed</h2>
              <p className="text-xs text-slate-500 mt-0.5">Latest events received from devices</p>
            </div>
            <Link href="/attendance" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          {live.isLoading ? (
            <PageSpinner />
          ) : !live.data?.length ? (
            <EmptyState title="No punches yet" message="Events will appear here as devices report them." />
          ) : (
            <ul className="divide-y divide-[hsl(var(--border))] max-h-96 overflow-y-auto">
              {live.data.map((ev) => (
                <li key={ev.id} className="flex items-center gap-3 px-5 py-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-600/15 text-blue-400 flex items-center justify-center shrink-0">
                    <Clock3 className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200 truncate">
                      <span className="font-mono">{ev.device_user_id}</span>
                      {ev.employee_id ? "" : " (unmatched)"}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      {formatTime(ev.event_time)} · verify {ev.verify_type ?? "—"} · {timeAgo(ev.event_time)}
                    </p>
                  </div>
                  <Badge variant={ev.processed ? "success" : "warning"}>
                    {ev.processed ? "processed" : "pending"}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-5">
          {/* Device health */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">Device health</h2>
              <Link href="/devices" className="text-xs text-blue-400 hover:text-blue-300">
                Manage
              </Link>
            </div>
            {deviceHealth.isLoading ? (
              <PageSpinner />
            ) : Object.keys(deviceHealth.data ?? {}).length === 0 ? (
              <EmptyState title="No devices" message="Add a device to start collecting punches." />
            ) : (
              <div className="space-y-3">
                {Object.entries(deviceHealth.data ?? {}).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm text-slate-300 capitalize">
                      <Monitor className="w-3.5 h-3.5 text-slate-500" />
                      {status}
                    </span>
                    <StatusBadge status={status} label={String(count)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Pending approvals */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">Pending approvals</h2>
              <Link href="/leave" className="text-xs text-blue-400 hover:text-blue-300">
                All requests
              </Link>
            </div>
            {!pendingLeave.data?.length ? (
              <EmptyState title="All clear" message="No leave requests waiting for you." />
            ) : (
              <ul className="space-y-3">
                {pendingLeave.data.slice(0, 5).map((req) => (
                  <li key={req.id} className="flex items-center gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-200 truncate">
                        {format(req.start_date, "dd MMM")} – {format(req.end_date, "dd MMM")} · {req.days}d
                      </p>
                      <p className="text-[11px] text-slate-500 truncate">{req.reason || "No reason given"}</p>
                    </div>
                    <button
                      onClick={() => decide.mutate({ id: req.id, approve: true })}
                      disabled={decide.isPending}
                      className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
                      aria-label="Approve"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => decide.mutate({ id: req.id, approve: false })}
                      disabled={decide.isPending}
                      className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors disabled:opacity-50"
                      aria-label="Reject"
                    >
                      <UserX className="w-3.5 h-3.5" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Quick links */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-white mb-3">Quick actions</h2>
            <div className="grid grid-cols-2 gap-2">
              <Link href="/employees" className="btn-ghost text-center text-xs">
                Add employee
              </Link>
              <Link href="/devices" className="btn-ghost text-center text-xs">
                Add device
              </Link>
              <Link href="/attendance" className="btn-ghost text-center text-xs">
                Manual punch
              </Link>
              <Link href="/reports" className="btn-ghost text-center text-xs">
                Run report
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Offline devices banner */}
      {offline > 0 && (
        <div className="mt-5 flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
          <WifiOff className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-sm text-red-300">
            {offline} device{offline > 1 ? "s" : ""} offline — records may be missing until they reconnect.
          </p>
          <span className={statusBg("offline")}>OFFLINE</span>
        </div>
      )}
    </Page>
  );
}
