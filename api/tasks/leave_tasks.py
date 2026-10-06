"""Celery tasks — leave accrual."""
from core.celery_app import celery_app


@celery_app.task(name="tasks.leave_tasks.daily_accrual", bind=True)
def daily_accrual(self):
    """
    Accrue leave balances daily for all active employees.
    Runs at 00:05 every day via Celery Beat.
    """
    import asyncio
    from datetime import date
    from core.database import AsyncSessionLocal
    from sqlalchemy import select
    from employees.models import Employee, EmployeeStatus
    from leave.models import LeaveType, LeaveBalance

    async def _run():
        async with AsyncSessionLocal() as db:
            today = date.today()
            accrued = 0

            result = await db.execute(
                select(Employee).where(Employee.status == EmployeeStatus.ACTIVE)
            )
            employees = list(result.scalars().all())

            for emp in employees:
                types_result = await db.execute(
                    select(LeaveType).where(
                        LeaveType.tenant_id == emp.tenant_id,
                        LeaveType.accrual_rate > 0,
                    )
                )
                leave_types = list(types_result.scalars().all())

                for lt in leave_types:
                    daily_rate = float(lt.accrual_rate) / 365.0

                    bal_result = await db.execute(
                        select(LeaveBalance).where(
                            LeaveBalance.employee_id == emp.id,
                            LeaveBalance.leave_type_id == lt.id,
                            LeaveBalance.year == today.year,
                        )
                    )
                    balance = bal_result.scalar_one_or_none()

                    if not balance:
                        balance = LeaveBalance(
                            tenant_id=emp.tenant_id,
                            employee_id=emp.id,
                            leave_type_id=lt.id,
                            year=today.year,
                            balance=0,
                            used=0,
                            accrued=0,
                        )

                    new_balance = min(
                        float(balance.balance) + daily_rate,
                        float(lt.max_balance),
                    )
                    balance.balance = round(new_balance, 4)
                    balance.accrued = round(float(balance.accrued) + daily_rate, 4)
                    db.add(balance)
                    accrued += 1

            await db.commit()
            return {"date": str(today), "accrued_entries": accrued}

    return asyncio.get_event_loop().run_until_complete(_run())
