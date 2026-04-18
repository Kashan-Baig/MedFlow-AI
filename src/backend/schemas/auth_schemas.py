from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Generic, Union
from src.backend.database.models import (
    Gender,
    UserRole,
    AppointmentStatus,
    CaseType,
    BloodGroup,
)


#  --- AUTH & USER SCHEMAS ---
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.PATIENT
    fullName: str
    contact_number: str
    gender: Gender
    specialization: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserOut
    access_token: str


class PatientAuthOut(BaseModel):
    patient_id: int
    full_name: str
    email: EmailStr
    contact_number: Optional[str] = None
    gender: Optional[Gender] = None

    class Config:
        from_attributes = True


class DoctorAuthOut(BaseModel):
    doctor_id: int
    full_name: str
    email: EmailStr
    contact_number: Optional[str] = None
    gender: Optional[Gender] = None

    class Config:
        from_attributes = True


class AdminAuthOut(BaseModel):
    admin_id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    user: UserOut
    role: Union[PatientAuthOut, DoctorAuthOut, AdminAuthOut]
