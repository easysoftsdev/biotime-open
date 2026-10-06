"""Employee REST endpoints."""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.exceptions import NotFoundError
from employees import schemas, service

router = APIRouter()


@router.get("", response_model=dict)
async def list_employees(
    department_id: uuid.UUID | None = None,
    emp_status: str | None = Query(None, alias="status"),
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employees, total = await service.list_employees(
        db, current_user.tenant_id, department_id, emp_status, search, page, page_size
    )
    return {
        "items": [schemas.EmployeeOut.model_validate(e) for e in employees],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=schemas.EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    body: schemas.EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = await service.create_employee(
        db, current_user.tenant_id, body.model_dump(exclude_none=True)
    )
    await db.commit()
    return employee


@router.get("/{employee_id}", response_model=schemas.EmployeeOut)
async def get_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    emp = await service.get_employee(db, employee_id)
    if not emp or emp.tenant_id != current_user.tenant_id:
        raise NotFoundError("Employee not found")
    return emp


@router.patch("/{employee_id}", response_model=schemas.EmployeeOut)
async def update_employee(
    employee_id: uuid.UUID,
    body: schemas.EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    emp = await service.get_employee(db, employee_id)
    if not emp or emp.tenant_id != current_user.tenant_id:
        raise NotFoundError("Employee not found")
    emp = await service.update_employee(db, emp, body.model_dump(exclude_none=True))
    await db.commit()
    return emp


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    emp = await service.get_employee(db, employee_id)
    if not emp or emp.tenant_id != current_user.tenant_id:
        raise NotFoundError("Employee not found")
    await service.delete_employee(db, emp)
    await db.commit()


@router.post("/{employee_id}/push-to-device", status_code=status.HTTP_202_ACCEPTED)
async def push_to_device(
    employee_id: uuid.UUID,
    body: schemas.PushToDeviceRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    emp = await service.get_employee(db, employee_id)
    if not emp or emp.tenant_id != current_user.tenant_id:
        raise NotFoundError("Employee not found")
    results = await service.push_employee_to_devices(db, emp, body.device_ids, body.include_biometrics)
    await db.commit()
    return {"results": results}
