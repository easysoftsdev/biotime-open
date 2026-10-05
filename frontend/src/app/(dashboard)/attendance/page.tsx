"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, RefreshCcw, Radio, Check, X } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import { StatusBadge, Badge } from "@/components/ui/Badge";
import { EmptyState, Pagination } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { Modal } from "@/components/ui/Modal";
import { Tabs } from "@/components/ui/Tabs";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { attendanceApi, employeesApi } from "@/lib/api";
import { apiErrorMessage, formatTime, minutesToHHMM, statusColor } from "@/lib/utils";
import type { AttendanceEvent, AttendanceRecord, Employee, ManualPunch, PaginatedResponse } from "@/types";

const STATUSES = ["present", "absent", "late", "early_leave", "on_leave", "holiday", "half_day", "overtime"];

export default function AttendancePage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("records");
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [range, setRange] = useState({ start: "", end: "" });
  const pageSize = 25;

  const [punchOpen, setPunchOpen] = useState(false);
  const [punch, setPunch] = useState({ employee_id: "", requested_time: "", punch_type: "in", reason: "" });
  const [recalcOpen, setRecalcOpen] = useState(false);
  const [recalc, setRecalc] = useState({ start_date: "", end_date: "" });
  const [rejectTarget, setRejectTarget] = useState<ManualPunch | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const records = useQuery({
    queryKey: ["attendance", "records", page, status, range],
    queryFn: async () =>
      (
        await attendanceApi.list({
          page,
          page_size: pageSize,
          status: status || undefined,
          start_date: range.start || undefined,
          end_date: range.end || undefined,
        })
      ).data as PaginatedResponse<AttendanceRecord>,
  });

  const live = useQuery({
    queryKey: ["attendance", "live", 50],
    queryFn: async () => (await attendanceApi.live(50)).data as AttendanceEvent[],
    enabled: tab === "live",
    refetchInterval: tab === "live" ? 10_000 : false,
  });

  const employees = useQuery({
    queryKey: ["employees", "map"],
    queryFn: async () =>
      (await employeesApi.list({ page: 1, page_size: 200 })).data as PaginatedResponse<Employee>,
  });

  const approvals = useQuery({
    queryKey: ["attendance", "manual-punches"],
    queryFn: async () =>
      (await attendanceApi.listManualPunches({ limit: 200 })).data as ManualPunch[],
    refetchInterval: 30_000,
  });

  const pendingCount = approvals.data?.filter((p) => p.status === "pending").length ?? 0;

  const nameOf = (id: string) => {
    const emp = employees.data?.items.find((e) => e.id === id);
    return emp ? `${emp.first_name} ${emp.last_name}` : id.slice(0, 8);
  };

  const createPunch = useMutation({
    mutationFn: () =>
      attendanceApi.manualPunch({
        employee_id: punch.employee_id,
        requested_time: new Date(punch.requested_time).toISOString(),
        punch_type: punch.punch_type,
        reason: punch.reason || null,
      }),
    onSuccess: () => {
      toast("success", "Manual punch submitted for approval");
      setPunchOpen(false);
      setPunch({ employee_id: "", requested_time: "", punch_type: "in", reason: "" });
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
      setTab("approvals");
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const runRecalc = useMutation({
    mutationFn: () => attendanceApi.recalculate(recalc),
    onSuccess: () => {
      toast("success", "Recalculation queued");
      setRecalcOpen(false);
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const decidePunch = useMutation({
    mutationFn: ({ id, approve, reason }: { id: string; approve: boolean; reason?: string }) =>
      attendanceApi.approvePunch(id, approve, reason),
    onSuccess: (_res, vars) => {
      toast("success", vars.approve ? "Punch approved" : "Punch request rejected");
      setRejectTarget(null);
      setRejectReason("");
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const items = records.data?.items ?? [];

  return (
    <Page
      title="Attendance"
      subtitle="Daily records and raw punch events"
      actions={
        <>
          <button className="btn-ghost flex items-center gap-2" onClick={() => setRecalcOpen(true)}>
            <RefreshCcw className="w-4 h-4" /> Recalculate
          </button>
          <button className="btn-primary flex items-center gap-2" onClick={() => setPunchOpen(true)}>
            <Plus className="w-4 h-4" /> Manual punch
          </button>
        </>
      }
    >
      <Tabs
        tabs={[
          { key: "records", label: "Records", count: records.data?.total },
          { key: "approvals", label: "Approvals", count: pendingCount || undefined },
          { key: "live", label: "Live feed", count: live.data?.length },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "records" ? (
        <>
          <div className="flex flex-wrap items-end gap-2 mb-4">
            <Field label="From">
              <input
                type="date"
                className="input w-40"
                value={range.start}
                onChange={(e) => {
                  setRange({ ...range, start: e.target.value });
                  setPage(1);
                }}
              />
            </Field>
            <Field label="To">
              <input
                type="date"
                className="input w-40"
                value={range.end}
                onChange={(e) => {
                  setRange({ ...range, end: e.target.value });
                  setPage(1);
                }}
              />
            </Field>
            <Field label="Status">
              <select
                className="input w-40"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">All</option>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </select>
            </Field>
            {(range.start || range.end || status) && (
              <button
                className="btn-ghost mb-0.5"
                onClick={() => {
                  setRange({ start: "", end: "" });
                  setStatus("");
                  setPage(1);
                }}
              >
                Clear
              </button>
            )}
          </div>

          <div className="card overflow-hidden">
            {records.isLoading ? (
              <PageSpinner />
            ) : !items.length ? (
              <EmptyState title="No records" message="Adjust the filters or wait for device sync." />
            ) : (
              <>
                <Table>
                  <Thead>
                    <Th>Date</Th>
                    <Th>Employee</Th>
                    <Th>First in</Th>
                    <Th>Last out</Th>
                    <Th>Worked</Th>
                    <Th>Late</Th>
                    <Th>Overtime</Th>
                    <Th>Status</Th>
                  </Thead>
                  <Tbody>
                    {items.map((r) => (
                      <Tr key={r.id}>
                        <Td className="text-xs">{r.date}</Td>
                        <Td className="text-sm text-white">{nameOf(r.employee_id)}</Td>
                        <Td className="text-xs">{formatTime(r.first_in)}</Td>
                        <Td className="text-xs">{formatTime(r.last_out)}</Td>
                        <Td className="text-xs">{minutesToHHMM(r.total_work_minutes)}</Td>
                        <Td className={`text-xs ${r.late_minutes > 0 ? "text-red-400" : "text-slate-500"}`}>
                          {r.late_minutes ? `${r.late_minutes}m` : "—"}
                        </Td>
                        <Td className="text-xs">{r.overtime_minutes ? `${r.overtime_minutes}m` : "—"}</Td>
                        <Td>
                          <span className={statusColor(r.status)}>
                            <StatusBadge status={r.status} />
                          </span>
                          {r.is_manual && <Badge className="ml-1.5">manual</Badge>}
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                <Pagination
                  page={page}
                  pageSize={pageSize}
                  total={records.data?.total ?? 0}
                  onPageChange={setPage}
                />
              </>
            )}
          </div>
        </>
      ) : tab === "approvals" ? (
        <div className="card overflow-hidden">
          {approvals.isLoading ? (
            <PageSpinner />
          ) : !approvals.data?.length ? (
            <EmptyState
              title="No punch requests"
              message="Requests submitted with Manual punch appear here for approval."
            />
          ) : (
            <Table>
              <Thead>
                <Th>Submitted</Th>
                <Th>Employee</Th>
                <Th>Punch time</Th>
                <Th>Type</Th>
                <Th>Reason</Th>
                <Th>Status</Th>
                <Th className="text-right">Action</Th>
              </Thead>
              <Tbody>
                {approvals.data.map((p) => (
                  <Tr key={p.id}>
                    <Td className="text-xs">{formatTime(p.created_at)}</Td>
                    <Td className="text-sm text-white">{nameOf(p.employee_id)}</Td>
                    <Td className="text-xs">{formatTime(p.requested_time)}</Td>
                    <Td className="text-xs">{p.punch_type === "in" ? "Clock in" : "Clock out"}</Td>
                    <Td className="text-xs text-slate-400">{p.reason || "—"}</Td>
                    <Td>
                      <Badge
                        variant={
                          p.status === "approved"
                            ? "success"
                            : p.status === "rejected"
                              ? "danger"
                              : "warning"
                        }
                      >
                        {p.status}
                      </Badge>
                      {p.status === "rejected" && p.rejected_reason && (
                        <span className="ml-1.5 text-[11px] text-slate-500">
                          {p.rejected_reason}
                        </span>
                      )}
                    </Td>
                    <Td className="text-right">
                      {p.status === "pending" ? (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            className="btn-primary disabled:opacity-50"
                            disabled={decidePunch.isPending}
                            onClick={() => decidePunch.mutate({ id: p.id, approve: true })}
                          >
                            <Check className="w-3.5 h-3.5 inline mr-1" />
                            Approve
                          </button>
                          <button
                            className="btn-ghost disabled:opacity-50"
                            disabled={decidePunch.isPending}
                            onClick={() => setRejectTarget(p)}
                          >
                            <X className="w-3.5 h-3.5 inline mr-1" />
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">
                          {p.approved_at ? formatTime(p.approved_at) : "—"}
                        </span>
                      )}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-[hsl(var(--border))]">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-400">Auto-refreshes every 10 seconds</span>
          </div>
          {live.isLoading ? (
            <PageSpinner />
          ) : !live.data?.length ? (
            <EmptyState title="No live events" message="Punches will stream in here." />
          ) : (
            <Table>
              <Thead>
                <Th>Time</Th>
                <Th>Device user</Th>
                <Th>Matched employee</Th>
                <Th>Verify</Th>
                <Th>Work code</Th>
                <Th>Processed</Th>
              </Thead>
              <Tbody>
                {live.data.map((ev) => (
                  <Tr key={ev.id}>
                    <Td className="text-xs">{formatTime(ev.event_time)}</Td>
                    <Td className="text-xs font-mono">{ev.device_user_id}</Td>
                    <Td className="text-sm text-white">
                      {ev.employee_id ? nameOf(ev.employee_id) : "unmatched"}
                    </Td>
                    <Td className="text-xs">
                      {ev.verify_type ?? "—"}
                      {ev.temperature ? ` · ${ev.temperature}°` : ""}
                    </Td>
                    <Td className="text-xs">{ev.work_code ?? "—"}</Td>
                    <Td>
                      <Badge variant={ev.processed ? "success" : "warning"}>
                        {ev.processed ? "processed" : "pending"}
                      </Badge>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </div>
      )}

      {/* Manual punch */}
      <Modal
        open={punchOpen}
        onClose={() => setPunchOpen(false)}
        title="Manual punch"
        description="Requires approval before it affects records"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setPunchOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={
                createPunch.isPending ||
                !punch.employee_id ||
                !punch.requested_time
              }
              onClick={() => createPunch.mutate()}
            >
              {createPunch.isPending ? "Submitting…" : "Submit"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="Employee" required>
            <select
              className="input"
              value={punch.employee_id}
              onChange={(e) => setPunch({ ...punch, employee_id: e.target.value })}
            >
              <option value="">Select employee…</option>
              {employees.data?.items.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.first_name} {e.last_name} ({e.employee_code})
                </option>
              ))}
            </select>
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Date & time" required>
              <input
                type="datetime-local"
                className="input"
                value={punch.requested_time}
                onChange={(e) => setPunch({ ...punch, requested_time: e.target.value })}
              />
            </Field>
            <Field label="Type">
              <select
                className="input"
                value={punch.punch_type}
                onChange={(e) => setPunch({ ...punch, punch_type: e.target.value })}
              >
                <option value="in">Clock in</option>
                <option value="out">Clock out</option>
              </select>
            </Field>
          </div>
          <Field label="Reason">
            <input
              className="input"
              value={punch.reason}
              onChange={(e) => setPunch({ ...punch, reason: e.target.value })}
              placeholder="Forgot to badge in"
            />
          </Field>
        </div>
      </Modal>

      {/* Reject punch request */}
      <Modal
        open={!!rejectTarget}
        onClose={() => setRejectTarget(null)}
        title="Reject punch request"
        description={
          rejectTarget
            ? `${nameOf(rejectTarget.employee_id)} · ${formatTime(rejectTarget.requested_time)}`
            : undefined
        }
        size="sm"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setRejectTarget(null)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={decidePunch.isPending || !rejectReason.trim() || !rejectTarget}
              onClick={() =>
                rejectTarget &&
                decidePunch.mutate({
                  id: rejectTarget.id,
                  approve: false,
                  reason: rejectReason.trim(),
                })
              }
            >
              {decidePunch.isPending ? "Rejecting…" : "Reject"}
            </button>
          </>
        }
      >
        <Field label="Reason" required>
          <input
            className="input"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Outside the approved overtime window"
          />
        </Field>
      </Modal>

      {/* Recalculate */}
      <Modal
        open={recalcOpen}
        onClose={() => setRecalcOpen(false)}
        title="Recalculate attendance"
        description="Re-runs the rules engine over a date range"
        size="sm"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setRecalcOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={runRecalc.isPending || !recalc.start_date || !recalc.end_date}
              onClick={() => runRecalc.mutate()}
            >
              {runRecalc.isPending ? "Queueing…" : "Run"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="From" required>
            <input
              type="date"
              className="input"
              value={recalc.start_date}
              onChange={(e) => setRecalc({ ...recalc, start_date: e.target.value })}
            />
          </Field>
          <Field label="To" required>
            <input
              type="date"
              className="input"
              value={recalc.end_date || recalc.start_date}
              onChange={(e) => setRecalc({ ...recalc, end_date: e.target.value })}
            />
          </Field>
          <p className="text-[11px] text-slate-500">
            Range: {recalc.start_date || "—"} → {recalc.end_date || recalc.start_date || "—"}
          </p>
        </div>
      </Modal>
    </Page>
  );
}
