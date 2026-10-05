"""Employee service — CRUD + device push."""
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions import ConflictError, NotFoundError
from employees.models import Employee, EmployeeBiometric


async def list_employees(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    department_id: uuid.UUID | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Employee], int]:
    q = select(Employee).where(Employee.tenant_id == tenant_id)
    if department_id:
        q = q.where(Employee.department_id == department_id)
    if status:
        q = q.where(Employee.status == status)
    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Employee.first_name.ilike(term),
                Employee.last_name.ilike(term),
                Employee.employee_code.ilike(term),
                Employee.email.ilike(term),
            )
        )
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_employee(db: AsyncSession, employee_id: uuid.UUID) -> Employee | None:
    result = await db.execute(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(selectinload(Employee.biometrics))
    )
    return result.scalar_one_or_none()


async def get_employee_by_code(db: AsyncSession, tenant_id: uuid.UUID, code: str) -> Employee | None:
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.employee_code == code,
        )
    )
    return result.scalar_one_or_none()


async def get_employee_by_device_uid(db: AsyncSession, tenant_id: uuid.UUID, device_user_id: str) -> Employee | None:
    result = await db.execute(
        select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.device_user_id == device_user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_employee(db: AsyncSession, tenant_id: uuid.UUID, data: dict) -> Employee:
    # Check uniqueness of employee_code within tenant
    existing = await get_employee_by_code(db, tenant_id, data["employee_code"])
    if existing:
        raise ConflictError(f"Employee code '{data['employee_code']}' already exists")

    employee = Employee(tenant_id=tenant_id, **data)
    db.add(employee)
    await db.flush()
    return employee


async def update_employee(db: AsyncSession, employee: Employee, data: dict) -> Employee:
    for key, val in data.items():
        setattr(employee, key, val)
    db.add(employee)
    await db.flush()
    return employee


async def delete_employee(db: AsyncSession, employee: Employee) -> None:
    await db.delete(employee)
    await db.flush()


async def push_employee_to_devices(
    db: AsyncSession,
    employee: Employee,
    device_ids: list[uuid.UUID],
    include_biometrics: bool = True,
) -> list[str]:
    """Queue CREATE_USER command for each target device."""
    from devices.service import get_device_by_id, queue_command
    from devices.models import CommandType

    results = []
    for device_id in device_ids:
        device = await get_device_by_id(db, device_id)
        if not device:
            results.append(f"{device_id}: device not found")
            continue

        payload = {
            "pin": employee.device_user_id or str(employee.employee_code),
            "name": f"{employee.first_name} {employee.last_name}",
            "privilege": 0,
            "card": "",
        }
        await queue_command(db, device, CommandType.CREATE_USER, payload=payload)
        results.append(f"{device_id}: queued")

    await db.flush()
    return results
