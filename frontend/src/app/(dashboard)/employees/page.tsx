"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Upload, Search } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import { StatusBadge } from "@/components/ui/Badge";
import { EmptyState, Pagination } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { Modal } from "@/components/ui/Modal";
import { Confirm } from "@/components/ui/Confirm";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { devicesApi, employeesApi } from "@/lib/api";
import { apiErrorMessage, formatDate } from "@/lib/utils";
import type { Device, Employee, PaginatedResponse } from "@/types";

interface EmployeeForm {
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  hire_date: string;
  device_user_id: string;
}

const emptyForm: EmployeeForm = {
  employee_code: "",
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  hire_date: "",
  device_user_id: "",
};

export default function EmployeesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [form, setForm] = useState<EmployeeForm>(emptyForm);
  const [deleting, setDeleting] = useState<Employee | null>(null);
  const [pushFor, setPushFor] = useState<Employee | null>(null);
  const [deviceIds, setDeviceIds] = useState<string[]>([]);

  const employees = useQuery({
    queryKey: ["employees", query, status, page],
    queryFn: async () =>
      (
        await employeesApi.list({
          page,
          page_size: pageSize,
          search: query || undefined,
          status: status || undefined,
        })
      ).data as PaginatedResponse<Employee>,
  });

  const devices = useQuery({
    queryKey: ["devices", "all"],
    queryFn: async () => (await devicesApi.list()).data as Device[],
    enabled: !!pushFor,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["employees"] });

  const save = useMutation({
    mutationFn: () => {
      const payload = {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email || null,
        phone: form.phone || null,
        hire_date: form.hire_date || null,
        device_user_id: form.device_user_id || null,
      };
      return editing
        ? employeesApi.update(editing.id, payload)
        : employeesApi.create({ ...payload, employee_code: form.employee_code });
    },
    onSuccess: () => {
      toast("success", editing ? "Employee updated" : "Employee created");
      setFormOpen(false);
      setEditing(null);
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => employeesApi.delete(id),
    onSuccess: () => {
      toast("success", "Employee deleted");
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const push = useMutation({
    mutationFn: () =>
      employeesApi.pushToDevice(pushFor!.id, { device_ids: deviceIds, include_biometrics: true }),
    onSuccess: () => {
      toast("success", "Push to device queued");
      setPushFor(null);
      setDeviceIds([]);
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setFormOpen(true);
  };

  const openEdit = (e: Employee) => {
    setEditing(e);
    setForm({
      employee_code: e.employee_code,
      first_name: e.first_name,
      last_name: e.last_name,
      email: e.email ?? "",
      phone: e.phone ?? "",
      hire_date: e.hire_date ?? "",
      device_user_id: e.device_user_id ?? "",
    });
    setFormOpen(true);
  };

  const items = employees.data?.items ?? [];
  const canSubmit =
    form.first_name.trim() && form.last_name.trim() && (editing || form.employee_code.trim());

  return (
    <Page
      title="Employees"
      subtitle="People enrolled in this tenant"
      actions={
        <button className="btn-primary flex items-center gap-2" onClick={openCreate}>
          <Plus className="w-4 h-4" /> Add employee
        </button>
      }
    >
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <form
          className="relative"
          onSubmit={(e) => {
            e.preventDefault();
            setQuery(search.trim());
            setPage(1);
          }}
        >
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
          <input
            className="input pl-9 w-64"
            placeholder="Search name, code or email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>
        <select className="input w-44" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="terminated">Terminated</option>
          <option value="onboarding">Onboarding</option>
        </select>
      </div>

      <div className="card overflow-hidden">
        {employees.isLoading ? (
          <PageSpinner />
        ) : !items.length ? (
          <EmptyState
            title="No employees found"
            message={query || status ? "Try a different search or filter." : "Create your first employee."}
            action={
              !query && !status ? (
                <button className="btn-primary" onClick={openCreate}>
                  Add employee
                </button>
              ) : undefined
            }
          />
        ) : (
          <>
            <Table>
              <Thead>
                <Th>Employee</Th>
                <Th>Code</Th>
                <Th>Status</Th>
                <Th>Email</Th>
                <Th>Phone</Th>
                <Th>Hire date</Th>
                <Th>Device UID</Th>
                <Th className="text-right">Actions</Th>
              </Thead>
              <Tbody>
                {items.map((e) => (
                  <Tr key={e.id}>
                    <Td>
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[10px] font-bold text-white shrink-0">
                          {e.first_name?.[0]}
                          {e.last_name?.[0]}
                        </div>
                        <span className="font-medium text-white">
                          {e.first_name} {e.last_name}
                        </span>
                      </div>
                    </Td>
                    <Td className="font-mono text-xs">{e.employee_code}</Td>
                    <Td>
                      <StatusBadge status={e.status} />
                    </Td>
                    <Td className="text-xs">{e.email ?? "—"}</Td>
                    <Td className="text-xs">{e.phone ?? "—"}</Td>
                    <Td className="text-xs">{formatDate(e.hire_date)}</Td>
                    <Td className="text-xs font-mono">{e.device_user_id ?? "—"}</Td>
                    <Td>
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="btn-ghost p-1.5"
                          title="Push to device"
                          onClick={() => {
                            setPushFor(e);
                            setDeviceIds([]);
                          }}
                        >
                          <Upload className="w-3.5 h-3.5" />
                        </button>
                        <button className="btn-ghost p-1.5" title="Edit" onClick={() => openEdit(e)}>
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          className="btn-ghost p-1.5 hover:text-red-400"
                          title="Delete"
                          onClick={() => setDeleting(e)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
            <Pagination page={page} pageSize={pageSize} total={employees.data?.total ?? 0} onPageChange={setPage} />
          </>
        )}
      </div>

      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={editing ? "Edit employee" : "Add employee"}
        description={editing ? editing.employee_code : "New hire record"}
        footer={
          <>
            <button className="btn-ghost" onClick={() => setFormOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={save.isPending || !canSubmit}
              onClick={() => save.mutate()}
            >
              {save.isPending ? "Saving…" : editing ? "Save changes" : "Create employee"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          {!editing && (
            <Field label="Employee code" required>
              <input
                className="input font-mono"
                value={form.employee_code}
                onChange={(e) => setForm({ ...form, employee_code: e.target.value })}
                placeholder="EMP-001"
              />
            </Field>
          )}
          <div className="grid grid-cols-2 gap-4">
            <Field label="First name" required>
              <input
                className="input"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
            </Field>
            <Field label="Last name" required>
              <input
                className="input"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Email">
              <input
                type="email"
                className="input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </Field>
            <Field label="Phone">
              <input
                className="input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Hire date">
              <input
                type="date"
                className="input"
                value={form.hire_date}
                onChange={(e) => setForm({ ...form, hire_date: e.target.value })}
              />
            </Field>
            <Field label="Device user ID" hint="PIN used on the terminal">
              <input
                className="input font-mono"
                value={form.device_user_id}
                onChange={(e) => setForm({ ...form, device_user_id: e.target.value })}
                placeholder="1001"
              />
            </Field>
          </div>
        </div>
      </Modal>

      <Modal
        open={!!pushFor}
        onClose={() => setPushFor(null)}
        title="Push to device"
        description={pushFor ? `${pushFor.first_name} ${pushFor.last_name}` : undefined}
        footer={
          <>
            <button className="btn-ghost" onClick={() => setPushFor(null)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={!deviceIds.length || push.isPending}
              onClick={() => push.mutate()}
            >
              {push.isPending ? "Queueing…" : `Push to ${deviceIds.length} device(s)`}
            </button>
          </>
        }
      >
        {devices.isLoading ? (
          <PageSpinner />
        ) : !devices.data?.length ? (
          <EmptyState title="No devices" message="Register a device first." />
        ) : (
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {devices.data.map((d) => (
              <label
                key={d.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-[hsl(var(--border))] hover:bg-[hsl(var(--muted))] cursor-pointer"
              >
                <input
                  type="checkbox"
                  className="accent-blue-500"
                  checked={deviceIds.includes(d.id)}
                  onChange={(e) =>
                    setDeviceIds((prev) =>
                      e.target.checked ? [...prev, d.id] : prev.filter((x) => x !== d.id)
                    )
                  }
                />
                <span className="flex-1 text-sm text-slate-200">{d.name}</span>
                <StatusBadge status={d.status} />
              </label>
            ))}
          </div>
        )}
      </Modal>

      <Confirm
        open={!!deleting}
        onClose={() => setDeleting(null)}
        title="Delete employee"
        message={`Delete ${deleting?.first_name} ${deleting?.last_name}? Attendance history is retained.`}
        confirmLabel="Delete"
        danger
        onConfirm={async () => {
          if (deleting) await remove.mutateAsync(deleting.id);
        }}
      />
    </Page>
  );
}
