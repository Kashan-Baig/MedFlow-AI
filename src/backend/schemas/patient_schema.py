from typing import Optional
from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr
from src.backend.database.models import Patient


class PatientUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
