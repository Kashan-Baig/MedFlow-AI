from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Generic, Union
from src.backend.database.models import (
    Gender,
    UserRole,
    AppointmentStatus,
    CaseType,
    BloodGroup,
)


class DoctorUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = None
    gender: Optional[Gender] = None
    specialization: Optional[str] = None
    on_duty_status: Optional[bool] = None
