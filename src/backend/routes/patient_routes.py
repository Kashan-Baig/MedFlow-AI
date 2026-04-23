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

@router.post("/book_appointment")
def book_appointment(
    patient_id: int,
    doctor_id: int,
    slot_id: int,
    db: Session = Depends(get_db)
):
    try:
        lock_query = text("""
            UPDATE schedule_slots
            SET is_locked = TRUE
            WHERE slot_id = :slot_id
            AND is_locked = FALSE
            RETURNING slot_id
        """)

        lock_result = db.execute(lock_query, {"slot_id": slot_id}).fetchone()

        if not lock_result:
            raise HTTPException(
                status_code=400,
                detail="Slot already booked"
            )

        insert_query = text("""
            INSERT INTO appointments (patient_id, doctor_id, slot_id, status)
            VALUES (:patient_id, :doctor_id, :slot_id, :status)
            RETURNING appointment_id
        """)

        result = db.execute(insert_query, {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "slot_id": slot_id,
            "status": "Confirmed"
        })

        appointment_id = result.fetchone()[0]

        db.commit()

        return {
            "status": "success",
            "appointment_id": appointment_id,
            "message": "Appointment booked successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient_history")
def get_patient_history(
    patient_id: int,
    db: Session = Depends(get_db)
):
    medical = db.execute(text("""
        SELECT 
            allergies,
            blood_group,
            chronic_conditions,
            current_medications,
            last_updated
        FROM medical_history
        WHERE patient_id = :patient_id
    """), {"patient_id": patient_id}).fetchone()

    medical_history = dict(medical._mapping) if medical else {}

    visits = db.execute(text("""
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.status,
            d.full_name AS doctor_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = :patient_id
        ORDER BY a.appointment_date DESC
    """), {"patient_id": patient_id}).fetchall()

    visiting_history = [dict(row._mapping) for row in visits]

    return {
        "status": "success",
        "medical_history": medical_history,
        "visiting_history": visiting_history,
        "total_visits": len(visiting_history)
    }



