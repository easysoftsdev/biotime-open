"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Zap, ScrollText, RotateCw } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import { StatusBadge, Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { Modal } from "@/components/ui/Modal";
import { Confirm } from "@/components/ui/Confirm";
import { Tabs } from "@/components/ui/Tabs";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { hrmPushApi } from "@/lib/api";
import { apiErrorMessage, formatDateTime, timeAgo } from "@/lib/utils";
import type { HRMPushTarget, PushJob, PushLog } from "@/types";

interface TargetForm {
  name: string;
  type: string;
  base_url: string;
  event_subscriptions: string;
  retry_max_attempts: number;
  active: boolean;
}

const emptyTarget: TargetForm = {
  name: "",
  type: "custom",
  base_url: "",
  event_subscriptions: "employee.created,employee.updated,attendance.punch",
  retry_max_attempts: 5,
  active: true,
};

const JOB_STATUSES = ["queued", "sending", "sent", "failed", "retrying", "dead"];

export default function HrmPushPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("targets");
  const [jobStatus, setJobStatus] = useState("");

  const [targetOpen, setTargetOpen] = useState(false);
  const [editing, setEditing] = useState<HRMPushTarget | null>(null);
  const [form, setForm] = useState<TargetForm>(emptyTarget);
  const [deleting, setDeleting] = useState<HRMPushTarget | null>(null);
  const [logsFor, setLogsFor] = useState<HRMPushTarget | null>(null);

  const targets = useQuery({
    queryKey: ["hrm", "targets"],
    queryFn: async () => (await hrmPushApi.targets()).data as HRMPushTarget[],
  });

  const jobs = useQuery({
    queryKey: ["hrm", "jobs", jobStatus],
    queryFn: async () =>
      (await hrmPushApi.jobs(jobStatus ? { push_status: jobStatus } : undefined)).data as PushJob[],
    enabled: tab === "jobs",
    refetchInterval: tab === "jobs" ? 15_000 : false,
  });

  const logs = useQuery({
    queryKey: ["hrm", "targets", logsFor?.id, "logs"],
    queryFn: async () => (await hrmPushApi.logs(logsFor!.id)).data as PushLog[],
    enabled: !!logsFor,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["hrm"] });

  const save = useMutation({
    mutationFn: () => {
      const payload = {
        name: form.name,
        type: form.type,
        base_url: form.base_url,
        event_subscriptions: form.event_subscriptions
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        retry_max_attempts: form.retry_max_attempts,
        active: form.active,
      };
      return editing ? hrmPushApi.updateTarget(editing.id, payload) : hrmPushApi.createTarget(payload);
    },
    onSuccess: () => {
      toast("success", editing ? "Target updated" : "Target created");
      setTargetOpen(false);
      setEditing(null);
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => hrmPushApi.deleteTarget(id),
    onSuccess: () => {
      toast("success", "Target deleted");
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const test = useMutation({
    mutationFn: (id: string) => hrmPushApi.testTarget(id),
    onSuccess: () => {
      toast("success", "Test push queued");
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const retry = useMutation({
    mutationFn: (id: string) => hrmPushApi.retryJob(id),
    onSuccess: () => {
      toast("success", "Job re-queued");
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  return (
    <Page
      title="HRM Push"
      subtitle="Outbound integrations to your HR system"
      actions={
        tab === "targets" ? (
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => {
              setEditing(null);
              setForm(emptyTarget);
              setTargetOpen(true);
            }}
          >
            <Plus className="w-4 h-4" /> Add target
          </button>
        ) : undefined
      }
    >
      <Tabs
        tabs={[
          { key: "targets", label: "Targets", count: targets.data?.length },
          { key: "jobs", label: "Jobs", count: jobs.data?.length },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "targets" &&
        (targets.isLoading ? (
          <PageSpinner />
        ) : !targets.data?.length ? (
          <EmptyState
            title="No push targets"
            message="Connect an HRM system (Odoo, SAP, custom webhook) to stream employee and attendance events."
            action={
              <button
                className="btn-primary"
                onClick={() => {
                  setEditing(null);
                  setForm(emptyTarget);
                  setTargetOpen(true);
                }}
              >
                Add target
              </button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {targets.data.map((t) => (
              <div key={t.id} className="card p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-white truncate">{t.name}</h3>
                      <Badge variant="info">{t.type}</Badge>
                      <StatusBadge status={t.active ? "online" : "offline"} label={t.active ? "active" : "paused"} />
                    </div>
                    <p className="text-[11px] text-slate-500 font-mono truncate mt-1">{t.base_url}</p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button
                      className="btn-ghost p-1.5"
                      title="Send test event"
                      onClick={() => test.mutate(t.id)}
                    >
                      <Zap className="w-3.5 h-3.5" />
                    </button>
                    <button
                      className="btn-ghost p-1.5"
                      title="Delivery logs"
                      onClick={() => setLogsFor(t)}
                    >
                      <ScrollText className="w-3.5 h-3.5" />
                    </button>
                    <button
                      className="btn-ghost p-1.5"
                      title="Edit"
                      onClick={() => {
                        setEditing(t);
                        setForm({
                          name: t.name,
                          type: t.type,
                          base_url: t.base_url,
                          event_subscriptions: t.event_subscriptions.join(", "),
                          retry_max_attempts: t.retry_max_attempts,
                          active: t.active,
                        });
                        setTargetOpen(true);
                      }}
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button
                      className="btn-ghost p-1.5 hover:text-red-400"
                      title="Delete"
                      onClick={() => setDeleting(t)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  {t.event_subscriptions.length ? (
                    t.event_subscriptions.map((s) => (
                      <span
                        key={s}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-[hsl(var(--muted))] text-slate-400 font-mono"
                      >
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px] text-slate-500">No subscriptions</span>
                  )}
                </div>

                <div className="mt-4 flex items-center justify-between text-[11px] text-slate-500">
                  <span>{t.retry_max_attempts} retry attempts</span>
                  <span>added {timeAgo(t.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        ))}

      {tab === "jobs" && (
        <>
          <div className="flex items-center gap-2 mb-4">
            <select
              className="input w-44"
              value={jobStatus}
              onChange={(e) => setJobStatus(e.target.value)}
            >
              <option value="">All statuses</option>
              {JOB_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="card overflow-hidden">
            {jobs.isLoading ? (
              <PageSpinner />
            ) : !jobs.data?.length ? (
              <EmptyState title="No push jobs" message="Events appear here as they are queued for delivery." />
            ) : (
              <Table>
                <Thead>
                  <Th>Event</Th>
                  <Th>Target</Th>
                  <Th>Status</Th>
                  <Th>Attempts</Th>
                  <Th>Error</Th>
                  <Th>Next retry</Th>
                  <Th>Created</Th>
                  <Th className="text-right">Action</Th>
                </Thead>
                <Tbody>
                  {jobs.data.map((j) => (
                    <Tr key={j.id}>
                      <Td className="text-xs font-mono">{j.event_type}</Td>
                      <Td className="text-xs font-mono">{j.target_id.slice(0, 8)}</Td>
                      <Td>
                        <StatusBadge status={j.status} />
                      </Td>
                      <Td className="text-xs">{j.attempts}</Td>
                      <Td className="text-xs text-red-400 max-w-48 truncate">{j.error ?? "—"}</Td>
                      <Td className="text-xs">{j.next_retry_at ? timeAgo(j.next_retry_at) : "—"}</Td>
                      <Td className="text-xs">{timeAgo(j.created_at)}</Td>
                      <Td className="text-right">
                        {(j.status === "failed" || j.status === "dead") && (
                          <button
                            className="btn-ghost p-1.5"
                            title="Retry"
                            onClick={() => retry.mutate(j.id)}
                          >
                            <RotateCw className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </div>
        </>
      )}

      {/* Target form */}
      <Modal
        open={targetOpen}
        onClose={() => setTargetOpen(false)}
        title={editing ? "Edit target" : "Add target"}
        description="HTTP endpoint that receives push events"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setTargetOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={save.isPending || !form.name.trim() || !form.base_url.trim()}
              onClick={() => save.mutate()}
            >
              {save.isPending ? "Saving…" : editing ? "Save changes" : "Create target"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Name" required>
              <input
                className="input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Odoo Production"
              />
            </Field>
            <Field label="Type">
              <select
                className="input"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="custom">Custom webhook</option>
                <option value="odoo">Odoo</option>
                <option value="sap">SAP SuccessFactors</option>
                <option value="oracle">Oracle HCM</option>
              </select>
            </Field>
          </div>
          <Field label="Base URL" required>
            <input
              className="input font-mono"
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="https://hrm.example.com/api/biotime"
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Subscriptions" hint="Comma-separated event names">
              <input
                className="input font-mono text-xs"
                value={form.event_subscriptions}
                onChange={(e) => setForm({ ...form, event_subscriptions: e.target.value })}
              />
            </Field>
            <Field label="Max retries">
              <input
                type="number"
                className="input"
                value={form.retry_max_attempts}
                onChange={(e) =>
                  setForm({ ...form, retry_max_attempts: Number(e.target.value) })
                }
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              className="accent-blue-500"
              checked={form.active}
              onChange={(e) => setForm({ ...form, active: e.target.checked })}
            />
            Active — receive events immediately
          </label>
        </div>
      </Modal>

      {/* Logs */}
      <Modal
        open={!!logsFor}
        onClose={() => setLogsFor(null)}
        title="Delivery logs"
        description={logsFor?.name}
        size="lg"
      >
        {logs.isLoading ? (
          <PageSpinner />
        ) : !logs.data?.length ? (
          <EmptyState title="No deliveries yet" message="Logs appear once the target receives events." />
        ) : (
          <Table>
            <Thead>
              <Th>Sent</Th>
              <Th>Event</Th>
              <Th>HTTP</Th>
              <Th>Attempt</Th>
              <Th>Duration</Th>
              <Th>Result</Th>
            </Thead>
            <Tbody>
              {logs.data.map((l) => (
                <Tr key={l.id}>
                  <Td className="text-xs">{l.sent_at ? formatDateTime(l.sent_at) : "—"}</Td>
                  <Td className="text-xs font-mono">{l.event_type}</Td>
                  <Td className="text-xs">{l.response_status ?? "—"}</Td>
                  <Td className="text-xs">{l.attempt_number}</Td>
                  <Td className="text-xs">{l.duration_ms}ms</Td>
                  <Td>
                    <Badge variant={l.success ? "success" : "danger"}>
                      {l.success ? "ok" : "failed"}
                    </Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Modal>

      <Confirm
        open={!!deleting}
        onClose={() => setDeleting(null)}
        title="Delete target"
        message={`Delete "${deleting?.name}"? Queued jobs for this target will fail.`}
        confirmLabel="Delete"
        danger
        onConfirm={async () => {
          if (deleting) await remove.mutateAsync(deleting.id);
        }}
      />
    </Page>
  );
}
