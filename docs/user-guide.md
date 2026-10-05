# BioTime Open — User Guide

A walkthrough of every page in the dashboard, from first login to a monthly
attendance + payroll cycle.

**Contents**

| # | Section |
|---|---|
| 1 | [Sign in for the first time](#1-sign-in-for-the-first-time) |
| 2 | [Dashboard](#2-dashboard) |
| 3 | [Devices](#3-devices) |
| 4 | [Employees](#4-employees) |
| 5 | [Attendance](#5-attendance) |
| 6 | [Shifts and Schedules](#6-shifts-and-schedules) |
| 7 | [Leave](#7-leave) |
| 8 | [Payroll](#8-payroll) |
| 9 | [HRM Push](#9-hrm-push) |
| 10 | [Reports](#10-reports) |
| 11 | [Settings](#11-settings) |
| 12 | [A typical month, end to end](#12-a-typical-month-end-to-end) |
| 13 | [Appendix: API, real-time feed, scheduled jobs](#13-appendix-api-real-time-feed-scheduled-jobs) |

---

## 1. Sign in for the first time

**Start the stack**

```bash
cp .env.example .env       # set SECRET_KEY, POSTGRES_PASSWORD, FIRST_ADMIN_EMAIL
docker compose up -d
```

Services that come up: `db`, `redis`, `minio`, `api`, `worker`, `beat`,
`frontend`, `nginx`.

**Create the first admin** (if you did not set `FIRST_ADMIN_*` in `.env`):

```bash
docker compose exec api python manage.py create-superuser
```

`python manage.py seed` loads the device-model registry and the first admin from
`FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD`.

**Open the dashboard** at `http://localhost:3000` and sign in. If 2FA is enabled
for your account you will be asked for a 6-digit code.

> **Note**
> If the login request fails with a CORS error, make sure your frontend origin is
> listed in `CORS_ORIGINS` (both `http://localhost:3000` and
> `http://127.0.0.1:3000` are shipped as defaults) and restart the API — see
> [Help & Troubleshooting](help.md#5-symptom-to-fix-table).

The sidebar carries ten sections:

```text
Dashboard · Devices · Employees · Attendance · Shifts
Leave · Payroll · HRM Push · Reports · Settings
```

---

## 2. Dashboard

The landing page answers "what is happening today".

| Widget | What it tells you |
|---|---|
| **Present / Absent / Late arrivals / Employees** | Today's headline numbers, plus "0/1 devices online" |
| **Device health** | How many terminals are online right now |
| **Pending leave** | Requests waiting for a decision — **Approve** / **Reject** inline |
| **Live punch feed** | The last punches as they arrive (updates as devices push) |

Approving from the dashboard uses the same endpoint as the Leave page
(`PUT /api/v1/leave/requests/{id}/approve`), so the two stay in sync.

---

## 3. Devices

Two tabs: **Devices** and **Sync jobs**.

### Add a device

1. Click **Add device**.
2. Fill in **Serial number** (from `Menu → About` on the terminal), **Name**,
   **Model** (optional) and **Timezone**.
3. Save. The row appears with status `unknown` until the terminal contacts the
   server.

The serial number is the identity — an unknown serial is auto-registered on
first handshake anyway, so this form is really about naming and timezone.

### Point the terminal at your server

On the device: `Menu → Communication → ADMS`

```text
Server Address:  http://YOUR_SERVER_IP:8000
Server Path:     /iclock/
Transfer interval: 1 minute
```

Then watch the row flip to **online** and make a test punch. Full checklist:
[Help — Why is my device offline?](help.md#4-why-is-my-device-offline-or-not-sending-punches).

### Row actions

| Icon / action | Effect |
|---|---|
| **Sync now** | Records a sync job (see [limitations](help.md#7-known-limitations-of-this-build)) |
| **Reboot** | Queues a reboot command; delivered on the device's next command poll |
| **Pending commands** | Shows queued + sent commands for that terminal |
| **Edit** / **Delete** | Update metadata / remove the device |

The status filter (All / Online / Offline / Unknown / Disabled) narrows the list.

---

## 4. Employees

Each employee is one row: code, name, email, phone, hire date and — crucially —
the **Device user ID**.

### Add an employee

1. **Add employee** → *Employee code* (required), *First name*, *Last name*,
   *Email*, *Phone*, *Hire date*.
2. **Device user ID** — the PIN used on the terminal.
   Set it to the same value as the PIN you will create on the device, otherwise
   punches will not match an employee.
3. Save.

### Push to device

**Push to device** queues a `CREATE_USER` command for that employee; the
terminal picks it up on its next command poll (30–60 s) and shows the user in
its list. Open *Pending commands* on the Devices page to watch it complete.

Deleting an employee removes them from the dashboard; it does not automatically
remove the PIN from every terminal.

---

## 5. Attendance

Two tabs: **Records** (processed daily rows) and **Live feed** (raw punches).

### Records

Columns: `Date · Employee · First in · Last out · Worked · Late · Overtime ·
Status`. Filter by **From / To** dates and **Status**, then page through the
results. The same data is available as
`GET /api/v1/attendance?start_date=…&end_date=…`.

### Live feed

Every incoming punch with `Time · Device user · Matched employee · Verify ·
Work code · Processed`. `pending` means the punch arrived but the daily record
has not been recalculated yet — usually the worker is busy or down.

### Manual punch

**Manual punch** opens a correction request:

```text
Employee · Date & time · Type (Clock in / Clock out) · Reason
```

It is stored as *pending approval* and only affects records once approved:

```http
PUT /api/v1/attendance/manual-punch/{request_id}/approve
```

> **Note**
> There is no approve button in the UI yet — approval is API-only.

### Recalculate attendance

**Recalculate attendance** re-runs the calculation for a date range. Use it after
importing data, changing a shift, or if *Live feed* shows punches that never
became records. A nightly recalculation also runs at 01:00 automatically.

---

## 6. Shifts and Schedules

Three tabs.

### Shifts

**Add shift** fields:

| Field | Meaning |
|---|---|
| Name | e.g. `General`, `Night` |
| Type | shift category |
| Start / End | working window |
| Break (min) | unpaid break |
| Grace (min) | minutes late before it counts as *Late* |
| OT after (min) | overtime starts after this much work (default 480 = 8 h) |
| Colour | used when visualising rosters |

Shifts can be edited (**Edit**) or removed (**Delete shift**).

### Holidays

Add a holiday with a **Date** and **Name**; edit or delete from the same tab.
Holidays are taken into account when attendance is calculated.

### Roster

**Bulk roster assignment** assigns a shift to several employees for a period:

```text
Employees (multi-select) · Shift · Effective from · Effective to
```

That is the link between the people in *Employees* and the times in *Shifts* —
without a roster row, attendance has nothing to compare punches against.

---

## 7. Leave

Three tabs: **Requests**, **Leave types**, **Balances**.

### Leave types

Define the categories first — **Name**, **Colour**, **Accrual / month** (days
added monthly) and **Max balance (days)**. Types can be edited or deleted.

### Requests

Each request shows `Employee · Type · Dates · Days · Reason · Status`. Use the
status filter to find `pending`, then **Approve** or **Reject** (rejection asks
for a reason). Balances and requests are also manageable from the dashboard.

### Balances

`Employee · Leave type · Accrued · Used · Balance · Year` — accrual runs daily
at 00:05 (`daily_accrual`).

---

## 8. Payroll

Two tabs: **Runs** and **Pay codes**.

### Pay codes

The building blocks of a run: `Code · Name · Type · Rate basis · Rate ·
Taxable`, plus free-text notes. Add, edit or delete from this tab.

### Runs

1. **New payroll run** → *Period start*, *Period end*, *Notes*. A new run starts
   as `draft`.
2. Select a run — its **items** appear as
   `Employee · Pay code · Hours · Amount · Notes`.
3. **WPS report** generates the payment file for that run
   (`GET /api/v1/payroll/wps-report?run_id=…`), processed in the background.

---

## 9. HRM Push

Outbound integration to your HR/ERP system (Odoo, SAP, or any webhook).

### Targets

**Add target**: **Name**, **Type** (`Custom webhook`, `Odoo`,
`SAP SuccessFactors`, `Oracle HCM`), **Base URL** (the endpoint that receives
events), **Subscriptions** (comma-separated event names, e.g.
`employee.created,employee.updated,attendance.punch`) and **Max retries**.

Useful actions per target:

- **Send test event** — verifies connectivity immediately
  (`POST /api/v1/hrm/targets/{id}/test`).
- **Delivery logs** — every attempt with its HTTP status.
- **Edit** / **Delete**.

### Jobs

Every queued delivery, with a status filter and a **Retry** button for failed
ones. Failed jobs are also retried automatically every 5 minutes
(`retry_failed_push_jobs`).

---

## 10. Reports

Four headline cards: **Employees**, **Devices** (with online count),
**Push jobs** (with delivered count) and **Failed deliveries**.

### Attendance report

Pick **From** / **To** and start the job. The worker builds an Excel file with

```text
Employee Code · Name · Date · First In · Last Out
Work Minutes · Late Minutes · OT Minutes · Status
```

and stores it in the MinIO `reports` bucket as
`reports/attendance_{tenant}_{start}_{end}.xlsx`. The page confirms the job id
when generation starts.

---

## 11. Settings

### Profile

Your email, role badge, `2FA on/off` badge, plus User ID, Tenant and account
status.

### Change password

**Current password**, **New password** (at least 8 characters), **Confirm new
password**. On success the session stays valid and the next sign-in uses the new
password.

### Two-factor authentication

1. Click the setup action — the page shows a **Secret key** and a
   **Provisioning URI** (scan it with Google Authenticator, Authy, 1Password…).
2. Enter the **6-digit code** to confirm.
3. From then on every sign-in asks for a code (`POST /api/v1/auth/totp/verify`).

---

## 12. A typical month, end to end

1. **One-off setup**
   - Add employees, set each *Device user ID*.
   - Add shifts → assign rosters → add holidays.
   - Register devices and point the terminals at the server.
   - **Push to device** for every employee.
   - Define leave types and pay codes.
2. **Every day**
   - Punches arrive by themselves; check the dashboard *Live feed*.
   - Approve pending leave and manual punches.
3. **Every period**
   - `Attendance → Recalculate attendance` for the range you are closing.
   - `Leave → Balances` before approving the rest of the month.
   - `Reports → Attendance report` for the range.
   - `Payroll → New payroll run` for the period → review items → **WPS report**.
   - Check `HRM Push → Jobs` for anything in `failed` and **Retry**.
4. **When something looks wrong**
   - Devices page → status / *Pending commands*.
   - [Help & Troubleshooting](help.md).

---

## 13. Appendix: API, real-time feed, scheduled jobs

### Main endpoints

Everything is under `/api/v1` (JWT in `Authorization: Bearer …`);
`GET /openapi.json` / `/docs` give the full schema.

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`, `POST /auth/change-password`, `POST /auth/totp/setup`, `POST /auth/totp/verify` |
| Devices | `GET/POST /devices`, `PATCH/DELETE /devices/{id}`, `POST /devices/{id}/sync`, `POST /devices/{id}/reboot`, `GET /devices/{id}/commands` |
| Employees | `GET/POST /employees`, `PATCH/DELETE /employees/{id}`, `POST /employees/{id}/push-to-device` |
| Attendance | `GET /attendance`, `GET /attendance/live`, `GET /attendance/summary`, `POST /attendance/manual-punch`, `PUT /attendance/manual-punch/{id}/approve`, `POST /attendance/recalculate` |
| Shifts | `GET/POST/PATCH/DELETE /shifts`, `POST /shifts/rosters`, `POST /shifts/rosters/bulk-assign`, `GET/POST/PATCH/DELETE /shifts/holidays…` |
| Leave | `GET/POST/PATCH/DELETE /leave/types`, `GET /leave/balances`, `GET/POST /leave/requests`, `PUT /leave/requests/{id}/approve` |
| Payroll | `GET/POST/PATCH/DELETE /payroll/pay-codes`, `GET/POST /payroll/runs`, `GET /payroll/runs/{id}/items`, `GET /payroll/wps-report` |
| HRM Push | `GET/POST/PATCH/DELETE /hrm/targets`, `POST /hrm/targets/{id}/test`, `GET /hrm/targets/{id}/logs`, `GET /hrm/jobs`, `POST /hrm/jobs/{id}/retry` |
| Reports | `GET /reports/attendance`, `GET /reports/device-health`, `GET /reports/hrm-push` |
| Sync | `GET /sync-jobs`, `GET /sync-jobs/{id}`, `POST /sync-jobs/{id}/retry` |
| Device protocol | `/iclock/cdata`, `/iclock/getrequest`, `/iclock/devicecmd`, `/iclock/ping` (no auth — called by terminals) |

### Real-time

| Socket | Carries |
|---|---|
| `ws://…/ws/live` | punches as they arrive |
| `ws://…/ws/devices` | device online/offline changes |

Both require the JWT (query param `?token=…`).

### Scheduled jobs

| Job | Schedule |
|---|---|
| Device health check | every 60 s |
| Failed sync retry | every 5 min |
| Failed HRM push retry | every 5 min |
| Attendance recalculation | nightly 01:00 |
| Leave accrual | daily 00:05 |
| Attendance processing | after every device upload |

### Related reading

- [Help & Troubleshooting](help.md) — connection issues, error table, known
  limitations.
- [README](../README.md) — architecture, supported devices, environment
  variables, Docker quickstart.
