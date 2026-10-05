export interface User {
  id: string;
  email: string;
  role: string;
  tenant_id: string;
  is_active: boolean;
  totp_enabled: boolean;
}

export interface Device {
  id: string;
  serial_number: string;
  name: string;
  model: string | null;
  firmware_version: string | null;
  ip_address: string | null;
  status: "online" | "offline" | "unknown" | "disabled";
  timezone: string;
  pending_sync: boolean;
  last_seen_at: string | null;
  last_sync_at: string | null;
  last_successful_sync_at: string | null;
  last_error: string | null;
  tenant_id: string;
  created_at: string;
}

export interface Employee {
  id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  status: string;
  hire_date: string | null;
  photo_url: string | null;
  device_user_id: string | null;
  department_id: string | null;
  position_id: string | null;
  area_id: string | null;
  tenant_id: string;
  created_at: string;
}

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  date: string;
  shift_id: string | null;
  first_in: string | null;
  last_out: string | null;
  total_work_minutes: number;
  late_minutes: number;
  early_leave_minutes: number;
  overtime_minutes: number;
  status: string;
  is_manual: boolean;
  calculated_at: string | null;
  notes: string | null;
}

export interface AttendanceEvent {
  id: string;
  device_id: string | null;
  device_user_id: string;
  employee_id: string | null;
  event_time: string;
  verify_type: number | null;
  verify_state: number | null;
  work_code: string | null;
  temperature: number | null;
  processed: boolean;
}

export interface Shift {
  id: string;
  name: string;
  type: string;
  start_time: string;
  end_time: string;
  break_minutes: number;
  grace_minutes: number;
  overtime_threshold_minutes: number;
  cross_day: boolean;
  color: string | null;
}

export interface LeaveType {
  id: string;
  name: string;
  accrual_rate: number;
  max_balance: number;
  carry_forward: boolean;
  requires_approval: boolean;
  paid: boolean;
  color: string | null;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  leave_type_id: string;
  start_date: string;
  end_date: string;
  days: number;
  reason: string | null;
  status: string;
  approval_level: number;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
}

export interface SyncJob {
  id: string;
  device_id: string;
  type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  records_received: number;
  records_inserted: number;
  records_duplicate: number;
  records_failed: number;
  error_message: string | null;
  created_at: string;
}

export interface HRMPushTarget {
  id: string;
  name: string;
  type: string;
  base_url: string;
  event_subscriptions: string[];
  active: boolean;
  retry_max_attempts: number;
  created_at: string;
}

export interface DashboardSummary {
  date: string;
  total_records: number;
  present: number;
  absent: number;
  late: number;
}

export interface Holiday {
  id: string;
  name: string;
  date: string;
  area_id: string | null;
  is_paid: boolean;
  recurring: boolean;
}

export interface LeaveBalance {
  id: string;
  employee_id: string;
  leave_type_id: string;
  balance: number;
  used: number;
  accrued: number;
  year: number;
}

export interface ManualPunch {
  id: string;
  employee_id: string;
  requested_time: string;
  punch_type: string;
  reason: string | null;
  status: string;
  approved_by: string | null;
  approved_at: string | null;
  rejected_reason: string | null;
  created_at: string;
}

export interface PayCode {
  id: string;
  code: string;
  name: string;
  type: string;
  rate_type: string;
  rate: number;
  taxable: boolean;
}

export interface PayrollRun {
  id: string;
  period_start: string;
  period_end: string;
  status: string;
  created_at: string;
  notes: string | null;
}

export interface PayrollItem {
  id: string;
  employee_id: string;
  pay_code_id: string;
  amount: number;
  hours: number;
  notes: string | null;
}

export interface PushJob {
  id: string;
  target_id: string;
  event_type: string;
  employee_id: string | null;
  status: string;
  attempts: number;
  error: string | null;
  next_retry_at: string | null;
  created_at: string;
}

export interface PushLog {
  id: string;
  event_type: string;
  employee_id: string | null;
  response_status: number | null;
  attempt_number: number;
  sent_at: string | null;
  duration_ms: number;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
