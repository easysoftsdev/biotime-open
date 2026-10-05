"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, RefreshCw, RotateCw, Pencil, Trash2, Terminal } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { Modal } from "@/components/ui/Modal";
import { Confirm } from "@/components/ui/Confirm";
import { Tabs } from "@/components/ui/Tabs";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { devicesApi, syncJobsApi } from "@/lib/api";
import { apiErrorMessage, timeAgo } from "@/lib/utils";
import type { Device, SyncJob } from "@/types";

interface DeviceForm {
  serial_number: string;
  name: string;
  model: string;
  timezone: string;
}

const emptyForm: DeviceForm = { serial_number: "", name: "", model: "", timezone: "UTC" };

export default function DevicesPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("devices");
  const [statusFilter, setStatusFilter] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Device | null>(null);
  const [form, setForm] = useState<DeviceForm>(emptyForm);
  const [deleting, setDeleting] = useState<Device | null>(null);
  const [commandsFor, setCommandsFor] = useState<Device | null>(null);

  const devices = useQuery({
    queryKey: ["devices", statusFilter],
    queryFn: async () =>
      (await devicesApi.list(statusFilter ? { status: statusFilter } : undefined)).data as Device[],
  });

  const jobs = useQuery({
    queryKey: ["sync-jobs"],
    queryFn: async () => (await syncJobsApi.list()).data as SyncJob[],
    enabled: tab === "sync",
  });

  const commands = useQuery({
    queryKey: ["devices", commandsFor?.id, "commands"],
    queryFn: async () => (await devicesApi.commands(commandsFor!.id)).data,
    enabled: !!commandsFor,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["devices"] });

  const save = useMutation({
    mutationFn: () => {
      const payload = {
        ...form,
        model: form.model || null,
      };
      return editing ? devicesApi.update(editing.id, payload) : devicesApi.create(payload);
    },
    onSuccess: () => {
      toast("success", editing ? "Device updated" : "Device added");
      setFormOpen(false);
      setEditing(null);
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => devicesApi.delete(id),
    onSuccess: () => {
      toast("success", "Device deleted");
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const action = useMutation({
    mutationFn: ({ id, kind }: { id: string; kind: "sync" | "reboot" }) =>
      kind === "sync" ? devicesApi.sync(id) : devicesApi.reboot(id),
    onSuccess: (_d, vars) => {
      toast("success", vars.kind === "sync" ? "Sync job created" : "Reboot command queued");
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setFormOpen(true);
  };

  const openEdit = (d: Device) => {
    setEditing(d);
    setForm({
      serial_number: d.serial_number,
      name: d.name,
      model: d.model ?? "",
      timezone: d.timezone,
    });
    setFormOpen(true);
  };

  return (
    <Page
      title="Devices"
      subtitle="ZKTeco terminals connected to this tenant"
      actions={
        <button className="btn-primary flex items-center gap-2" onClick={openCreate}>
          <Plus className="w-4 h-4" /> Add device
        </button>
      }
    >
      <Tabs
        tabs={[
          { key: "devices", label: "Devices", count: devices.data?.length },
          { key: "sync", label: "Sync jobs", count: jobs.data?.length },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "devices" ? (
        <>
          <div className="flex items-center gap-2 mb-4">
            <select
              className="input w-44"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All statuses</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
              <option value="unknown">Unknown</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>

          <div className="card overflow-hidden">
            {devices.isLoading ? (
              <PageSpinner />
            ) : !devices.data?.length ? (
              <EmptyState
                title="No devices"
                message="Register your first terminal by serial number to start syncing punches."
                action={
                  <button className="btn-primary" onClick={openCreate}>
                    Add device
                  </button>
                }
              />
            ) : (
              <Table>
                <Thead>
                  <Th>Device</Th>
                  <Th>Serial</Th>
                  <Th>Status</Th>
                  <Th>IP</Th>
                  <Th>Model</Th>
                  <Th>Last seen</Th>
                  <Th className="text-right">Actions</Th>
                </Thead>
                <Tbody>
                  {devices.data.map((d) => (
                    <Tr key={d.id}>
                      <Td>
                        <p className="font-medium text-white">{d.name}</p>
                        {d.last_error && (
                          <p className="text-[11px] text-red-400 max-w-56 truncate">{d.last_error}</p>
                        )}
                      </Td>
                      <Td className="font-mono text-xs">{d.serial_number}</Td>
                      <Td>
                        <StatusBadge status={d.status} />
                      </Td>
                      <Td className="text-xs">{d.ip_address ?? "—"}</Td>
                      <Td className="text-xs">{d.model ?? "—"}</Td>
                      <Td className="text-xs">{timeAgo(d.last_seen_at)}</Td>
                      <Td>
                        <div className="flex items-center justify-end gap-1">
                          <button
                            className="btn-ghost p-1.5"
                            title="Sync now"
                            onClick={() => action.mutate({ id: d.id, kind: "sync" })}
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                          </button>
                          <button
                            className="btn-ghost p-1.5"
                            title="Reboot"
                            onClick={() => action.mutate({ id: d.id, kind: "reboot" })}
                          >
                            <RotateCw className="w-3.5 h-3.5" />
                          </button>
                          <button
                            className="btn-ghost p-1.5"
                            title="Pending commands"
                            onClick={() => setCommandsFor(d)}
                          >
                            <Terminal className="w-3.5 h-3.5" />
                          </button>
                          <button className="btn-ghost p-1.5" title="Edit" onClick={() => openEdit(d)}>
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            className="btn-ghost p-1.5 hover:text-red-400"
                            title="Delete"
                            onClick={() => setDeleting(d)}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </div>
        </>
      ) : (
        <div className="card overflow-hidden">
          {jobs.isLoading ? (
            <PageSpinner />
          ) : !jobs.data?.length ? (
            <EmptyState title="No sync jobs" message="Jobs appear here when a device sync is triggered." />
          ) : (
            <Table>
              <Thead>
                <Th>Job</Th>
                <Th>Type</Th>
                <Th>Status</Th>
                <Th>Received</Th>
                <Th>Inserted</Th>
                <Th>Duplicate</Th>
                <Th>Failed</Th>
                <Th>Started</Th>
                <Th className="text-right">Action</Th>
              </Thead>
              <Tbody>
                {jobs.data.map((j) => (
                  <Tr key={j.id}>
                    <Td className="font-mono text-xs">{j.id.slice(0, 8)}</Td>
                    <Td className="text-xs">{j.type}</Td>
                    <Td>
                      <StatusBadge status={j.status} />
                    </Td>
                    <Td className="text-xs">{j.records_received}</Td>
                    <Td className="text-xs">{j.records_inserted}</Td>
                    <Td className="text-xs">{j.records_duplicate}</Td>
                    <Td className="text-xs">{j.records_failed}</Td>
                    <Td className="text-xs">{timeAgo(j.started_at ?? j.created_at)}</Td>
                    <Td className="text-right">
                      {j.status === "failed" && (
                        <button
                          className="btn-ghost text-xs"
                          onClick={() =>
                            syncJobsApi
                              .retry(j.id)
                              .then(() => {
                                toast("success", "Sync job re-queued");
                                queryClient.invalidateQueries({ queryKey: ["sync-jobs"] });
                              })
                              .catch((e) => toast("error", apiErrorMessage(e)))
                          }
                        >
                          Retry
                        </button>
                      )}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </div>
      )}

      {/* Create / edit */}
      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={editing ? "Edit device" : "Add device"}
        description={editing ? editing.serial_number : "Register a new terminal"}
        footer={
          <>
            <button className="btn-ghost" onClick={() => setFormOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={save.isPending}
              onClick={() => save.mutate()}
            >
              {save.isPending ? "Saving…" : editing ? "Save changes" : "Add device"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          {!editing && (
            <Field label="Serial number" required hint="Found on the device label or ADMS settings">
              <input
                className="input font-mono"
                value={form.serial_number}
                onChange={(e) => setForm({ ...form, serial_number: e.target.value })}
                placeholder="X1234567890101"
              />
            </Field>
          )}
          <Field label="Name" required>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Main entrance"
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Model">
              <input
                className="input"
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                placeholder="iClock 8800"
                disabled={!!editing}
              />
            </Field>
            <Field label="Timezone">
              <input
                className="input"
                value={form.timezone}
                onChange={(e) => setForm({ ...form, timezone: e.target.value })}
                placeholder="Asia/Manila"
              />
            </Field>
          </div>
        </div>
      </Modal>

      {/* Commands */}
      <Modal
        open={!!commandsFor}
        onClose={() => setCommandsFor(null)}
        title="Pending commands"
        description={commandsFor?.name}
        size="lg"
      >
        {commands.isLoading ? (
          <PageSpinner />
        ) : !commands.data?.length ? (
          <EmptyState title="No pending commands" message="Queued commands will show up here." />
        ) : (
          <Table>
            <Thead>
              <Th>Command</Th>
              <Th>Status</Th>
              <Th>Attempts</Th>
              <Th>Scheduled</Th>
              <Th>Error</Th>
            </Thead>
            <Tbody>
              {commands.data.map((c: { id: string; command_type: string; status: string; attempts: number; scheduled_at: string | null; error: string | null }) => (
                <Tr key={c.id}>
                  <Td className="text-xs font-mono">{c.command_type}</Td>
                  <Td>
                    <StatusBadge status={c.status} />
                  </Td>
                  <Td className="text-xs">{c.attempts}</Td>
                  <Td className="text-xs">{timeAgo(c.scheduled_at)}</Td>
                  <Td className="text-xs text-red-400">{c.error ?? "—"}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Modal>

      <Confirm
        open={!!deleting}
        onClose={() => setDeleting(null)}
        title="Delete device"
        message={`Delete "${deleting?.name}"? Historical punches are kept, but the device can no longer sync.`}
        confirmLabel="Delete"
        danger
        onConfirm={async () => {
          if (deleting) await remove.mutateAsync(deleting.id);
        }}
      />
    </Page>
  );
}
