from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend.database.db_connection import get_db

router = APIRouter()

@router.get("/dashboard")
def dashboard():
    return {"message": "Doctor dashboard"}


@router.get("/all_doctors")
def get_all_doctors(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT 
                doctor_id, full_name, specialization,email,contact_number
        FROM doctors
    """)).fetchall()

    doctors = [dict(row._mapping) for row in result]

    return {
        "status": "success",
        "count": len(doctors),
        "data": doctors
    }

@router.get("/all_specializations")
def get_all_specializations(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT DISTINCT specialization
        FROM doctors
    """)).fetchall()

    specializations = [row._mapping["specialization"] for row in result]

    return {
        "status": "success",
        "count": len(specializations),
        "data": specializations
    }
