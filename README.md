# BioTime Open — ZKTeco Attendance Platform

> An open-source, self-hosted alternative to ZKTeco BioTime.
> Connect any ZKTeco device, process attendance, and push data to any HRM/ERP via a unified webhook/API layer.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/UI-Next.js-black)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-336791)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED)](https://docker.com)

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [Feature Parity Checklist](#2-feature-parity-checklist)
3. [Supported ZKTeco Devices](#3-supported-zkteco-devices)
4. [HRM / ERP Integration](#4-hrm--erp-integration)
5. [High-Level Architecture](#5-high-level-architecture)
6. [Layer-by-Layer Breakdown](#6-layer-by-layer-breakdown)
7. [Device Abstraction Layer](#7-device-abstraction-layer)
8. [HRM Push Layer](#8-hrm-push-layer)
9. [End-to-End Data Flows](#9-end-to-end-data-flows)
10. [Database Schema](#10-database-schema)
11. [API Surface](#11-api-surface)
12. [Sync Engine Architecture](#12-sync-engine-architecture)
13. [Device State Machine](#13-device-state-machine)
14. [Technology Stack](#14-technology-stack)
15. [Key Architectural Principles](#15-key-architectural-principles)
16. [Quickstart (Docker Compose)](#16-quickstart-docker-compose)
17. [Environment Variables](#17-environment-variables)
18. [Project Structure](#18-project-structure)
19. [Contributing](#19-contributing)
20. [License](#20-license)

---

## 1. What Is This?

**BioTime Open** is a fully self-hosted, open-source attendance management platform that replicates and extends ZKTeco BioTime. It connects directly to ZKTeco hardware using the same ADMS/PUSH SDK protocols the devices already speak, processes attendance records, and can push that data to any external HRM, ERP, or payroll system via configurable webhooks or a built-in REST push layer.

### Why build this?

| Pain with BioTime                          | How BioTime Open solves it                          |
|--------------------------------------------|-----------------------------------------------------|
| Expensive per-seat licensing               | Free and open-source (MIT)                          |
| Cloud-only or Windows-only deployment      | Docker, self-hosted, runs anywhere                  |
| No HRM integration / locked export formats | Webhook push to any HRM with field mapping          |
| Black-box sync — no visibility             | Full sync job audit trail, live status dashboard    |
| New device model breaks compatibility      | Model registry — new device = new DB row, no code   |
| Attendance recalculation is manual         | Automatic nightly recalc with full audit trail      |
| No open API                                | Full REST API + WebSocket, OpenAPI docs included    |

---

## 2. Feature Parity Checklist

### Device Management
- [x] Auto-registration of new devices on first connect
- [x] Device health monitoring (heartbeat, last seen, online/offline state)
- [x] Firmware version tracking per device
- [x] Multi-area / multi-site device grouping
- [x] Remote device reboot and config push
- [x] Per-device timezone support
- [x] Manual sync trigger with live job status
- [x] Device-to-device employee transfer
- [x] Bulk device command dispatch
- [ ] Device firmware OTA update (planned)

### Biometric & Employee Sync
- [x] Push employees to device (create / update / delete)
- [x] Pull biometric templates from device (face, fingerprint, palm)
- [x] Server-side biometric template storage (encrypted)
- [x] Cross-device template replication
- [x] Card / RFID enrollment sync
- [x] QR code enrollment sync
- [ ] ISO/IEC 19794 template normalization (planned)

### Attendance Processing
- [x] Real-time punch ingestion via ADMS push
- [x] Offline punch recovery on device reconnect
- [x] Idempotent deduplication (event fingerprint)
- [x] Attendance record calculation (late, early leave, overtime, absent)
- [x] Configurable attendance policies per department
- [x] Manual punch entry with approval workflow
- [x] Attendance recalculation on policy change
- [x] Raw event log — immutable, always rebuildable
- [x] Work codes / verification type mapping
- [ ] Geo-fenced mobile punch (planned)

### Shift & Roster
- [x] Flexible shift definitions (fixed, flexible, open)
- [x] Shift cycles and rotation patterns
- [x] Individual and bulk roster assignment
- [x] Holiday calendar (per area, recurring)
- [x] Cross-midnight shift support

### Leave Management
- [x] Configurable leave types with accrual rules
- [x] Leave balance tracking per employee per year
- [x] Leave request and multi-level approval workflow
- [x] Carry-forward and max-balance rules
- [x] Leave impact on attendance records
- [ ] Leave accrual on custom schedules (planned)

### Payroll Integration
- [x] Pay code mapping (regular, overtime, holiday, absent)
- [x] Employee salary structure
- [x] Payroll run generation
- [x] WPS (Wages Protection System) report export
- [x] Push payroll data to HRM via webhook
- [ ] Direct bank file generation (planned)

### HRM / ERP Push (unique to BioTime Open)
- [x] Configurable webhook push per event type
- [x] Field mapping (map our fields to target HRM fields)
- [x] Push attendance records to: Odoo, SAP, Oracle HCM, Workday, custom API
- [x] Retry on failure with exponential backoff
- [x] Push audit log (every payload sent, response received)
- [x] Test push (send sample payload to target HRM)
- [x] Multi-target push (push same event to multiple HRMs)
- [ ] Native Odoo connector (planned)
- [ ] Native SAP SuccessFactors connector (planned)

### Access Control
- [x] Access groups and door assignments
- [x] Time-based access rules
- [x] Employee access assignment
- [x] Access event log

### Visitor Management
- [x] Visitor registration and pre-registration
- [x] QR-based visitor check-in
- [x] Visitor access grant to specific devices
- [x] Host employee notification on visitor arrival

### Reporting
- [x] Daily / monthly attendance summary
- [x] Late and absent reports
- [x] Overtime reports
- [x] Leave balance reports
- [x] Device health and sync status reports
- [x] Export to CSV, Excel, PDF
- [x] Scheduled report delivery via email

### System
- [x] Multi-tenant support (multiple organizations)
- [x] Role-based access control (Super Admin, HR Admin, Manager, Employee)
- [x] Full audit log on all changes
- [x] REST API with OpenAPI/Swagger docs
- [x] WebSocket real-time live punch feed
- [x] Two-factor authentication (TOTP)
- [x] SSO via OAuth2 / SAML (planned)
- [x] Docker Compose one-command deployment
- [ ] Kubernetes Helm chart (planned)

---

## 3. Supported ZKTeco Devices

All ZKTeco devices that support the **ADMS (Attendance Data Management System)** protocol are supported. This covers virtually every ZKTeco terminal released after 2015.

### SpeedFace Series (Face + Palm Recognition)

| Series         | Models                                        | Protocol       |
|----------------|-----------------------------------------------|----------------|
| V5L Series     | V5L, V5L[QR], V5L[TD], V5L[TI], V5L[QR][TI]  | ADMS + PUSH SDK |
| V4L Pro Series | V4L Pro, V4L Pro-QR, V4L Pro-RFID             | ADMS + PUSH SDK |
| V3L Series     | V3L, V3L[QR], V3L[RFID], V3L Lite            | ADMS            |
| H5L Series     | H5L, H5L[P]                                   | ADMS + PUSH SDK |
| M4             | SpeedFace-M4                                  | ADMS            |
| M1 / M2        | SpeedFace-M1, SpeedFace-M2                    | ADMS            |
| 7BL            | SpeedFace-7BL                                 | ADMS            |

### InFace Series (Face Recognition)

| Series   | Models                        | Protocol |
|----------|-------------------------------|----------|
| InFace   | InFace 600, 800, 900 Series   | ADMS     |

### ProFace Series

| Series  | Models                        | Protocol       |
|---------|-------------------------------|----------------|
| ProFace | ProFace X, ProFace X[TD]      | ADMS + PUSH SDK |

### Fingerprint Terminals

| Series       | Models                                                    | Protocol    |
|--------------|-----------------------------------------------------------|-------------|
| uFace Series | uFace 800, uFace 202, uFace 4                             | ADMS        |
| K Series     | K40, K50, K60, K80                                        | ADMS        |
| F Series     | F18, F19, F21, F22                                        | ADMS        |
| G Series     | G3, G3 Plus, G4                                           | ADMS        |
| MB Series    | MB10, MB20, MB40, MB160, MB460, MB1000                    | ADMS        |

### Access Control Panels

| Series      | Models                        | Protocol |
|-------------|-------------------------------|----------|
| C3 Series   | C3-100, C3-200, C3-400        | TCP      |
| inBio Series| inBio160, inBio260, inBio460  | TCP      |

### Legacy Devices (TCP Protocol)

| Series      | Models                          | Protocol |
|-------------|---------------------------------|----------|
| V5 Series   | SpeedFace-V5, SpeedFace-V5L     | TCP      |
| TF Series   | TF1700, TF1800                  | TCP      |

> **Don't see your device?** If it has an IP address and can be pointed at a server URL in its configuration, it almost certainly supports ADMS. Open an issue with your device model and we'll add support.

---

## 4. HRM / ERP Integration

BioTime Open includes a dedicated **HRM Push Layer** that forwards processed attendance data to any external HR system. No polling required — data is pushed as events are processed.

### How It Works

```
Attendance Record Created / Updated
            │
            ▼
    HRM Push Router
            │
    ┌───────┼───────┐
    ▼       ▼       ▼
 Odoo    SAP HR   Custom
Webhook  Webhook  Webhook
```

### Supported Push Targets

| Target           | Status      | Push Format        |
|------------------|-------------|--------------------|
| Custom REST API  | ✅ Ready    | JSON (configurable)|
| Odoo HR          | ✅ Ready    | JSON-RPC / REST    |
| SAP SuccessFactors | 🚧 Planned | OData REST         |
| Oracle HCM Cloud | 🚧 Planned | REST               |
| Workday          | 🚧 Planned | REST               |
| BambooHR         | ✅ Ready    | REST               |
| Zoho People      | ✅ Ready    | REST               |
| Darwinbox        | ✅ Ready    | REST               |
| Keka HR          | ✅ Ready    | REST               |
| greytHR          | ✅ Ready    | REST               |
| Webhook (generic)| ✅ Ready    | JSON               |

### Field Mapping

Every push target has a configurable field map. You define how your fields translate to the target HRM's fields:

```json
{
  "target": "odoo",
  "endpoint": "https://your-odoo.com/api/attendance",
  "auth": { "type": "bearer", "token": "{{env.ODOO_TOKEN}}" },
  "field_map": {
    "employee_code":  "employee_id.barcode",
    "punch_time":     "check_in",
    "punch_type":     "attendance_type",
    "device_serial":  "device_id"
  },
  "events": ["punch_in", "punch_out", "manual_punch"],
  "retry": { "max_attempts": 5, "backoff": "exponential" }
}
```

### Push Events

| Event                  | Triggered When                                  |
|------------------------|-------------------------------------------------|
| `punch_in`             | First punch of the day ingested                 |
| `punch_out`            | Last punch of the day ingested                  |
| `raw_punch`            | Every individual punch event received           |
| `attendance_calculated`| Daily attendance record finalized               |
| `manual_punch_approved`| Manual punch request approved                   |
| `leave_approved`       | Leave request approved                          |
| `payroll_run_completed`| Payroll run finalized                           |
| `employee_synced`      | Employee pushed to / pulled from device         |

### Push Audit Log

Every push attempt is logged:

```
push_log (
  id, target_id, event_type, employee_id,
  payload JSONB, response_status, response_body,
  attempt_number, sent_at, duration_ms, success
)
```

---

## 5. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                  │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Next.js Web  │  │ Mobile App   │  │ Admin Portal │  │ ESS Portal   │   │
│  │ Dashboard    │  │  (Flutter)   │  │ (RBAC)       │  │ (Employee)   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└─────────┼─────────────────┼─────────────────┼─────────────────┼───────────┘
          └─────────────────┴─────────────────┴─────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY LAYER                                 │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        FastAPI Application                           │  │
│  │                                                                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │  │
│  │  │ REST API   │  │ ADMS Server│  │ WebSocket  │  │ Auth / RBAC  │   │  │
│  │  │ /api/v1/*  │  │ /iclock/*  │  │ Real-time  │  │ JWT + OAuth2 │   │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN SERVICES LAYER                              │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    DEVICE ABSTRACTION LAYER                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │ ADMS       │  │ PUSH SDK   │  │ BEST       │  │ TCP Legacy     │  │  │
│  │  │ Adapter    │  │ Adapter    │  │ Adapter    │  │ Adapter        │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Device       │  │ Sync         │  │ Attendance   │  │ Shift &      │   │
│  │ Manager      │  │ Manager      │  │ Engine       │  │ Roster Engine│   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Leave        │  │ Payroll      │  │ Notification │  │ Report       │   │
│  │ Engine       │  │ Engine       │  │ Service      │  │ Engine       │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Access       │  │ Visitor      │  │ HRM Push     │  │ Command      │   │
│  │ Control      │  │ Management   │  │ Layer        │  │ Queue        │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
┌───────────────────────────┐   ┌───────────────────────────────────────────┐
│    MESSAGE & QUEUE LAYER  │   │           HRM PUSH TARGETS                │
│                           │   │                                           │
│    Redis + Celery         │   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│    - device queues        │   │  │ Odoo │ │ SAP  │ │Zoho  │ │ Custom   │  │
│    - hrm_push queue       │   │  │  HR  │ │  HR  │ │People│ │ REST API │  │
│    - Celery Beat schedules│   │  └──────┘ └──────┘ └──────┘ └──────────┘  │
└───────────────────────────┘   └───────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                    │
│                                                                            │
│  PostgreSQL (primary)   Redis (cache/state)   MinIO/S3 (files)            │
│  Prometheus + Grafana   Sentry (errors)                                   │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         DEVICE LAYER (ALL ZKTECO)                          │
│                                                                            │
│  SpeedFace V5L/V4L/V3L/H5L  ·  InFace  ·  ProFace  ·  uFace  ·  K/F/G   │
│  MB Series  ·  C3/inBio Access Panels  ·  Legacy TCP Devices              │
│                                                                            │
│  Protocol: ADMS/HTTP (primary)  ·  PUSH SDK  ·  TCP (legacy)              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Layer-by-Layer Breakdown

### 6.1 Client Layer

| Component     | Technology                    | Purpose                                       |
|---------------|-------------------------------|-----------------------------------------------|
| Web Dashboard | Next.js, TypeScript, Tailwind | Admin, HR, and manager views                  |
| Mobile App    | Flutter                       | Employee self-service, geofenced punch        |
| Admin Portal  | Next.js (RBAC)                | Super admin, tenant management, HR functions  |
| ESS Portal    | Next.js                       | Employee self-service (leave, punch, profile) |

### 6.2 API Gateway Layer

| Component   | Technology        | Purpose                                     |
|-------------|-------------------|---------------------------------------------|
| REST API    | FastAPI           | `/api/v1/*` for all business operations     |
| ADMS Server | FastAPI           | `/iclock/*` for ZKTeco device communication |
| WebSocket   | FastAPI WebSocket | Real-time punches and device status         |
| Auth / RBAC | JWT + OAuth2      | Authentication and authorization            |

### 6.3 Domain Services Layer

| Service                  | Responsibility                                               |
|--------------------------|--------------------------------------------------------------|
| Device Abstraction Layer | Model registry, capability resolver, protocol adapters       |
| Device Manager           | Device registration, health monitoring, command dispatch     |
| Sync Manager             | Bidirectional sync orchestration, conflict resolution        |
| Attendance Engine        | Raw event processing, record calculation, policy enforcement |
| Shift & Roster Engine    | Shift definitions, roster assignments, holiday management    |
| Leave Engine             | Leave types, balances, accrual rules, request workflows      |
| Payroll Engine           | Pay code mapping, salary computation, payroll run management |
| Notification Service     | Multi-channel notifications (push, email, SMS)               |
| Report Engine            | Report generation, scheduling, and export                    |
| Access Control           | Door groups, zone access policies, time-based rules          |
| Visitor Management       | Visitor registration, pre-registration, access granting      |
| HRM Push Layer           | Event-driven push to external HRM/ERP systems                |
| Command Queue            | Async device command queue with retry and acknowledgement    |

### 6.4 Message & Queue Layer

**Broker:** Redis + Celery

| Queue              | Worker                        |
|--------------------|-------------------------------|
| device_heartbeat   | device_sync_worker            |
| device_sync        | attendance_process_worker     |
| attendance_process | user_sync_worker              |
| user_sync          | notification_worker           |
| notification_send  | report_generation_worker      |
| report_generation  | payroll_calc_worker           |
| payroll_calc       | leave_accrual_worker          |
| leave_accrual      | hrm_push_worker               |
| hrm_push           |                               |

**Celery Beat Schedules:**

| Task                | Schedule    |
|---------------------|-------------|
| device_health_check | Every 1 min |
| auto_sync_retry     | Every 5 min |
| hrm_push_retry      | Every 5 min |
| leave_accrual       | Daily       |
| report_export       | Scheduled   |
| attendance_recalc   | Nightly     |

### 6.5 Data Layer

| Store        | Purpose                                   |
|--------------|-------------------------------------------|
| PostgreSQL   | Primary database (all domain data)        |
| Redis        | Cache, sessions, device state, job locks  |
| MinIO / S3   | Bio photos, report exports, backups       |
| Prometheus   | Metrics collection                        |
| Grafana      | Dashboards and alerting                   |
| Sentry       | Error tracking                            |

---

## 7. Device Abstraction Layer

Adding a new ZKTeco device model requires **zero code changes** — only a new row in `device_models`.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVICE ABSTRACTION LAYER                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Device Model Registry                       │    │
│  │                                                          │    │
│  │  device_models table:                                    │    │
│  │  - series: SpeedFace-V5L, V4L Pro, V3L, InFace, etc.    │    │
│  │  - model_code: V5L, V5L[QR], K40, F18, MB1000, etc.     │    │
│  │  - default_capabilities: JSONB                           │    │
│  │  - adms_supported: BOOLEAN                               │    │
│  │  - push_sdk_supported: BOOLEAN                           │    │
│  │  - tcp_supported: BOOLEAN                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Capability Resolver                         │    │
│  │                                                          │    │
│  │  Input:  serial_number + firmware_version + model hint   │    │
│  │  Output: DeviceCapabilities object                       │    │
│  │                                                          │    │
│  │  Resolution order:                                       │    │
│  │  1. Exact model_code match                               │    │
│  │  2. Firmware variant match                               │    │
│  │  3. Series base template                                 │    │
│  │  4. Flag for manual review if unknown                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Protocol Adapter Interface                  │    │
│  │                                                          │    │
│  │  handshake(device)             -> DeviceCapabilities     │    │
│  │  receive_attendance(payload)   -> list[RawEvent]         │    │
│  │  send_command(device, command) -> CommandResult          │    │
│  │  poll_commands(device)         -> list[Command]          │    │
│  │  push_user(device, user)       -> CommandResult          │    │
│  │  pull_users(device)            -> list[User]             │    │
│  │  push_template(device, tmpl)   -> CommandResult          │    │
│  │  pull_template(device, uid)    -> Template               │    │
│  │  test_connection(device)       -> ConnectionStatus       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ ADMS       │  │ PUSH SDK   │  │ BEST       │  │ TCP Legacy │  │
│  │ Adapter    │  │ Adapter    │  │ Adapter    │  │ Adapter    │  │
│  │            │  │            │  │            │  │            │  │
│  │ All modern │  │ Template   │  │ Advanced   │  │ Old devices│  │
│  │ ZKTeco     │  │ push/pull  │  │ features   │  │ C3 / inBio │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### ADMS Endpoints (what devices call)

ZKTeco devices call **your server** — you don't poll them. Point the device's server URL to your BioTime Open instance:

```
Device setting → Server Address: http://your-server:8000
Device setting → Server Path:    /iclock/
```

```http
GET  /iclock/cdata       # Device handshake — server returns config
POST /iclock/cdata       # Device pushes attendance records
GET  /iclock/getrequest  # Device polls for pending commands
POST /iclock/devicecmd   # Device acknowledges command execution
GET  /iclock/ping        # Heartbeat — device sends every 30–60s
```

---

## 8. HRM Push Layer

```
┌──────────────────────────────────────────────────────────────────┐
│                        HRM PUSH LAYER                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Push Target Registry                     │  │
│  │                                                            │  │
│  │  hrm_push_targets table:                                   │  │
│  │  - name, type (odoo/sap/zoho/custom), base_url            │  │
│  │  - auth_config JSONB (bearer/basic/apikey/oauth2)         │  │
│  │  - field_map JSONB                                         │  │
│  │  - event_subscriptions TEXT[]                             │  │
│  │  - active, retry_config JSONB                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Event Router                             │  │
│  │                                                            │  │
│  │  1. Attendance record created/updated                      │  │
│  │  2. Look up active targets subscribed to this event        │  │
│  │  3. Apply field_map to transform payload                   │  │
│  │  4. Enqueue to hrm_push queue                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Push Worker                              │  │
│  │                                                            │  │
│  │  1. Dequeue push job                                       │  │
│  │  2. Resolve auth credentials                               │  │
│  │  3. POST to target HRM endpoint                            │  │
│  │  4. Log result (push_log)                                  │  │
│  │  5. On failure: exponential backoff retry (max 5)          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Odoo │  │ SAP  │  │ Zoho │  │ BambooHR │  │ Custom REST  │  │
│  │  HR  │  │  HR  │  │People│  │          │  │     API      │  │
│  └──────┘  └──────┘  └──────┘  └──────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. End-to-End Data Flows

### 9.1 Normal Attendance Flow (Device Online)

```
ZKTeco Device (any model)
        │
        │  POST /iclock/cdata  (ADMS push)
        ▼
FastAPI ADMS Handler
        │
        ▼
Device Model Registry lookup
        │
        ▼
Capability Resolver → select Protocol Adapter
        │
        ▼
Normalize to RawEvent schema
        │
        ▼
device_attendance_events
   INSERT ... ON CONFLICT (device_id, event_fingerprint) DO NOTHING
        │
        ▼
Celery: attendance_process queue
        │
        ▼
Attendance Engine → calculate record
        │
        ▼
attendance_records (upsert)
        │
        ├──► WebSocket broadcast → Dashboard live feed
        │
        └──► HRM Push Router → enqueue to hrm_push queue
                                      │
                                      ▼
                              hrm_push_worker
                                      │
                                      ▼
                             POST to target HRM
```

### 9.2 Offline Device Recovery Flow

```
Device goes offline
        │
        ▼
Device stores records locally (internal flash)
        │
        ▼
Server: last_seen_at stops updating
        │
        ▼
Celery Beat: device_health_check (every 1 min)
   NOW() - last_seen_at > threshold → device.status = OFFLINE
        │
        ▼
Dashboard alert: OFFLINE — N records pending
        │
        ▼
Device reconnects → POST /iclock/cdata with backlog
        │
        ▼
Idempotent ingestion (event_fingerprint dedup)
   → no duplicates, no data loss
        │
        ▼
Normal attendance processing resumes
```

### 9.3 Manual Sync Flow

```
Admin: "Sync Now"
        │
        ▼
POST /api/v1/devices/{id}/sync
        │
        ▼
sync_job created (status=QUEUED)
        │
        ├── Device ONLINE  → execute immediately
        │
        └── Device OFFLINE → device_command created
                              status = WAITING_FOR_DEVICE
        │
        ▼
202 Accepted { "job_id": "..." }
        │
        ▼  (device polls every 30s)
GET /iclock/getrequest → returns SYNC_ATTENDANCE command
        │
        ▼
Device uploads stored records
        │
        ▼
Ingestion pipeline (idempotent)
        │
        ▼
sync_job → COMPLETED
```

### 9.4 Employee Push Flow

```
HR creates employee
        │
        ▼
employees table updated
        │
        ▼
Command queued: CREATE_USER (for each assigned device)
        │
        ▼
Capability check (does this device support face/card/FP?)
        │
        ▼
Device polls GET /iclock/getrequest
        │
        ▼
Device receives CREATE_USER with biometric data
        │
        ▼
Device creates user locally
        │
        ▼
POST /iclock/devicecmd → acknowledgement
        │
        ▼
device_command → COMPLETED
```

### 9.5 HRM Push Flow

```
attendance_records upserted
        │
        ▼
HRM Push Router
   find all active push targets subscribed to 'attendance_calculated'
        │
        ▼
For each target:
   apply field_map → transform payload
   enqueue to hrm_push queue
        │
        ▼
hrm_push_worker dequeues
        │
        ▼
POST {target.base_url} with mapped payload + auth headers
        │
        ├── 2xx → push_log success, done
        │
        └── 4xx/5xx/timeout
                │
                ▼
           schedule retry (exponential backoff)
           max 5 attempts → push_log failure, alert admin
```

---

## 10. Database Schema

### 10.1 Device & Sync Tables

```sql
devices (
  id UUID PRIMARY KEY,
  serial_number VARCHAR UNIQUE NOT NULL,
  name VARCHAR,
  model VARCHAR,
  firmware_version VARCHAR,
  ip_address INET,
  status VARCHAR,           -- UNKNOWN | ONLINE | OFFLINE | DISABLED
  last_seen_at TIMESTAMPTZ,
  last_sync_at TIMESTAMPTZ,
  last_successful_sync_at TIMESTAMPTZ,
  last_error_at TIMESTAMPTZ,
  last_error TEXT,
  pending_sync BOOLEAN DEFAULT FALSE,
  area_id UUID REFERENCES areas(id),
  timezone VARCHAR,
  tenant_id UUID REFERENCES tenants(id)
)

device_models (
  id UUID PRIMARY KEY,
  series VARCHAR,
  model_code VARCHAR UNIQUE,
  display_name VARCHAR,
  adms_supported BOOLEAN DEFAULT TRUE,
  push_sdk_supported BOOLEAN DEFAULT FALSE,
  tcp_supported BOOLEAN DEFAULT FALSE,
  default_capabilities JSONB
)

device_capabilities (
  id UUID PRIMARY KEY,
  device_id UUID REFERENCES devices(id),
  protocol VARCHAR,
  supports_face BOOLEAN,
  supports_fingerprint BOOLEAN,
  supports_palm BOOLEAN,
  supports_rfid BOOLEAN,
  supports_qr BOOLEAN,
  supports_temperature BOOLEAN,
  max_users INTEGER,
  max_faces INTEGER,
  max_fingerprints INTEGER,
  max_cards INTEGER,
  max_transactions INTEGER,
  last_capability_sync TIMESTAMPTZ
)

device_attendance_events (
  id UUID PRIMARY KEY,
  device_id UUID REFERENCES devices(id),
  device_event_id VARCHAR,
  device_user_id VARCHAR,
  employee_id UUID REFERENCES employees(id),
  event_time TIMESTAMPTZ NOT NULL,
  event_time_local TIMESTAMPTZ,
  verify_type SMALLINT,    -- face/fingerprint/card/password
  verify_state SMALLINT,   -- in/out/break/overtime
  work_code VARCHAR,
  raw_payload JSONB,
  event_fingerprint VARCHAR NOT NULL,
  received_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(device_id, event_fingerprint)
)

sync_jobs (
  id UUID PRIMARY KEY,
  device_id UUID REFERENCES devices(id),
  type VARCHAR,
  status VARCHAR,          -- QUEUED | RUNNING | WAITING_FOR_DEVICE | COMPLETED | FAILED
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  records_received INTEGER DEFAULT 0,
  records_inserted INTEGER DEFAULT 0,
  records_duplicate INTEGER DEFAULT 0,
  records_failed INTEGER DEFAULT 0,
  error_message TEXT
)

device_commands (
  id UUID PRIMARY KEY,
  device_id UUID REFERENCES devices(id),
  command_type VARCHAR,
  payload JSONB,
  status VARCHAR,          -- QUEUED | SENT | COMPLETED | FAILED | WAITING_FOR_DEVICE
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  scheduled_at TIMESTAMPTZ,
  executed_at TIMESTAMPTZ,
  error TEXT,
  sync_job_id UUID REFERENCES sync_jobs(id)
)
```

### 10.2 Multi-Tenancy

```sql
tenants (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  slug VARCHAR UNIQUE NOT NULL,
  plan VARCHAR DEFAULT 'standard',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
)
-- tenant_id column added to: devices, employees, departments,
-- areas, shifts, leave_types, hrm_push_targets, users
```

### 10.3 Employee & Organization Tables

```sql
employees (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  employee_code VARCHAR NOT NULL,
  first_name VARCHAR,
  last_name VARCHAR,
  email VARCHAR,
  phone VARCHAR,
  department_id UUID REFERENCES departments(id),
  position_id UUID REFERENCES positions(id),
  area_id UUID REFERENCES areas(id),
  hire_date DATE,
  status VARCHAR,          -- ACTIVE | INACTIVE | TERMINATED
  device_user_id VARCHAR,  -- ID used on the device
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  UNIQUE(tenant_id, employee_code)
)

departments  (id, tenant_id, name, parent_id, area_id)
positions    (id, tenant_id, title, department_id)
areas        (id, tenant_id, name, timezone)

employee_biometrics (
  id UUID PRIMARY KEY,
  employee_id UUID REFERENCES employees(id),
  template_type VARCHAR,   -- face | fingerprint | palm | card | qr
  template_data BYTEA,     -- encrypted at rest
  device_id UUID REFERENCES devices(id),
  synced_to_devices UUID[],
  created_at TIMESTAMPTZ
)
```

### 10.4 Shift & Schedule Tables

```sql
shifts (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  name VARCHAR,
  type VARCHAR,            -- FIXED | FLEXIBLE | OPEN
  start_time TIME,
  end_time TIME,
  break_minutes INTEGER DEFAULT 0,
  grace_minutes INTEGER DEFAULT 0,
  overtime_threshold_minutes INTEGER DEFAULT 0,
  cross_day BOOLEAN DEFAULT FALSE,
  color VARCHAR
)

shift_cycles (id, tenant_id, name, pattern JSONB, cycle_length_days INTEGER)

rosters (
  id UUID PRIMARY KEY,
  employee_id UUID REFERENCES employees(id),
  shift_id UUID REFERENCES shifts(id),
  cycle_id UUID REFERENCES shift_cycles(id),
  effective_from DATE,
  effective_to DATE,
  assigned_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ
)

holidays (id, tenant_id, name, date DATE, area_id, is_paid BOOLEAN, recurring BOOLEAN)
```

### 10.5 Attendance Tables

```sql
attendance_records (
  id UUID PRIMARY KEY,
  employee_id UUID REFERENCES employees(id),
  date DATE NOT NULL,
  shift_id UUID REFERENCES shifts(id),
  first_in TIMESTAMPTZ,
  last_out TIMESTAMPTZ,
  total_work_minutes INTEGER,
  break_minutes INTEGER,
  late_minutes INTEGER,
  early_leave_minutes INTEGER,
  overtime_minutes INTEGER,
  status VARCHAR,          -- PRESENT | ABSENT | HALF_DAY | ON_LEAVE | HOLIDAY
  is_manual BOOLEAN DEFAULT FALSE,
  manually_edited_by UUID,
  manually_edited_at TIMESTAMPTZ,
  calculated_at TIMESTAMPTZ,
  UNIQUE(employee_id, date)
)

attendance_policies (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  name VARCHAR,
  late_grace_minutes INTEGER,
  early_leave_grace_minutes INTEGER,
  absence_threshold_minutes INTEGER,
  half_day_threshold_minutes INTEGER,
  overtime_rule JSONB,
  pay_code VARCHAR,
  applicable_departments UUID[]
)

manual_punch_requests (
  id UUID PRIMARY KEY,
  employee_id UUID,
  requested_time TIMESTAMPTZ,
  punch_type VARCHAR,
  reason TEXT,
  status VARCHAR,
  approved_by UUID,
  approved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ
)
```

### 10.6 Leave Tables

```sql
leave_types (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  name VARCHAR,
  accrual_rate NUMERIC,
  max_balance NUMERIC,
  carry_forward BOOLEAN,
  requires_approval BOOLEAN,
  paid BOOLEAN
)

leave_balances (
  id UUID PRIMARY KEY,
  employee_id UUID,
  leave_type_id UUID,
  balance NUMERIC,
  used NUMERIC,
  accrued NUMERIC,
  year INTEGER,
  UNIQUE(employee_id, leave_type_id, year)
)

leave_requests (
  id UUID PRIMARY KEY,
  employee_id UUID,
  leave_type_id UUID,
  start_date DATE,
  end_date DATE,
  days NUMERIC,
  reason TEXT,
  status VARCHAR,
  current_approver_id UUID,
  approval_level INTEGER,
  created_at TIMESTAMPTZ
)
```

### 10.7 HRM Push Tables

```sql
hrm_push_targets (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  name VARCHAR,
  type VARCHAR,            -- odoo | sap | zoho | bamboohr | custom
  base_url VARCHAR,
  auth_config JSONB,       -- { type: bearer|basic|apikey|oauth2, ... }
  field_map JSONB,
  event_subscriptions TEXT[],
  active BOOLEAN DEFAULT TRUE,
  retry_config JSONB       -- { max_attempts: 5, backoff: exponential }
)

hrm_push_jobs (
  id UUID PRIMARY KEY,
  target_id UUID REFERENCES hrm_push_targets(id),
  event_type VARCHAR,
  employee_id UUID,
  payload JSONB,
  status VARCHAR,          -- QUEUED | SENT | FAILED | RETRYING
  attempts INTEGER DEFAULT 0,
  next_retry_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ
)

push_log (
  id UUID PRIMARY KEY,
  target_id UUID,
  job_id UUID,
  event_type VARCHAR,
  employee_id UUID,
  payload JSONB,
  response_status INTEGER,
  response_body TEXT,
  attempt_number INTEGER,
  sent_at TIMESTAMPTZ,
  duration_ms INTEGER,
  success BOOLEAN
)
```

### 10.8 Payroll Tables

```sql
pay_codes    (id, tenant_id, code, name, type, rate_type, rate, taxable)
employee_salary (id, employee_id, pay_code_id, amount, effective_from, effective_to)
payroll_runs    (id, tenant_id, period_start, period_end, status, created_by, created_at)
payroll_items   (id, payroll_run_id, employee_id, pay_code_id, amount, hours, notes)
```

### 10.9 Access Control & Visitor Tables

```sql
access_groups  (id, tenant_id, name, device_id, door_id, schedule JSONB)
employee_access (id, employee_id, access_group_id, valid_from, valid_to)

visitors (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  name VARCHAR,
  company VARCHAR,
  phone VARCHAR,
  id_number VARCHAR,
  photo_url VARCHAR,
  host_employee_id UUID,
  purpose TEXT,
  check_in_at TIMESTAMPTZ,
  check_out_at TIMESTAMPTZ,
  badge_number VARCHAR,
  access_group_id UUID,
  status VARCHAR           -- EXPECTED | CHECKED_IN | CHECKED_OUT
)
```

### 10.10 System Tables

```sql
tenants      (id, name, slug, plan, is_active, created_at)

users (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  email VARCHAR,
  password_hash VARCHAR,
  role VARCHAR,            -- super_admin | hr_admin | manager | employee
  employee_id UUID,
  is_active BOOLEAN,
  totp_secret VARCHAR,
  last_login_at TIMESTAMPTZ
)

audit_log (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  user_id UUID,
  action VARCHAR,
  entity_type VARCHAR,
  entity_id UUID,
  before_state JSONB,
  after_state JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ
)

notifications (id, recipient_id, channel, subject, body, status, sent_at, error)
report_templates (id, tenant_id, name, type, query, columns JSONB, schedule)
```

---

## 11. API Surface

### 11.1 ADMS Endpoints (ZKTeco Device Communication)

```http
GET  /iclock/cdata         # Handshake — device sends serial, gets config back
POST /iclock/cdata         # Device pushes attendance records
GET  /iclock/getrequest    # Device polls for pending commands
POST /iclock/devicecmd     # Device confirms command execution
GET  /iclock/ping          # Heartbeat every 30–60s
```

### 11.2 Devices

```http
GET    /api/v1/devices                      # List all devices
POST   /api/v1/devices                      # Register device manually
GET    /api/v1/devices/{id}                 # Device detail + status
PATCH  /api/v1/devices/{id}                 # Update device settings
DELETE /api/v1/devices/{id}                 # Remove device
POST   /api/v1/devices/{id}/sync            # Trigger manual sync
POST   /api/v1/devices/{id}/reboot          # Remote reboot
POST   /api/v1/devices/{id}/commands        # Send custom command
POST   /api/v1/devices/{id}/transfer        # Transfer employees to another device
GET    /api/v1/devices/{id}/events          # Raw attendance events from device
```

### 11.3 Employees

```http
GET    /api/v1/employees                    # List employees
POST   /api/v1/employees                    # Create employee
GET    /api/v1/employees/{id}               # Employee detail
PATCH  /api/v1/employees/{id}               # Update employee
POST   /api/v1/employees/{id}/push-to-device   # Push employee to device(s)
POST   /api/v1/employees/{id}/sync-biometrics  # Pull/push biometric templates
DELETE /api/v1/employees/{id}/from-device/{device_id}  # Remove from device
```

### 11.4 Attendance

```http
GET    /api/v1/attendance                   # List attendance records (filterable)
GET    /api/v1/attendance/{employee_id}     # Employee attendance history
POST   /api/v1/attendance/manual-punch      # Submit manual punch
POST   /api/v1/attendance/recalculate       # Trigger recalculation for date range
GET    /api/v1/attendance/live              # WebSocket: live punch feed
```

### 11.5 HRM Push

```http
GET    /api/v1/hrm/targets                  # List push targets
POST   /api/v1/hrm/targets                  # Create push target
PATCH  /api/v1/hrm/targets/{id}             # Update push target
DELETE /api/v1/hrm/targets/{id}             # Remove push target
POST   /api/v1/hrm/targets/{id}/test        # Send test payload
GET    /api/v1/hrm/targets/{id}/logs        # Push audit log
POST   /api/v1/hrm/jobs/{id}/retry          # Retry failed push job
```

### 11.6 Shifts & Leave

```http
GET    /api/v1/shifts                       # List shifts
POST   /api/v1/shifts                       # Create shift
POST   /api/v1/rosters/bulk-assign          # Bulk roster assignment
GET    /api/v1/leave/types                  # Leave types
POST   /api/v1/leave/requests               # Submit leave request
PUT    /api/v1/leave/requests/{id}/approve  # Approve / reject
```

### 11.7 Reports

```http
GET    /api/v1/reports/attendance           # Attendance summary report
GET    /api/v1/reports/late                 # Late arrivals report
GET    /api/v1/reports/absent               # Absenteeism report
GET    /api/v1/reports/overtime             # Overtime report
GET    /api/v1/reports/device-health        # Device sync health report
GET    /api/v1/reports/hrm-push             # HRM push success/failure report
POST   /api/v1/reports/export               # Export (CSV / Excel / PDF)
```

### 11.8 Sync Jobs

```http
GET    /api/v1/sync-jobs                    # List sync jobs
GET    /api/v1/sync-jobs/{id}               # Sync job detail + progress
POST   /api/v1/sync-jobs/{id}/retry         # Retry failed sync job
```

---

## 12. Sync Engine Architecture

```
                    Sync Manager
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      ADMS Push      Scheduled Sync  Manual Sync
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Synchronization Pipeline
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Validate       Deduplicate     Store RAW
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Attendance Engine
                         ▼
                  PostgreSQL (upsert)
                         │
                         ▼
                  HRM Push Router
```

**Sync Job Lifecycle:**

```
QUEUED → RUNNING → COMPLETED
              │
              ▼
     WAITING_FOR_DEVICE → COMPLETED
              │
              ▼
           FAILED → (retry up to 3x) → COMPLETED | PERMANENTLY_FAILED
```

**Per-device locking** prevents concurrent sync jobs for the same device:

```
lock:device:{device_id}:sync   (Redis SETNX, TTL 10 min)
```

---

## 13. Device State Machine

```
             ┌──────────┐
             │ UNKNOWN  │
             └────┬─────┘
                  │ first heartbeat received
                  ▼
             ┌──────────┐
        ┌───►│  ONLINE  │◄──────────────┐
        │    └────┬─────┘               │
        │         │ heartbeat timeout   │ device reconnects
        │         ▼                     │
        │    ┌──────────┐               │
        │    │ OFFLINE  │───────────────┘
        │    └────┬─────┘
        │         │ admin disables
        │         ▼
        │    ┌──────────┐
        └────│ DISABLED │
             └──────────┘
```

**Heartbeat monitoring (Celery Beat, every 1 min):**

```python
for device in devices.where(status != DISABLED):
    if now() - device.last_seen_at > OFFLINE_THRESHOLD:
        device.status = OFFLINE
        notify_admins(device)
```

---

## 14. Technology Stack

| Layer         | Technology                                              |
|---------------|---------------------------------------------------------|
| Frontend      | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| Mobile        | Flutter 3                                               |
| API           | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic             |
| Database      | PostgreSQL 16                                           |
| Queue         | Redis 7 + Celery 5                                      |
| Cache         | Redis 7                                                 |
| File Storage  | MinIO (self-hosted) or AWS S3                           |
| Auth          | JWT, OAuth2, TOTP (2FA)                                 |
| Notifications | SMTP, WhatsApp Business API, Firebase Push              |
| Monitoring    | Prometheus, Grafana, Sentry                             |
| CI/CD         | GitHub Actions                                          |
| Deployment    | Docker Compose (dev/prod), Kubernetes (optional)        |
| Testing       | Pytest, Factory Boy, Playwright, Locust                 |
| API Docs      | OpenAPI / Swagger (auto-generated by FastAPI)           |

---

## 15. Key Architectural Principles

1. **Automatic first, manual fallback, never lose data** — devices push automatically; manual sync is always a fallback; offline devices recover on reconnect.
2. **Device-agnostic** — any ZKTeco device that supports ADMS works. New models require a DB row, not code.
3. **HRM-agnostic** — push to any HRM via configurable webhook targets with field mapping.
4. **Raw events are immutable** — attendance records are always derived and can be fully recalculated from raw events.
5. **Idempotent ingestion** — event fingerprint deduplication means retries and double-pushes are safe.
6. **Async everywhere** — no blocking HTTP; sync and push jobs return `202 Accepted` with a job ID.
7. **Capability-aware** — commands are validated against the device's actual capabilities before queuing.
8. **Per-device locking** — Redis locks prevent concurrent sync conflicts on the same device.
9. **Multi-tenant by design** — `tenant_id` on all domain tables; data is fully isolated per organization.
10. **Audit everything** — every data change, sync job, push attempt, and device command is logged.

---

## 16. Quickstart (Docker Compose)

### Prerequisites

- Docker ≥ 24
- Docker Compose ≥ 2.20

### 1. Clone

```bash
git clone https://github.com/your-org/biotime-open.git
cd biotime-open
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY, POSTGRES_PASSWORD, FIRST_ADMIN_EMAIL
```

### 3. Start

```bash
docker compose up -d
```

### 4. Run migrations

```bash
docker compose exec api alembic upgrade head
```

### 5. Create first admin

```bash
docker compose exec api python manage.py create-superuser
```

### 6. Open dashboard

```
http://localhost:3000
```

### 7. Point your ZKTeco device at the server

On the device, set:

```
Server Address:  http://YOUR_SERVER_IP:8000
Server Path:     /iclock/
```

The device will auto-register on first connect.

---

## 17. Environment Variables

| Variable                  | Required | Default         | Description                                  |
|---------------------------|----------|-----------------|----------------------------------------------|
| `SECRET_KEY`              | Yes      | —               | JWT signing secret (generate randomly)       |
| `POSTGRES_HOST`           | Yes      | `db`            | PostgreSQL host                              |
| `POSTGRES_PORT`           | No       | `5432`          | PostgreSQL port                              |
| `POSTGRES_DB`             | Yes      | `biotime`       | Database name                                |
| `POSTGRES_USER`           | Yes      | `biotime`       | Database user                                |
| `POSTGRES_PASSWORD`       | Yes      | —               | Database password                            |
| `REDIS_URL`               | Yes      | `redis://redis` | Redis connection URL                         |
| `MINIO_ENDPOINT`          | No       | `minio:9000`    | MinIO / S3 endpoint                          |
| `MINIO_ACCESS_KEY`        | No       | —               | MinIO access key                             |
| `MINIO_SECRET_KEY`        | No       | —               | MinIO secret key                             |
| `FIRST_ADMIN_EMAIL`       | Yes      | —               | Email for the initial superadmin account     |
| `FIRST_ADMIN_PASSWORD`    | Yes      | —               | Password for the initial superadmin account  |
| `DEVICE_OFFLINE_THRESHOLD`| No       | `300`           | Seconds before device is marked offline      |
| `HRM_PUSH_MAX_RETRIES`    | No       | `5`             | Max retry attempts for failed HRM pushes     |
| `SENTRY_DSN`              | No       | —               | Sentry DSN for error tracking                |
| `SMTP_HOST`               | No       | —               | SMTP host for email notifications            |
| `SMTP_PORT`               | No       | `587`           | SMTP port                                    |
| `SMTP_USER`               | No       | —               | SMTP username                                |
| `SMTP_PASSWORD`           | No       | —               | SMTP password                                |

---

## 18. Project Structure

```
biotime-open/
├── api/                        # FastAPI backend
│   ├── core/                   # Config, database, security, middleware
│   ├── devices/                # Device management + ADMS server
│   │   ├── adms/               # ADMS protocol handler (/iclock/*)
│   │   ├── adapters/           # Protocol adapters (ADMS, PUSH SDK, TCP)
│   │   ├── registry.py         # Device model registry
│   │   └── capability.py       # Capability resolver
│   ├── attendance/             # Attendance engine + processing
│   ├── employees/              # Employee and biometrics management
│   ├── shifts/                 # Shift and roster engine
│   ├── leave/                  # Leave engine
│   ├── payroll/                # Payroll engine
│   ├── hrm_push/               # HRM push layer + webhook targets
│   │   ├── router.py           # Event router
│   │   ├── worker.py           # Celery push worker
│   │   ├── targets/            # Built-in target connectors
│   │   │   ├── odoo.py
│   │   │   ├── bamboohr.py
│   │   │   ├── zoho.py
│   │   │   └── generic.py
│   │   └── field_mapper.py     # Field map transform engine
│   ├── access/                 # Access control
│   ├── visitors/               # Visitor management
│   ├── reports/                # Report engine
│   ├── notifications/          # Notification service
│   ├── sync/                   # Sync engine + job management
│   ├── tasks/                  # Celery tasks + beat schedule
│   └── websocket/              # WebSocket live feed
├── web/                        # Next.js frontend
│   ├── app/                    # App router pages
│   ├── components/             # UI components
│   └── lib/                    # API client, hooks, utils
├── mobile/                     # Flutter mobile app
├── migrations/                 # Alembic DB migrations
├── docker/                     # Dockerfiles
├── docker-compose.yml          # Development stack
├── docker-compose.prod.yml     # Production stack
├── .env.example
└── README.md
```

---

## 19. Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

### Areas where help is most needed

- **Device connectors** — if you have a ZKTeco model not listed above, test it and submit the `device_models` row
- **HRM connectors** — native connectors for SAP SuccessFactors, Oracle HCM, Workday
- **Translations** — the UI needs i18n (Arabic, Urdu, Hindi, Bahasa, French)
- **Tests** — device protocol mock tests, Playwright E2E tests
- **Documentation** — device setup guides per model

### Development setup

```bash
# Backend
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000

# Frontend
cd web
npm install
npm run dev

# Queue workers
cd api
celery -A tasks worker --loglevel=info
celery -A tasks beat --loglevel=info
```

---

## 20. License

MIT License — see [LICENSE](LICENSE).

This project is not affiliated with, endorsed by, or connected to ZKTeco Co., Ltd. or ZKBiometrics.
"BioTime" is a registered trademark of ZKTeco. This project uses the same open ADMS protocol that ZKTeco devices expose.
