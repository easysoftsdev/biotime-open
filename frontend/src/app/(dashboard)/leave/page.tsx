"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Check, X, Pencil, Trash2 } from "lucide-react";
import { format } from "date-fns";
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
import { employeesApi, leaveApi } from "@/lib/api";
import { apiErrorMessage, formatDate } from "@/lib/utils";
import type { Employee, LeaveBalance, LeaveRequest, LeaveType, PaginatedResponse } from "@/types";

interface TypeForm {
  name: string;
  accrual_rate: number;
  max_balance: number;
  carry_forward: boolean;
  requires_approval: boolean;
  paid: boolean;
  color: string;
}

const emptyType: TypeForm = {
  name: "",
  accrual_rate: 1.25,
  max_balance: 30,
  carry_forward: true,
  requires_approval: true,
  paid: true,
  color: "#3b82f6",
};

export default function LeavePage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("requests");
  const [statusFilter, setStatusFilter] = useState("");

  const [requestOpen, setRequestOpen] = useState(false);
  const [request, setRequest] = useState({
    employee_id: "",
    leave_type_id: "",
    start_date: "",
    end_date: "",
    reason: "",
  });

  const [typeOpen, setTypeOpen] = useState(false);
  const [editingType, setEditingType] = useState<LeaveType | null>(null);
  const [typeForm, setTypeForm] = useState<TypeForm>(emptyType);
  const [deletingType, setDeletingType] = useState<LeaveType | null>(null);

  const requests = useQuery({
    queryKey: ["leave", "requests", statusFilter],
    queryFn: async () =>
      (await leaveApi.requests(statusFilter ? { req_status: statusFilter } : undefined))
        .data as LeaveRequest[],
  });

  const types = useQuery({
    queryKey: ["leave", "types"],
    queryFn: async () => (await leaveApi.types()).data as LeaveType[],
  });

  const balances = useQuery({
    queryKey: ["leave", "balances"],
    queryFn: async () => (await leaveApi.balances()).data as LeaveBalance[],
    enabled: tab === "balances",
  });

  const employees = useQuery({
    queryKey: ["employees", "map"],
    queryFn: async () =>
      (await employeesApi.list({ page: 1, page_size: 200 })).data as PaginatedResponse<Employee>,
  });

  const nameOf = (id: string) => {
    const e = employees.data?.items.find((x) => x.id === id);
    return e ? `${e.first_name} ${e.last_name}` : id.slice(0, 8);
  };
  const typeOf = (id: string) => types.data?.find((t) => t.id === id)?.name ?? "—";

  const invalidateRequests = () =>
    queryClient.invalidateQueries({ queryKey: ["leave", "requests"] });

  const decide = useMutation({
    mutationFn: ({ id, approve, reason }: { id: string; approve: boolean; reason?: string }) =>
      leaveApi.approve(id, { approve, rejection_reason: reason ?? null }),
    onSuccess: (_d, vars) => {
      toast("success", vars.approve ? "Leave approved" : "Leave rejected");
      invalidateRequests();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const createRequest = useMutation({
    mutationFn: () => leaveApi.createRequest(request),
    onSuccess: () => {
      toast("success", "Leave request submitted");
      setRequestOpen(false);
      setRequest({ employee_id: "", leave_type_id: "", start_date: "", end_date: "", reason: "" });
      invalidateRequests();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const saveType = useMutation({
    mutationFn: () =>
      editingType ? leaveApi.updateType(editingType.id, typeForm) : leaveApi.createType(typeForm),
    onSuccess: () => {
      toast("success", editingType ? "Leave type updated" : "Leave type created");
      setTypeOpen(false);
      setEditingType(null);
      queryClient.invalidateQueries({ queryKey: ["leave", "types"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const removeType = useMutation({
    mutationFn: (id: string) => leaveApi.deleteType(id),
    onSuccess: () => {
      toast("success", "Leave type deleted");
      queryClient.invalidateQueries({ queryKey: ["leave", "types"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const pendingCount = requests.data?.filter((r) => r.status === "pending").length ?? 0;

  return (
    <Page
      title="Leave"
      subtitle="Requests, policies and balances"
      actions={
        tab === "requests" ? (
          <button className="btn-primary flex items-center gap-2" onClick={() => setRequestOpen(true)}>
            <Plus className="w-4 h-4" /> New request
          </button>
        ) : tab === "types" ? (
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => {
              setEditingType(null);
              setTypeForm(emptyType);
              setTypeOpen(true);
            }}
          >
            <Plus className="w-4 h-4" /> Add type
          </button>
        ) : undefined
      }
    >
      <Tabs
        tabs={[
          { key: "requests", label: "Requests", count: requests.data?.length },
          { key: "types", label: "Leave types", count: types.data?.length },
          { key: "balances", label: "Balances", count: balances.data?.length },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "requests" && (
        <>
          <div className="flex items-center gap-2 mb-4">
            <select
              className="input w-44"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="cancelled">Cancelled</option>
            </select>
            {pendingCount > 0 && <Badge variant="warning">{pendingCount} awaiting approval</Badge>}
          </div>

          <div className="card overflow-hidden">
            {requests.isLoading ? (
              <PageSpinner />
            ) : !requests.data?.length ? (
              <EmptyState title="No leave requests" message="Nothing matches this filter." />
            ) : (
              <Table>
                <Thead>
                  <Th>Employee</Th>
                  <Th>Type</Th>
                  <Th>Dates</Th>
                  <Th>Days</Th>
                  <Th>Reason</Th>
                  <Th>Status</Th>
                  <Th className="text-right">Actions</Th>
                </Thead>
                <Tbody>
                  {requests.data.map((r) => (
                    <Tr key={r.id}>
                      <Td className="text-sm text-white">{nameOf(r.employee_id)}</Td>
                      <Td className="text-xs">{typeOf(r.leave_type_id)}</Td>
                      <Td className="text-xs">
                        {formatDate(r.start_date)} → {formatDate(r.end_date)}
                      </Td>
                      <Td className="text-xs">{r.days}</Td>
                      <Td className="text-xs max-w-48 truncate">{r.reason ?? "—"}</Td>
                      <Td>
                        <StatusBadge status={r.status} />
                      </Td>
                      <Td>
                        <div className="flex items-center justify-end gap-1">
                          {r.status === "pending" ? (
                            <>
                              <button
                                className="btn-ghost p-1.5 text-emerald-400"
                                title="Approve"
                                onClick={() => decide.mutate({ id: r.id, approve: true })}
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                              <button
                                className="btn-ghost p-1.5 text-red-400"
                                title="Reject"
                                onClick={() =>
                                  decide.mutate({
                                    id: r.id,
                                    approve: false,
                                    reason: "Rejected from leave queue",
                                  })
                                }
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </>
                          ) : (
                            <span className="text-[11px] text-slate-500">
                              {r.approved_at ? format(new Date(r.approved_at), "dd MMM yyyy") : "—"}
                            </span>
                          )}
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </div>
        </>
      )}

      {tab === "types" &&
        (types.isLoading ? (
          <PageSpinner />
        ) : !types.data?.length ? (
          <EmptyState title="No leave types" message="Create annual, sick or unpaid leave policies." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {types.data.map((t) => (
              <div key={t.id} className="card p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ background: t.color ?? "#3b82f6" }}
                    />
                    <h3 className="text-sm font-semibold text-white">{t.name}</h3>
                  </div>
                  <div className="flex gap-1">
                    <button
                      className="btn-ghost p-1.5"
                      onClick={() => {
                        setEditingType(t);
                        setTypeForm({
                          name: t.name,
                          accrual_rate: t.accrual_rate,
                          max_balance: t.max_balance,
                          carry_forward: t.carry_forward,
                          requires_approval: t.requires_approval,
                          paid: t.paid,
                          color: t.color ?? "#3b82f6",
                        });
                        setTypeOpen(true);
                      }}
                    >
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button
                      className="btn-ghost p-1.5 hover:text-red-400"
                      onClick={() => setDeletingType(t)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-[hsl(var(--muted))] px-3 py-2">
                    <p className="text-slate-500 text-[10px] uppercase">Accrual</p>
                    <p className="text-slate-200 font-medium mt-0.5">{t.accrual_rate}/mo</p>
                  </div>
                  <div className="rounded-lg bg-[hsl(var(--muted))] px-3 py-2">
                    <p className="text-slate-500 text-[10px] uppercase">Max balance</p>
                    <p className="text-slate-200 font-medium mt-0.5">{t.max_balance}d</p>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <Badge variant={t.paid ? "success" : "default"}>{t.paid ? "paid" : "unpaid"}</Badge>
                  {t.requires_approval && <Badge variant="info">approval</Badge>}
                  {t.carry_forward && <Badge variant="warning">carry-over</Badge>}
                </div>
              </div>
            ))}
          </div>
        ))}

      {tab === "balances" &&
        (balances.isLoading ? (
          <PageSpinner />
        ) : !balances.data?.length ? (
          <EmptyState title="No balances" message="Balances appear once leave types and employees exist." />
        ) : (
          <div className="card overflow-hidden">
            <Table>
              <Thead>
                <Th>Employee</Th>
                <Th>Leave type</Th>
                <Th>Accrued</Th>
                <Th>Used</Th>
                <Th>Balance</Th>
                <Th>Year</Th>
              </Thead>
              <Tbody>
                {balances.data.map((b) => (
                  <Tr key={b.id}>
                    <Td className="text-sm text-white">{nameOf(b.employee_id)}</Td>
                    <Td className="text-xs">{typeOf(b.leave_type_id)}</Td>
                    <Td className="text-xs">{b.accrued}</Td>
                    <Td className="text-xs">{b.used}</Td>
                    <Td>
                      <span className={b.balance <= 0 ? "text-red-400 text-xs" : "text-emerald-400 text-xs"}>
                        {b.balance}
                      </span>
                    </Td>
                    <Td className="text-xs">{b.year}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>
        ))}

      {/* New request */}
      <Modal
        open={requestOpen}
        onClose={() => setRequestOpen(false)}
        title="New leave request"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setRequestOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={
                createRequest.isPending ||
                !request.employee_id ||
                !request.leave_type_id ||
                !request.start_date ||
                !request.end_date
              }
              onClick={() => createRequest.mutate()}
            >
              {createRequest.isPending ? "Submitting…" : "Submit"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="Employee" required>
            <select
              className="input"
              value={request.employee_id}
              onChange={(e) => setRequest({ ...request, employee_id: e.target.value })}
            >
              <option value="">Select…</option>
              {employees.data?.items.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.first_name} {e.last_name} ({e.employee_code})
                </option>
              ))}
            </select>
          </Field>
          <Field label="Leave type" required>
            <select
              className="input"
              value={request.leave_type_id}
              onChange={(e) => setRequest({ ...request, leave_type_id: e.target.value })}
            >
              <option value="">Select…</option>
              {types.data?.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="From" required>
              <input
                type="date"
                className="input"
                value={request.start_date}
                onChange={(e) => setRequest({ ...request, start_date: e.target.value })}
              />
            </Field>
            <Field label="To" required>
              <input
                type="date"
                className="input"
                min={request.start_date}
                value={request.end_date}
                onChange={(e) => setRequest({ ...request, end_date: e.target.value })}
              />
            </Field>
          </div>
          <Field label="Reason">
            <textarea
              className="input min-h-20"
              value={request.reason}
              onChange={(e) => setRequest({ ...request, reason: e.target.value })}
              placeholder="Family trip"
            />
          </Field>
        </div>
      </Modal>

      {/* Leave type form */}
      <Modal
        open={typeOpen}
        onClose={() => setTypeOpen(false)}
        title={editingType ? "Edit leave type" : "Add leave type"}
        footer={
          <>
            <button className="btn-ghost" onClick={() => setTypeOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={saveType.isPending || !typeForm.name.trim()}
              onClick={() => saveType.mutate()}
            >
              {saveType.isPending ? "Saving…" : editingType ? "Save changes" : "Create"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Name" required>
              <input
                className="input"
                value={typeForm.name}
                onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })}
                placeholder="Annual leave"
              />
            </Field>
            <Field label="Colour">
              <input
                type="color"
                className="input h-10 p-1"
                value={typeForm.color}
                onChange={(e) => setTypeForm({ ...typeForm, color: e.target.value })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Accrual / month">
              <input
                type="number"
                step="0.25"
                className="input"
                value={typeForm.accrual_rate}
                onChange={(e) => setTypeForm({ ...typeForm, accrual_rate: Number(e.target.value) })}
              />
            </Field>
            <Field label="Max balance (days)">
              <input
                type="number"
                className="input"
                value={typeForm.max_balance}
                onChange={(e) => setTypeForm({ ...typeForm, max_balance: Number(e.target.value) })}
              />
            </Field>
          </div>
          <div className="space-y-2">
            {(
              [
                ["paid", "Paid leave"],
                ["requires_approval", "Requires approval"],
                ["carry_forward", "Carry over to next year"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="flex items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  className="accent-blue-500"
                  checked={typeForm[key]}
                  onChange={(e) => setTypeForm({ ...typeForm, [key]: e.target.checked })}
                />
                {label}
              </label>
            ))}
          </div>
        </div>
      </Modal>

      <Confirm
        open={!!deletingType}
        onClose={() => setDeletingType(null)}
        title="Delete leave type"
        message={`Delete "${deletingType?.name}"? Balances tied to it may be affected.`}
        confirmLabel="Delete"
        danger
        onConfirm={async () => {
          if (deletingType) await removeType.mutateAsync(deletingType.id);
        }}
      />
    </Page>
  );
}
