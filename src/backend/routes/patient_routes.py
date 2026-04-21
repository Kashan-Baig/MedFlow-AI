from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

# from workflows.patient_flow import run_patient_flow
import src.ai.db_services.db_services as db_service
import src.backend.core.middleware as security
from src.backend.database.db_connection import get_db
from sqlalchemy.orm import Session


router = APIRouter(prefix="/patient", tags=["Patient"])


@router.post("/consult")
def consult(data: dict, admin: dict = Depends(security.get_current_admin)):
    return {"message": "Consultation logic goes here", "admin": admin.get("sub")}


@router.get("/all_patients")
def get_all_patient(
    db: Session = Depends(get_db), admin: dict = Depends(security.get_current_admin)
):

    print(admin)
    result = db.execute(
        text(
            """
        SELECT 
            patient_id, full_name, age 
        FROM patients
    """
        )
    ).fetchall()

    patients = [dict(row._mapping) for row in result]

    return {"status": "success", "count": len(patients), "data": patients}


@router.get("/user_data")
def get_single_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.get_current_user),
):

    result = db.execute(
        text(
            """
        SELECT 
            id,
            email,
            password_hash,
            role
        FROM users
        WHERE id = :id
    """
        ),
        {"id": id},
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = dict(result._mapping)

    return {"status": "success", "data": user_data}


@router.get("/appointments")
def get_patient_appointments(
    current_patient: dict = Depends(security.get_current_patient),
):
    patient_id = current_patient.get("role_id")
    return {
        "status_code": 200,
        "message": "Appointments fetched successfully",
        "data": db_service.get_appointments_by_patient_id(patient_id),
    }
