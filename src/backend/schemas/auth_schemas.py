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
    age: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True


class PatientAuthOut(BaseModel):
    id: int = Field(validation_alias="patient_id")
    full_name: str
    email: EmailStr
    contact_number: Optional[str] = None
    gender: Optional[Gender] = None

    class Config:
        from_attributes = True


class DoctorAuthOut(BaseModel):
    id: int = Field(validation_alias="doctor_id")
    full_name: str
    email: EmailStr
    contact_number: Optional[str] = None
    gender: Optional[Gender] = None
    specialization: Optional[str] = None

    class Config:
        from_attributes = True


class AdminAuthOut(BaseModel):
    id: int = Field(validation_alias="admin_id")
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    user: UserOut
    role: Union[PatientAuthOut, DoctorAuthOut, AdminAuthOut]
    access_token: str


class RegisterResponse(BaseModel):
    user: UserOut
    role: Union[PatientAuthOut, DoctorAuthOut, AdminAuthOut]
