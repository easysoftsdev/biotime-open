# Help & Troubleshooting

Quick answers to the questions people ask most, then a symptom → fix table.

**Contents**

1. [Which IP do I enter: the device's or mine?](#1-which-ip-do-i-enter-the-devices-or-mine)
2. [What happens if the connection drops?](#2-what-happens-if-the-connection-drops)
3. [Can I pull a whole month of data on demand?](#3-can-i-pull-a-whole-month-of-data-on-demand)
4. [Why is my device offline or not sending punches?](#4-why-is-my-device-offline-or-not-sending-punches)
5. [Symptom to fix table](#5-symptom-to-fix-table)
6. [Background jobs that run by themselves](#6-background-jobs-that-run-by-themselves)
7. [Known limitations of this build](#7-known-limitations-of-this-build)
8. [Getting help](#8-getting-help)

---

## 1. Which IP do I enter: the device's or mine?

**Yours.** The app never dials the terminal. BioTime speaks ZKTeco **ADMS/PUSH**,
which is *device-initiated*: the terminal connects out to the server.

| Where | What you enter |
|---|---|
| On the terminal (`Menu → Communication → ADMS`) | **Your server's** address and path |
| In the dashboard (`Devices → Add device`) | Serial number, name, timezone — **no IP field** |

Device side:

```text
Server Address:  http://YOUR_SERVER_IP:8000     (or https://your.domain via nginx)
Server Path:     /iclock/
Transfer interval: 1 minute
```

The serial number is the device's identity — grab it from `Menu → About` or the
sticker on the box. An unknown serial is **auto-registered** on first handshake
(`backend/devices/adms/handler.py` → `handle_handshake`), so registering in the
UI first is optional; it only lets you set a friendly name, timezone and area.

> **Note**
> `Device.ip_address` exists in the database but nothing requires it — it is
> display-only metadata (it will read "—"). It would only matter for the legacy
> TCP protocol, where the server connects *to* the device; that adapter is not
> part of this build.

Endpoints the terminal calls, all under the API host:

| Purpose | Request | Interval |
|---|---|---|
| Handshake / config | `GET /iclock/cdata?SN=…` | on connect |
| Attendance upload | `POST /iclock/cdata?SN=…&table=ATTLOG` | ~1 min |
| Poll queued commands | `GET /iclock/getrequest?SN=…` | ~30–60 s |
| Heartbeat | `GET /iclock/ping?SN=…` | ~30–60 s |
| Command ack | `POST /iclock/devicecmd?SN=…` | when a command runs |

**Connectivity test** (run from a machine on the same network as the device):

```bash
curl "http://YOUR_SERVER_IP:8000/iclock/cdata?SN=TEST001&V=1&F=1"
```

Expected: `GET OPTION FROM:TEST001` followed by `ATTLOGStamp=…` lines.
If that works from a machine that can reach the device's network, the terminal
will connect too.

---

## 2. What happens if the connection drops?

Nothing is lost. The terminal is the buffer:

- Punches keep being stored **on the device** while it is offline.
- On reconnect the handshake answers `ATTLOGStamp=None` with `Realtime=1`, which
  tells the device *"send your whole ATTLOG again"* — including every punch made
  during the outage.
- Every incoming event is de-duplicated by fingerprint
  `sha256(serial:uid:timestamp)` with `ON CONFLICT DO NOTHING`
  (`backend/devices/adms/handler.py` → `_save_raw_event`), so re-sending days or
  a full month is idempotent: **no duplicates, no gaps**.

So recovery is automatic — bring the link back and wait for the next transfer
interval.

---

## 3. Can I pull a whole month of data on demand?

Two different things are often mixed up here:

| You want | How |
|---|---|
| Read a month **already on the server** | `Attendance` page → set *From / To*, or `GET /api/v1/attendance?start_date=2026-09-01&end_date=2026-09-30` |
| Make the **device re-send** everything it holds | Happens by itself on reconnect (section 2); there is no separate button needed |
| Export it as a file | `Reports → Attendance report` → background job → Excel (`.xlsx`) stored in the `reports` bucket in MinIO |
| Payroll period export | `Payroll → WPS report` (per run) |

> **Note**
> The **Sync** button on the Devices page currently only records a *sync job*
> row (visible under `Devices → Sync jobs`). It does not yet queue a command on
> the terminal — the automatic full re-upload on reconnect is what actually
> backfills data. See [Known limitations](#7-known-limitations-of-this-build).

---

## 4. Why is my device offline or not sending punches?

Work through this checklist in order:

1. **Reachability** — run the `curl` from section 1. No answer → firewall,
   reverse proxy or wrong IP/hostname is the problem.
2. **Correct port and path** — default API port is `8000`, path is `/iclock/`
   (with the trailing slash on most firmwares). Behind nginx, use port 80/443
   and confirm the proxy forwards to the API container.
3. **Serial match** — `Devices` page shows the terminal's serial. If it never
   appears, the device is not reaching the API at all (see 1–2).
4. **Status / last seen** — `Devices` → status column. Still `offline` after
   ~5 minutes of no contact → the device stopped dialing (check the terminal's
   own `Comm` settings and whether it lost its network).
5. **Test punch** — make a punch on the terminal, then check
   `Attendance → Live feed` within a minute.
   - Appears in *Live feed* but not in *Records*: attendance processing did not
     run → make sure the **worker** service is up (section 6).
   - Does not appear anywhere: the device is not uploading (step 1–4).
6. **Employee mapping** — punches only match an employee if the terminal user's
   PIN equals the employee's **Device user ID** (`Employees → Add/Edit` →
   *Device user ID*). Push employees to the terminal with
   `Employees → Push to device`.

---

## 5. Symptom to fix table

| Symptom | Likely cause | Fix |
|---|---|---|
| Device never appears in the dashboard | Terminal can't reach the server | Section 4, steps 1–2 (`curl` test, firewall, port/path) |
| Device online, no punches | Employee PIN ≠ *Device user ID*, or nothing to push yet | Set Device user ID, `Push to device`, punch again |
| Punches in *Live feed* but daily records stay empty | Celery worker not running | `docker compose up -d worker`, then *Attendance → Recalculate attendance* for the range |
| `401 Unauthorized` | Access token expired | Sign out/in; refresh token is used automatically (`POST /auth/refresh`) |
| `422` on a request | Missing/malformed field in the payload | Check the field the endpoint expects (`GET /openapi.json`) |
| CORS error in the browser | Frontend origin missing from `CORS_ORIGINS`, or API not restarted after the change | `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` in `.env`, then `docker compose restart api` |
| API container restart-loops on start | Settings parsing error at boot | Current code accepts comma-separated values; update to the latest `backend/core/config.py` and check `docker compose logs api` |
| Login shows "Enter your 2FA code" | TOTP enabled on the account | Type the 6-digit code from your authenticator app |
| Manual punch saved but records unchanged | Manual punches require approval | API: `PUT /api/v1/attendance/manual-punch/{id}/approve` (no UI button yet) |
| Reports / WPS "started" but no file | Background worker not running | `docker compose up -d worker beat`; the Excel lands in the MinIO `reports` bucket |
| Leave never accrues / attendance not recalculated at night | `beat` scheduler down | `docker compose up -d beat` (schedules are in `backend/core/celery_app.py`) |

---

## 6. Background jobs that run by themselves

| Job | Schedule | Task |
|---|---|---|
| Device health check | every 60 s | online/offline status |
| Failed sync retry | every 5 min | retries stuck sync jobs |
| Failed HRM push retry | every 5 min | retries failed deliveries |
| Attendance recalculation | nightly 01:00 | re-runs daily records |
| Leave accrual | daily 00:05 | adds monthly balances |
| On-demand processing | on each upload | `process_raw_events` after every `POST /iclock/cdata` |

If none of these are firing, the `worker` and `beat` services are probably not
running: `docker compose ps`.

---

## 7. Known limitations of this build

Documented so you don't waste time hunting for a feature that isn't wired yet:

- **Sync button** records a job row but does not queue a terminal command;
  automatic full re-upload on reconnect is the real backfill mechanism.
- **Manual punch approval** is API-only (`PUT …/manual-punch/{id}/approve`) —
  there is no approve button in the UI.
- **Raw device events** (`device_attendance_events`) are stored, but only the
  live feed is exposed; there is no browse/export endpoint for the raw log yet.
- **Roles** (`super_admin`, `hr_admin`, `manager`, `employee`) exist in the
  schema, but endpoints currently only require authentication — any signed-in
  user can call any endpoint.
- **Reports** show the task id when generation starts; the download link for the
  generated Excel is not surfaced in the UI yet (retrieve it from MinIO).

---

## 8. Getting help

Attach these and the answer is usually immediate:

```bash
docker compose ps                       # what is running
docker compose logs --tail=200 api      # API log
docker compose logs --tail=200 worker   # background jobs
curl -i "http://YOUR_SERVER_IP:8000/iclock/cdata?SN=TEST001&V=1&F=1"
```

Also useful: device model + firmware, serial number, whether it is on the same
LAN or over the internet, and the exact time a test punch was made.

---

**Next:** the step-by-step walkthrough lives in the [User Guide](user-guide.md).
