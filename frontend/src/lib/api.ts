/**
 * Axios API client — auto-attaches JWT, handles 401 refresh.
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// ─── Request interceptor — attach token ───────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Response interceptor — handle 401 ───────────────────────
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Try refresh
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const resp = await axios.post(`${API_BASE}/api/v1/auth/refresh`, {
            refresh_token: refresh,
          });
          const { access_token } = resp.data;
          localStorage.setItem("access_token", access_token);
          // Retry original
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`;
            return api.request(error.config);
          }
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ─── Typed resource helpers ───────────────────────────────────
export const authApi = {
  login: (email: string, password: string, totp_code?: string) =>
    api.post("/auth/login", { email, password, totp_code }),
  me: () => api.get("/auth/me"),
  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }),
  totpSetup: () => api.post("/auth/totp/setup"),
  totpVerify: (code: string, secret?: string) =>
    api.post("/auth/totp/verify", { code, secret }),
};

export const devicesApi = {
  list:         (params?: object)          => api.get("/devices", { params }),
  get:          (id: string)               => api.get(`/devices/${id}`),
  create:       (data: object)             => api.post("/devices", data),
  update:       (id: string, data: object) => api.patch(`/devices/${id}`, data),
  delete:       (id: string)               => api.delete(`/devices/${id}`),
  sync:         (id: string)               => api.post(`/devices/${id}/sync`),
  reboot:       (id: string)               => api.post(`/devices/${id}/reboot`),
  commands:     (id: string)               => api.get(`/devices/${id}/commands`),
  capabilities: (id: string)               => api.get(`/devices/${id}/capabilities`),
};

export const employeesApi = {
  list:         (params?: object)          => api.get("/employees", { params }),
  get:          (id: string)               => api.get(`/employees/${id}`),
  create:       (data: object)             => api.post("/employees", data),
  update:       (id: string, data: object) => api.patch(`/employees/${id}`, data),
  delete:       (id: string)               => api.delete(`/employees/${id}`),
  pushToDevice: (id: string, data: object) => api.post(`/employees/${id}/push-to-device`, data),
};

export const attendanceApi = {
  list:          (params?: object)           => api.get("/attendance", { params }),
  live:          (limit?: number)            => api.get("/attendance/live", { params: { limit } }),
  summary:       (for_date?: string)         => api.get("/attendance/summary", { params: { for_date } }),
  manualPunch:   (data: object)              => api.post("/attendance/manual-punch", data),
  listManualPunches: (params?: object)       => api.get("/attendance/manual-punch", { params }),
  approvePunch:  (id: string, approve: boolean, reject_reason?: string) =>
    api.put(`/attendance/manual-punch/${id}/approve`, null, { params: { approve, reject_reason } }),
  recalculate:   (data: object)              => api.post("/attendance/recalculate", data),
};

export const shiftsApi = {
  list:        ()             => api.get("/shifts"),
  create:      (data: object) => api.post("/shifts", data),
  update:      (id: string, data: object) => api.patch(`/shifts/${id}`, data),
  delete:      (id: string)   => api.delete(`/shifts/${id}`),
  bulkRoster:  (data: object) => api.post("/shifts/rosters/bulk-assign", data),
  holidays:    ()             => api.get("/shifts/holidays"),
  addHoliday:  (data: object) => api.post("/shifts/holidays", data),
  updateHoliday: (id: string, data: object) => api.patch(`/shifts/holidays/${id}`, data),
  deleteHoliday: (id: string) => api.delete(`/shifts/holidays/${id}`),
};

export const leaveApi = {
  types:          ()             => api.get("/leave/types"),
  createType:     (data: object) => api.post("/leave/types", data),
  updateType:     (id: string, data: object) => api.patch(`/leave/types/${id}`, data),
  deleteType:     (id: string) => api.delete(`/leave/types/${id}`),
  balances:       (params?: object) => api.get("/leave/balances", { params }),
  requests:       (params?: object) => api.get("/leave/requests", { params }),
  createRequest:  (data: object) => api.post("/leave/requests", data),
  approve:        (id: string, data: object) => api.put(`/leave/requests/${id}/approve`, data),
};

export const payrollApi = {
  payCodes: ()             => api.get("/payroll/pay-codes"),
  createPayCode: (data: object) => api.post("/payroll/pay-codes", data),
  updatePayCode: (id: string, data: object) => api.patch(`/payroll/pay-codes/${id}`, data),
  deletePayCode: (id: string) => api.delete(`/payroll/pay-codes/${id}`),
  runs:     ()             => api.get("/payroll/runs"),
  createRun:(data: object) => api.post("/payroll/runs", data),
  items:    (runId: string)=> api.get(`/payroll/runs/${runId}/items`),
  wpsReport:(runId: string)=> api.get("/payroll/wps-report", { params: { run_id: runId } }),
};

export const hrmPushApi = {
  targets:      ()                          => api.get("/hrm/targets"),
  createTarget: (data: object)              => api.post("/hrm/targets", data),
  updateTarget: (id: string, data: object)  => api.patch(`/hrm/targets/${id}`, data),
  deleteTarget: (id: string)                => api.delete(`/hrm/targets/${id}`),
  testTarget:   (id: string)                => api.post(`/hrm/targets/${id}/test`),
  logs:         (id: string)                => api.get(`/hrm/targets/${id}/logs`),
  jobs:         (params?: object)           => api.get("/hrm/jobs", { params }),
  retryJob:     (id: string)                => api.post(`/hrm/jobs/${id}/retry`),
};

export const syncJobsApi = {
  list:   (params?: object) => api.get("/sync-jobs", { params }),
  get:    (id: string)      => api.get(`/sync-jobs/${id}`),
  retry:  (id: string)      => api.post(`/sync-jobs/${id}/retry`),
};

export const reportsApi = {
  attendance:  (params: object) => api.get("/reports/attendance", { params }),
  deviceHealth:()               => api.get("/reports/device-health"),
  hrmPush:     ()               => api.get("/reports/hrm-push"),
};
