"""Celery tasks — report generation."""
import uuid
from core.celery_app import celery_app


@celery_app.task(name="tasks.report_tasks.generate_attendance_report", bind=True)
def generate_attendance_report(
    self,
    tenant_id: str,
    start_date: str,
    end_date: str,
    department_id: str | None = None,
    employee_id: str | None = None,
):
    import asyncio
    from datetime import date
    from core.database import AsyncSessionLocal
    from attendance.models import AttendanceRecord
    from employees.models import Employee
    from sqlalchemy import select
    import openpyxl
    import io

    async def _run():
        async with AsyncSessionLocal() as db:
            q = (
                select(AttendanceRecord, Employee)
                .join(Employee, Employee.id == AttendanceRecord.employee_id)
                .where(
                    AttendanceRecord.tenant_id == uuid.UUID(tenant_id),
                    AttendanceRecord.date >= date.fromisoformat(start_date),
                    AttendanceRecord.date <= date.fromisoformat(end_date),
                )
            )
            if employee_id:
                q = q.where(AttendanceRecord.employee_id == uuid.UUID(employee_id))

            result = await db.execute(q)
            rows = result.all()

            # Build Excel
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Attendance Report"
            headers = [
                "Employee Code", "Name", "Date", "First In", "Last Out",
                "Work Minutes", "Late Minutes", "OT Minutes", "Status",
            ]
            ws.append(headers)

            for rec, emp in rows:
                ws.append([
                    emp.employee_code,
                    f"{emp.first_name} {emp.last_name}",
                    str(rec.date),
                    str(rec.first_in) if rec.first_in else "",
                    str(rec.last_out) if rec.last_out else "",
                    rec.total_work_minutes,
                    rec.late_minutes,
                    rec.overtime_minutes,
                    rec.status,
                ])

            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)

            # Upload to MinIO
            from core.storage import upload_file
            from core.config import settings
            object_name = f"reports/attendance_{tenant_id}_{start_date}_{end_date}.xlsx"
            url = upload_file(
                settings.MINIO_BUCKET_REPORTS,
                object_name,
                buf,
                len(buf.getvalue()),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            return {"url": url, "rows": len(rows)}

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.report_tasks.generate_payroll_run", bind=True)
def generate_payroll_run(self, run_id: str):
    """Calculate payroll items for a payroll run."""
    import asyncio
    from core.database import AsyncSessionLocal
    from payroll.models import PayrollRun, PayrollItem, EmployeeSalary
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PayrollRun).where(PayrollRun.id == uuid.UUID(run_id))
            )
            run = result.scalar_one_or_none()
            if not run:
                return {"error": "Run not found"}

            # Get all salary records active during period
            sal_result = await db.execute(
                select(EmployeeSalary).where(
                    EmployeeSalary.effective_from <= run.period_end,
                ).where(
                    (EmployeeSalary.effective_to == None) |  # noqa: E711
                    (EmployeeSalary.effective_to >= run.period_start)
                )
            )
            salaries = list(sal_result.scalars().all())

            items_created = 0
            for sal in salaries:
                item = PayrollItem(
                    tenant_id=run.tenant_id,
                    payroll_run_id=run.id,
                    employee_id=sal.employee_id,
                    pay_code_id=sal.pay_code_id,
                    amount=sal.amount,
                    hours=0,
                )
                db.add(item)
                items_created += 1

            run.status = "calculated"
            db.add(run)
            await db.commit()
            return {"run_id": run_id, "items": items_created}

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.report_tasks.generate_wps_report", bind=True)
def generate_wps_report(self, run_id: str, tenant_id: str):
    """Generate WPS (UAE/GCC Wages Protection System) CSV export."""
    import asyncio
    import csv
    import io
    from core.database import AsyncSessionLocal
    from payroll.models import PayrollItem, PayCode
    from employees.models import Employee
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PayrollItem, Employee, PayCode)
                .join(Employee, Employee.id == PayrollItem.employee_id)
                .join(PayCode, PayCode.id == PayrollItem.pay_code_id)
                .where(PayrollItem.payroll_run_id == uuid.UUID(run_id))
            )
            rows = result.all()

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([
                "EmployeeID", "EmployeeName", "IBAN",
                "BasicSalary", "HousingAllowance", "TransportAllowance",
                "TotalSalary", "Currency",
            ])

            # Group by employee
            emp_totals: dict[str, dict] = {}
            for item, emp, pc in rows:
                key = str(emp.id)
                if key not in emp_totals:
                    emp_totals[key] = {
                        "code": emp.employee_code,
                        "name": f"{emp.first_name} {emp.last_name}",
                        "total": 0.0,
                    }
                emp_totals[key]["total"] += float(item.amount)

            for data in emp_totals.values():
                writer.writerow([
                    data["code"], data["name"], "",
                    data["total"], 0, 0,
                    data["total"], "AED",
                ])

            content = buf.getvalue().encode("utf-8")
            from core.storage import upload_file
            from core.config import settings
            object_name = f"reports/wps_{run_id}.csv"
            url = upload_file(
                settings.MINIO_BUCKET_REPORTS,
                object_name,
                io.BytesIO(content),
                len(content),
                "text/csv",
            )
            return {"url": url, "employees": len(emp_totals)}

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="tasks.notification_tasks.send_notification", bind=True)
def send_notification(self, recipient_email: str, subject: str, body: str):
    """Send email notification."""
    from core.config import settings
    import smtplib
    from email.mime.text import MIMEText

    if not settings.SMTP_HOST:
        return {"skipped": "SMTP not configured"}

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return {"sent": True, "to": recipient_email}
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
