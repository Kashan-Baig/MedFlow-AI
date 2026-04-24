from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Generic
from typing_extensions import TypeVar
from datetime import date, time
from decimal import Decimal
from src.backend.database.models import AppointmentStatus, CaseType, BloodGroup
from src.backend.schemas.auth_schemas import (
    AdminAuthOut,
    DoctorAuthOut,
    LoginResponse,
    PatientAuthOut,
    RegisterResponse,
    UserBase,
    UserCreate,
    UserLogin,
    UserOut,
)

# Defaulting T to Any allows both GenericResponse[T] and GenericResponse.
T = TypeVar("T", default=Any)


class GenericResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None


# --- PATIENT & HISTORY ---
class MedicalHistoryBase(BaseModel):
    allergies: List[str] = []
    blood_group: Optional[BloodGroup] = None
    chronic_conditions: List[str] = []
    current_medications: List[str] = []
    last_updated: Optional[date] = None


class PatientBase(BaseModel):
    full_name: str
    email: EmailStr
    contact_number: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None


class PatientOut(PatientBase):
    patient_id: int

    class Config:
        from_attributes = True


# --- DOCTOR & SLOTS ---
class DoctorOut(BaseModel):
    doctor_id: int
    name: str
    specialization: Optional[str] = None
    on_duty_status: bool
    workload_count: int

    class Config:
        from_attributes = True


class SlotOut(BaseModel):
    slot_id: int
    available_date: date
    start_time: time
    end_time: time
    is_locked: bool

    class Config:
        from_attributes = True


# --- PRECHECK & APPOINTMENT ---
class MedicalPrecheckBase(BaseModel):
    blood_pressure: Optional[str] = None
    temperature: Optional[Decimal] = None
    pulse_rate: Optional[int] = None
    spo2: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    patient_symptoms: List[str] = []
    ai_predicted_condition: Optional[str] = None


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    slot_id: int
    case_type: CaseType


class AppointmentOut(BaseModel):
    appointment_id: int
    status: AppointmentStatus
    case_type: CaseType

    class Config:
        from_attributes = True
