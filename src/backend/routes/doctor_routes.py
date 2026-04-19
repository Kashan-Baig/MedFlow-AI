from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database import models
from src.backend.core.middleware import get_current_user

router = APIRouter()

@router.get("/dashboard")
def dashboard():
    return {"message": "Doctor dashboard"}

@router.get("/all_doctors")
def get_all_doctors(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):

    result = db.execute(text("""
        SELECT 
            doctor_id, 
            full_name, 
            specialization, 
            user_id, 
            email, 
            contact_number 
        FROM doctors
    """)).fetchall()

    doctors = [dict(row._mapping) for row in result]

    return {
        "status": "success",
        "count": len(doctors),
        "data": doctors
    }

@router.get("/all_specialization")
def get_all_specialization(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    result = db.execute(text("""
        SELECT 
            DISTINCT specialization
        FROM doctors
        WHERE specialization IS NOT NULL
        ORDER BY specialization
    """)).fetchall()
    specializations = [row._mapping["specialization"] for row in result]
    return {
        "status": "success",
        "count": len(specializations),
        "data": specializations
    }
