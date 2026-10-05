"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { Page } from "@/components/layout/Page";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageSpinner } from "@/components/ui/Spinner";
import { Modal } from "@/components/ui/Modal";
import { Confirm } from "@/components/ui/Confirm";
import { Tabs } from "@/components/ui/Tabs";
import { Field } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toaster";
import { employeesApi, shiftsApi } from "@/lib/api";
import { apiErrorMessage, formatDate } from "@/lib/utils";
import type { Employee, Holiday, PaginatedResponse, Shift } from "@/types";

interface ShiftForm {
  name: string;
  type: string;
  start_time: string;
  end_time: string;
  break_minutes: number;
  grace_minutes: number;
  overtime_threshold_minutes: number;
  cross_day: boolean;
  color: string;
}

const emptyShift: ShiftForm = {
  name: "",
  type: "fixed",
  start_time: "08:00",
  end_time: "17:00",
  break_minutes: 60,
  grace_minutes: 15,
  overtime_threshold_minutes: 480,
  cross_day: false,
  color: "#3b82f6",
};

export default function ShiftsPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("shifts");

  const [shiftOpen, setShiftOpen] = useState(false);
  const [editing, setEditing] = useState<Shift | null>(null);
  const [form, setForm] = useState<ShiftForm>(emptyShift);
  const [deleting, setDeleting] = useState<Shift | null>(null);

  const [holidayOpen, setHolidayOpen] = useState(false);
  const [holiday, setHoliday] = useState({ name: "", date: "", is_paid: true, recurring: false });
  const [deletingHoliday, setDeletingHoliday] = useState<Holiday | null>(null);

  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulk, setBulk] = useState({ shift_id: "", effective_from: "", effective_to: "", employee_ids: [] as string[] });

  const shifts = useQuery({
    queryKey: ["shifts"],
    queryFn: async () => (await shiftsApi.list()).data as Shift[],
  });

  const holidays = useQuery({
    queryKey: ["shifts", "holidays"],
    queryFn: async () => (await shiftsApi.holidays()).data as Holiday[],
    enabled: tab === "holidays",
  });

  const employees = useQuery({
    queryKey: ["employees", "map"],
    queryFn: async () =>
      (await employeesApi.list({ page: 1, page_size: 200 })).data as PaginatedResponse<Employee>,
    enabled: tab === "roster",
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["shifts"] });

  const saveShift = useMutation({
    mutationFn: () => {
      const payload = { ...form, color: form.color || null };
      return editing ? shiftsApi.update(editing.id, payload) : shiftsApi.create(payload);
    },
    onSuccess: () => {
      toast("success", editing ? "Shift updated" : "Shift created");
      setShiftOpen(false);
      setEditing(null);
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const removeShift = useMutation({
    mutationFn: (id: string) => shiftsApi.delete(id),
    onSuccess: () => {
      toast("success", "Shift deleted");
      invalidate();
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const addHoliday = useMutation({
    mutationFn: () => shiftsApi.addHoliday(holiday),
    onSuccess: () => {
      toast("success", "Holiday added");
      setHolidayOpen(false);
      setHoliday({ name: "", date: "", is_paid: true, recurring: false });
      queryClient.invalidateQueries({ queryKey: ["shifts", "holidays"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const removeHoliday = useMutation({
    mutationFn: (id: string) => shiftsApi.deleteHoliday(id),
    onSuccess: () => {
      toast("success", "Holiday removed");
      queryClient.invalidateQueries({ queryKey: ["shifts", "holidays"] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const bulkAssign = useMutation({
    mutationFn: () =>
      shiftsApi.bulkRoster({
        employee_ids: bulk.employee_ids,
        shift_id: bulk.shift_id,
        effective_from: bulk.effective_from,
        effective_to: bulk.effective_to || null,
      }),
    onSuccess: () => {
      toast("success", `Roster assigned to ${bulk.employee_ids.length} employee(s)`);
      setBulkOpen(false);
      setBulk({ shift_id: "", effective_from: "", effective_to: "", employee_ids: [] });
    },
    onError: (err) => toast("error", apiErrorMessage(err)),
  });

  const openEdit = (s: Shift) => {
    setEditing(s);
    setForm({
      name: s.name,
      type: s.type,
      start_time: s.start_time.slice(0, 5),
      end_time: s.end_time.slice(0, 5),
      break_minutes: s.break_minutes,
      grace_minutes: s.grace_minutes,
      overtime_threshold_minutes: s.overtime_threshold_minutes,
      cross_day: s.cross_day,
      color: s.color ?? "#3b82f6",
    });
    setShiftOpen(true);
  };

  return (
    <Page
      title="Shifts & Schedules"
      subtitle="Working patterns, holidays and rostering"
      actions={
        tab === "shifts" ? (
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => {
              setEditing(null);
              setForm(emptyShift);
              setShiftOpen(true);
            }}
          >
            <Plus className="w-4 h-4" /> Add shift
          </button>
        ) : tab === "holidays" ? (
          <button className="btn-primary flex items-center gap-2" onClick={() => setHolidayOpen(true)}>
            <Plus className="w-4 h-4" /> Add holiday
          </button>
        ) : (
          <button className="btn-primary flex items-center gap-2" onClick={() => setBulkOpen(true)}>
            <Plus className="w-4 h-4" /> Bulk assign
          </button>
        )
      }
    >
      <Tabs
        tabs={[
          { key: "shifts", label: "Shifts", count: shifts.data?.length },
          { key: "holidays", label: "Holidays", count: holidays.data?.length },
          { key: "roster", label: "Roster" },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "shifts" &&
        (shifts.isLoading ? (
          <PageSpinner />
        ) : !shifts.data?.length ? (
          <EmptyState title="No shifts" message="Create a shift to start rostering employees." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {shifts.data.map((s) => (
              <div key={s.id} className="card p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ background: s.color ?? "#3b82f6" }}
                    />
                    <div>
                      <h3 className="text-sm font-semibold text-white">{s.name}</h3>
                      <p className="text-[11px] text-slate-500 capitalize">{s.type}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button className="btn-ghost p-1.5" onClick={() => openEdit(s)}>
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button
                      className="btn-ghost p-1.5 hover:text-red-400"
                      onClick={() => setDeleting(s)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-[hsl(var(--muted))] px-3 py-2">
                    <p className="text-slate-500 text-[10px] uppercase">Schedule</p>
                    <p className="text-slate-200 font-medium mt-0.5">
                      {s.start_time.slice(0, 5)} – {s.end_time.slice(0, 5)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-[hsl(var(--muted))] px-3 py-2">
                    <p className="text-slate-500 text-[10px] uppercase">Break</p>
                    <p className="text-slate-200 font-medium mt-0.5">{s.break_minutes} min</p>
                  </div>
                  <div className="rounded-lg bg-[hsl(var(--muted))] px-3 py-2">
                    <p className="text-slate-500 text-[10px] uppercase">Grace</p>
                    <p className="text-slate-200 font-medium mt-0.5">{s.grace_minutes} min</p>
                  </div>
                  <div className="rounded-lg bg-[hsl(var(--muted))] px-3 py-2">
                    <p className="text-slate-500 text-[10px] uppercase">OT after</p>
                    <p className="text-slate-200 font-medium mt-0.5">
                      {Math.floor(s.overtime_threshold_minutes / 60)}h
                    </p>
                  </div>
                </div>

                {s.cross_day && (
                  <div className="mt-3">
                    <Badge variant="warning">cross-day shift</Badge>
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}

      {tab === "holidays" &&
        (holidays.isLoading ? (
          <PageSpinner />
        ) : !holidays.data?.length ? (
          <EmptyState title="No holidays" message="Add public holidays so they are excluded from accruals." />
        ) : (
          <div className="card overflow-hidden">
            <Table>
              <Thead>
                <Th>Name</Th>
                <Th>Date</Th>
                <Th>Paid</Th>
                <Th>Recurring</Th>
                <Th className="text-right">Action</Th>
              </Thead>
              <Tbody>
                {holidays.data.map((h) => (
                  <Tr key={h.id}>
                    <Td className="text-sm text-white">{h.name}</Td>
                    <Td className="text-xs">{formatDate(h.date)}</Td>
                    <Td>
                      <Badge variant={h.is_paid ? "success" : "default"}>{h.is_paid ? "paid" : "unpaid"}</Badge>
                    </Td>
                    <Td className="text-xs">{h.recurring ? "yearly" : "one-off"}</Td>
                    <Td className="text-right">
                      <button
                        className="btn-ghost p-1.5 hover:text-red-400"
                        onClick={() => setDeletingHoliday(h)}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>
        ))}

      {tab === "roster" && (
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-white mb-1">Bulk roster assignment</h2>
          <p className="text-xs text-slate-500 mb-4">
            Assign a shift to many employees for a date range in one go.
          </p>
          <button className="btn-primary" onClick={() => setBulkOpen(true)}>
            Start bulk assign
          </button>
        </div>
      )}

      {/* Shift form */}
      <Modal
        open={shiftOpen}
        onClose={() => setShiftOpen(false)}
        title={editing ? "Edit shift" : "Add shift"}
        footer={
          <>
            <button className="btn-ghost" onClick={() => setShiftOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={saveShift.isPending || !form.name.trim()}
              onClick={() => saveShift.mutate()}
            >
              {saveShift.isPending ? "Saving…" : editing ? "Save changes" : "Create shift"}
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
                placeholder="Day shift"
              />
            </Field>
            <Field label="Type">
              <select
                className="input"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="fixed">Fixed</option>
                <option value="flexible">Flexible</option>
                <option value="rotating">Rotating</option>
                <option value="split">Split</option>
              </select>
            </Field>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Field label="Start" required>
              <input
                type="time"
                className="input"
                value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
              />
            </Field>
            <Field label="End" required>
              <input
                type="time"
                className="input"
                value={form.end_time}
                onChange={(e) => setForm({ ...form, end_time: e.target.value })}
              />
            </Field>
            <Field label="Break (min)">
              <input
                type="number"
                className="input"
                value={form.break_minutes}
                onChange={(e) => setForm({ ...form, break_minutes: Number(e.target.value) })}
              />
            </Field>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Field label="Grace (min)">
              <input
                type="number"
                className="input"
                value={form.grace_minutes}
                onChange={(e) => setForm({ ...form, grace_minutes: Number(e.target.value) })}
              />
            </Field>
            <Field label="OT after (min)">
              <input
                type="number"
                className="input"
                value={form.overtime_threshold_minutes}
                onChange={(e) =>
                  setForm({ ...form, overtime_threshold_minutes: Number(e.target.value) })
                }
              />
            </Field>
            <Field label="Colour">
              <input
                type="color"
                className="input h-10 p-1"
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              className="accent-blue-500"
              checked={form.cross_day}
              onChange={(e) => setForm({ ...form, cross_day: e.target.checked })}
            />
            Crosses midnight
          </label>
        </div>
      </Modal>

      {/* Holiday form */}
      <Modal
        open={holidayOpen}
        onClose={() => setHolidayOpen(false)}
        title="Add holiday"
        size="sm"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setHolidayOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={addHoliday.isPending || !holiday.name || !holiday.date}
              onClick={() => addHoliday.mutate()}
            >
              {addHoliday.isPending ? "Saving…" : "Add"}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <Field label="Name" required>
            <input
              className="input"
              value={holiday.name}
              onChange={(e) => setHoliday({ ...holiday, name: e.target.value })}
              placeholder="Founding Day"
            />
          </Field>
          <Field label="Date" required>
            <input
              type="date"
              className="input"
              value={holiday.date}
              onChange={(e) => setHoliday({ ...holiday, date: e.target.value })}
            />
          </Field>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                className="accent-blue-500"
                checked={holiday.is_paid}
                onChange={(e) => setHoliday({ ...holiday, is_paid: e.target.checked })}
              />
              Paid holiday
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                className="accent-blue-500"
                checked={holiday.recurring}
                onChange={(e) => setHoliday({ ...holiday, recurring: e.target.checked })}
              />
              Repeat every year
            </label>
          </div>
        </div>
      </Modal>

      {/* Bulk roster */}
      <Modal
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        title="Bulk roster assignment"
        description="Select a shift, date range and employees"
        size="lg"
        footer={
          <>
            <button className="btn-ghost" onClick={() => setBulkOpen(false)}>
              Cancel
            </button>
            <button
              className="btn-primary disabled:opacity-50"
              disabled={
                bulkAssign.isPending || !bulk.shift_id || !bulk.effective_from || !bulk.employee_ids.length
              }
              onClick={() => bulkAssign.mutate()}
            >
              {bulkAssign.isPending
                ? "Assigning…"
                : `Assign ${bulk.employee_ids.length} employee(s)`}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Field label="Shift" required>
              <select
                className="input"
                value={bulk.shift_id}
                onChange={(e) => setBulk({ ...bulk, shift_id: e.target.value })}
              >
                <option value="">Select…</option>
                {shifts.data?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Effective from" required>
              <input
                type="date"
                className="input"
                value={bulk.effective_from}
                onChange={(e) => setBulk({ ...bulk, effective_from: e.target.value })}
              />
            </Field>
            <Field label="Effective to">
              <input
                type="date"
                className="input"
                value={bulk.effective_to}
                onChange={(e) => setBulk({ ...bulk, effective_to: e.target.value })}
              />
            </Field>
          </div>

          <Field label="Employees" required>
            <div className="border border-[hsl(var(--border))] rounded-lg max-h-64 overflow-y-auto divide-y divide-[hsl(var(--border))]">
              <div className="flex items-center gap-3 px-3 py-2 sticky top-0 bg-[hsl(var(--card))] border-b border-[hsl(var(--border))]">
                <input
                  type="checkbox"
                  className="accent-blue-500"
                  checked={
                    !!employees.data?.items.length &&
                    bulk.employee_ids.length === employees.data.items.length
                  }
                  onChange={(e) =>
                    setBulk({
                      ...bulk,
                      employee_ids: e.target.checked
                        ? employees.data?.items.map((x) => x.id) ?? []
                        : [],
                    })
                  }
                />
                <span className="text-xs text-slate-400">Select all</span>
              </div>
              {employees.data?.items.map((e) => (
                <label key={e.id} className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-[hsl(var(--muted))]">
                  <input
                    type="checkbox"
                    className="accent-blue-500"
                    checked={bulk.employee_ids.includes(e.id)}
                    onChange={(ev) =>
                      setBulk({
                        ...bulk,
                        employee_ids: ev.target.checked
                          ? [...bulk.employee_ids, e.id]
                          : bulk.employee_ids.filter((x) => x !== e.id),
                      })
                    }
                  />
                  <span className="text-sm text-slate-200">
                    {e.first_name} {e.last_name}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">{e.employee_code}</span>
                </label>
              ))}
            </div>
          </Field>
        </div>
      </Modal>

      <Confirm
        open={!!deleting}
        onClose={() => setDeleting(null)}
        title="Delete shift"
        message={`Delete "${deleting?.name}"? Existing rosters keep a reference to it.`}
        confirmLabel="Delete"
        danger
        onConfirm={async () => {
          if (deleting) await removeShift.mutateAsync(deleting.id);
        }}
      />

      <Confirm
        open={!!deletingHoliday}
        onClose={() => setDeletingHoliday(null)}
        title="Delete holiday"
        message={`Remove "${deletingHoliday?.name}" from the holiday calendar?`}
        confirmLabel="Delete"
        danger
        onConfirm={async () => {
          if (deletingHoliday) await removeHoliday.mutateAsync(deletingHoliday.id);
        }}
      />
    </Page>
  );
}
