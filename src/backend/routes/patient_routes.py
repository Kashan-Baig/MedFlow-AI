from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import jwt

from src.backend.database.db_connection import get_db
from src.backend.core.middleware import get_current_admin,get_current_user

router = APIRouter()


@router.post("/consult")
def consult(data: dict, admin: dict = Depends(get_current_admin)):
    return {"message": "Consultation logic goes here", "admin": admin.get("sub")}


@router.get("/all_patients")
def get_all_patient(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):

    result = db.execute(text("""
        SELECT 
            patient_id, full_name, age 
        FROM patients
    """)).fetchall()

    patients = [dict(row._mapping) for row in result]

    return {
        "status": "success",
        "count": len(patients),
        "data": patients
    }

@router.get("/user_data")
def get_single_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    result = db.execute(text("""
        SELECT 
            id,
            email,
            password_hash,
            role
        FROM users
        WHERE id = :id
    """), {"id": id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = dict(result._mapping)

    return {
        "status": "success",
        "data": user_data
    }
