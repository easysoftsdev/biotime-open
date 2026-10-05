"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, FileDown, ChevronRight } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { Modal } from "@/components/ui/Modal";
import { Confirm } from "@/components/ui/Confirm";
import { Tabs } from "@/components/ui/Tabs";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { employeesApi, payrollApi } from "@/lib/api";
import { apiErrorMessage, formatDate } from "@/lib/utils";
import type { Employee, PaginatedResponse, PayCode, PayrollItem, PayrollRun } from "@/types";

interface PayCodeForm {
  code: string;
  name: string;
  type: string;
  rate_type: string;
  rate: number;
  taxable: boolean;
}

const emptyPayCode: PayCodeForm = {
  code: "",
  name: "",
  type: "earning",
  rate_type: "fixed",
  rate: 0,
  taxable: true,
};

export default function PayrollPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("runs");

  const [payCodeOpen, setPayCodeOpen] = useState(false);
  const [editing, setEditing] = useState<PayCode | null>(null);
  const [payCodeForm, setPayCodeForm] = useState<PayCodeForm>(emptyPayCode);
  const [deletingPayCode, setDeletingPayCode] = useState<PayCode | null>(null);

  const [runOpen, setRunOpen] = useState(false);
  const [runForm, setRunForm] = useState({ period_start: "", period_end: "", notes: "" });
  const [selectedRun, setSelectedRun] = useState<PayrollRun | null>(null);

  const payCodes = useQuery({
    queryKey: ["payroll", "pay-codes"],
    queryFn: async () => (await payrollApi.payCodes()).data as PayCode[],
    enabled: tab === "codes" || !!selectedRun,
  });

  const runs = useQuery({
    queryKey: ["payroll", "runs"],
    queryFn: async () => (await payrollApi.runs()).data as PayrollRun[],
    enabled: tab === "runs",
  });

  const items = useQuery({
    queryKey: ["payroll", "runs", selectedRun?.id, "items"],
    queryFn: async () => (await payrollApi.items(selectedRun!.id)).data as PayrollItem[],
    enabled: !!selectedRun,
  });

  const employees = useQuery({
    queryKey: ["employees", "map"],
    queryFn: async () =>
      (await employeesApi.list({ page: 1, page_size: 200 })).data as PaginatedResponse<Employee>,
    enabled: !!selectedRun,
  });

  const nameOf = (id: string) => {
    const e = employees.data?.items.find((x) => x.id === id);
    return e ? `${e.first_name} ${e.last_name}` : id.slice(0, 8);
  };
  const codeOf = (id: string) =>
    payCodes.data?.find((c) => c.id === id)?.name ?? id.slice(0, 8);

  const savePayCode = useMutation({
    mutationFn: () =>
      editing
        ? payrollApi.updatePayCode(editing.id, payCodeForm)
        : payrollApi.createPayCode(payCodeForm),
    onSuccess: () => {
      toast("success", editing ? "Pay code updated" : "Pay code created");
      setPayCodeOpen(false);
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["payroll", "pay-codes"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const removePayCode = useMutation({
    mutationFn: (id: string) => payrollApi.deletePayCode(id),
    onSuccess: () => {
      toast("success", "Pay code deleted");
      queryClient.invalidateQueries({ queryKey: ["payroll", "pay-codes"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const createRun = useMutation({
    mutationFn: () => payrollApi.createRun(runForm),
    onSuccess: () => {
      toast("success", "Payroll run created");
      setRunOpen(false);
      setRunForm({ period_start: "", period_end: "", notes: "" });
      queryClient.invalidateQueries({ queryKey: ["payroll", "runs"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const wps = useMutation({
    mutationFn: (runId: string) => payrollApi.wpsReport(runId),
    onSuccess: () => toast("success", "WPS report generation started"),
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  return (
    <Page
      title="Payroll"
      subtitle="Pay codes, runs and WPS exports"
      actions={
        tab === "runs" ? (
          <button className="btn-primary flex items-center gap-2" onClick={() => setRunOpen(true)}>
            <Plus className="w-4 h-4" /> New run
          </button>
        ) : (
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => {
              setEditing(null);
              setPayCodeForm(emptyPayCode);
              setPayCodeOpen(true);
            }}
          >
            <Plus className="w-4 h-4" /> Add pay code
          </button>
        )
      }
    >
      <Tabs
        tabs={[
          { key: "runs", label: "Runs", count: runs.data?.length },
          { key: "codes", label: "Pay codes", count: payCodes.data?.length },
        ]}
        active={tab}
        onChange={(k) => {
          setTab(k);
          setSelectedRun(null);
        }}
      />

      {tab === "runs" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-1 space-y-3">
            {runs.isLoading ? (
              <PageSpinner />
            ) : !runs.data?.length ? (
              <div className="card">
                <EmptyState
                  title="No payroll runs"
                  message="Create a run to calculate earnings for a pay period."
                  action={
                    <button className="btn-primary" onClick={() => setRunOpen(true)}>
                      New run
                    </button>
                  }
                />
              </div>
            ) : (
              runs.data.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedRun(r)}
                  className={`w-full text-left card p-4 transition-colors ${
                    selectedRun?.id === r.id
                      ? "border-blue-500/50 bg-blue-600/10"
                      : "hover:bg-[hsl(var(--muted))]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-white">
                        {formatDate(r.period_start)} → {formatDate(r.period_end)}
                      </p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        created {formatDate(r.created_at)}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <StatusBadge status={r.status} />
                    {r.notes && (
                      <span className="text-[11px] text-slate-500 truncate">{r.notes}</span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          <div className="lg:col-span-2">
            {!selectedRun ? (
              <div className="card">
                <EmptyState
                  title="Select a run"
                  message="Pick a payroll run on the left to inspect its line items."
                />
              </div>
            ) : (
              <div className="card overflow-hidden">
                <div className="flex items-center justify-between px-5 py-4 border-b border-[hsl(var(--border))]">
                  <div>
                    <h2 className="text-sm font-semibold text-white">
                      {formatDate(selectedRun.period_start)} → {formatDate(selectedRun.period_end)}
                    </h2>
                    <p className="text-xs text-slate-500">{items.data?.length ?? 0} line items</p>
                  </div>
                  <button
                    className="btn-ghost flex items-center gap-2 text-xs"
                    onClick={() => wps.mutate(selectedRun.id)}
                    disabled={wps.isPending}
                  >
                    <FileDown className="w-3.5 h-3.5" />
                    {wps.isPending ? "Generating…" : "WPS report"}
                  </button>
                </div>
                {items.isLoading ? (
                  <PageSpinner />
                ) : !items.data?.length ? (
                  <EmptyState
                    title="No items"
                    message="This run has no calculated items yet — the payroll task may still be running."
                  />
                ) : (
                  <Table>
                    <Thead>
                      <Th>Employee</Th>
                      <Th>Pay code</Th>
                      <Th>Hours</Th>
                      <Th>Amount</Th>
                      <Th>Notes</Th>
                    </Thead>
                    <Tbody>
                      {items.data.map((it) => (
                        <Tr key={it.id}>
                          <Td className="text-sm text-white">{nameOf(it.employee_id)}</Td>
                          <Td className="text-xs">{codeOf(it.pay_code_id)}</Td>
                          <Td className="text-xs">{it.hours}</Td>
                          <Td className="text-xs font-medium text-emerald-400">
                            {it.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </Td>
                          <Td className="text-xs text-slate-500">{it.notes ?? "—"}</Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "codes" &&
        (payCodes.isLoading ? (
          <PageSpinner />
        ) : !payCodes.data?.length ? (
          <div className="card">
            <EmptyState
              title="No pay codes"
              message="Define earnings and deductions used by payroll runs."
            />
          </div>
        ) : (
          <div className="card overflow-hidden">
            <Table>
              <Thead>
                <Th>Code</Th>
                <Th>Name</Th>
                <Th>Type</Th>
                <Th>Rate basis</Th>
                <Th>Rate</Th>
                <Th>Taxable</Th>
                <Th className="text-right">Actions</Th>
              </Thead>
              <Tbody>
                {payCodes.data.map((c) => (
                  <Tr key={c.id}>
                    <Td className="font-mono text-xs">{c.code}</Td>
                    <Td className="text-sm text-white">{c.name}</Td>
                    <Td>
                      <Badge variant={c.type === "earning" ? "success" : "danger"}>{c.type}</Badge>
                    </Td>
                    <Td className="text-xs">{c.rate_type}</Td>
                    <Td className="text-xs">{c.rate}</Td>
                    <Td className="text-xs">{c.taxable ? "yes" : "no"}</Td>
                    <Td>
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="btn-ghost p-1.5"
                          onClick={() => {
                            setEditing(c);
                            setPayCodeForm({
                              code: c.code,
                              name: c.name,
                              type: c.type,
                              rate_type: c.rate_type,
                              rate: c.rate,
                              taxable: c.taxable,
                            });
                            setPayCodeOpen(true);
                          }}
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          className="btn-ghost p-1.5 hover:text-red-400"
                          onClick={() => setDeletingPayCode(c)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>
        ))}

      {/* Pay code form */}
      <Modal
        open={payCodeOpen}
        onClose={() => setPayCodeOpen(false)}
        title={editing ? "Edit pay code" : "Add pay code"}
        footer={
          <>
            <button className="btn-ghost" onClick={() => setPayCodeOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={
                savePayCode.isPending || !payCodeForm.code.trim() || !payCodeForm.name.trim()
              }
              onClick={() => savePayCode.mutate()}
            >
              {savePayCode.isPending ? "Saving…" : editing ? "Save changes" : "Create"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Code" required>
              <input
                className="input font-mono"
                value={payCodeForm.code}
                onChange={(e) => setPayCodeForm({ ...payCodeForm, code: e.target.value })}
                placeholder="BASIC"
              />
            </Field>
            <Field label="Name" required>
              <input
                className="input"
                value={payCodeForm.name}
                onChange={(e) => setPayCodeForm({ ...payCodeForm, name: e.target.value })}
                placeholder="Basic pay"
              />
            </Field>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Field label="Type">
              <select
                className="input"
                value={payCodeForm.type}
                onChange={(e) => setPayCodeForm({ ...payCodeForm, type: e.target.value })}
              >
                <option value="earning">Earning</option>
                <option value="deduction">Deduction</option>
              </select>
            </Field>
            <Field label="Rate basis">
              <select
                className="input"
                value={payCodeForm.rate_type}
                onChange={(e) => setPayCodeForm({ ...payCodeForm, rate_type: e.target.value })}
              >
                <option value="fixed">Fixed</option>
                <option value="hourly">Hourly</option>
                <option value="percent">Percent</option>
              </select>
            </Field>
            <Field label="Rate">
              <input
                type="number"
                step="0.01"
                className="input"
                value={payCodeForm.rate}
                onChange={(e) => setPayCodeForm({ ...payCodeForm, rate: Number(e.target.value) })}
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              className="accent-blue-500"
              checked={payCodeForm.taxable}
              onChange={(e) => setPayCodeForm({ ...payCodeForm, taxable: e.target.checked })}
            />
            Subject to tax
          </label>
        </div>
      </Modal>

      {/* New run */}
      <Modal
        open={runOpen}
        onClose={() => setRunOpen(false)}
        title="New payroll run"
        size="sm"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setRunOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={
                createRun.isPending || !runForm.period_start || !runForm.period_end
              }
              onClick={() => createRun.mutate()}
            >
              {createRun.isPending ? "Creating…" : "Create run"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Period start" required>
              <input
                type="date"
                className="input"
                value={runForm.period_start}
                onChange={(e) => setRunForm({ ...runForm, period_start: e.target.value })}
              />
            </Field>
            <Field label="Period end" required>
              <input
                type="date"
                className="input"
                min={runForm.period_start}
                value={runForm.period_end}
                onChange={(e) => setRunForm({ ...runForm, period_end: e.target.value })}
              />
            </Field>
          </div>
          <Field label="Notes">
            <input
              className="input"
              value={runForm.notes}
              onChange={(e) => setRunForm({ ...runForm, notes: e.target.value })}
              placeholder="October payroll"
            />
          </Field>
        </div>
      </Modal>

      <Confirm
        open={!!deletingPayCode}
        onClose={() => setDeletingPayCode(null)}
        title="Delete pay code"
        message={`Delete "${deletingPayCode?.name}"? Existing run items keep their amounts.`}
        confirmLabel="Delete"
        danger
        onConfirm={async () => {
          if (deletingPayCode) await removePayCode.mutateAsync(deletingPayCode.id);
        }}
      />
    </Page>
  );
}
