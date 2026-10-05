"""Employee schemas."""
import uuid
from datetime import date, datetime
from pydantic import BaseModel, EmailStr


class AreaOut(BaseModel):
    id: uuid.UUID
    name: str
    timezone: str
    model_config = {"from_attributes": True}


class DepartmentOut(BaseModel):
    id: uuid.UUID
    name: str
    area_id: uuid.UUID | None
    model_config = {"from_attributes": True}


class PositionOut(BaseModel):
    id: uuid.UUID
    title: str
    department_id: uuid.UUID | None
    model_config = {"from_attributes": True}


class EmployeeOut(BaseModel):
    id: uuid.UUID
    employee_code: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    status: str
    hire_date: date | None
    photo_url: str | None
    device_user_id: str | None
    department_id: uuid.UUID | None
    position_id: uuid.UUID | None
    area_id: uuid.UUID | None
    tenant_id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class EmployeeCreate(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None
    hire_date: date | None = None
    department_id: uuid.UUID | None = None
    position_id: uuid.UUID | None = None
    area_id: uuid.UUID | None = None
    device_user_id: str | None = None


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    status: str | None = None
    hire_date: date | None = None
    department_id: uuid.UUID | None = None
    position_id: uuid.UUID | None = None
    area_id: uuid.UUID | None = None


class PushToDeviceRequest(BaseModel):
    device_ids: list[uuid.UUID]
    include_biometrics: bool = True


class EmployeeListParams(BaseModel):
    department_id: uuid.UUID | None = None
    status: str | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 50
