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

@router.get("/today_schedule")
def get_today_schedule(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT 
            a.appointment_id,
            a.appointment_date,
            p.full_name AS patient_name,
            d.full_name AS doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE DATE(a.appointment_date) = CURRENT_DATE
        ORDER BY a.appointment_date
    """)).fetchall()

    schedule = [dict(row._mapping) for row in result]

    if not schedule:
        return {
            "status": "success",
            "message": "No appointments scheduled for today",
            "data": []
        }

    return {
        "status": "success",
        "count": len(schedule),
        "data": schedule
    }

@router.get("/doctors_by_specialization")
def get_doctors_by_specialization(
    specialization: str,
    db: Session = Depends(get_db)
):
    result = db.execute(text("""
        SELECT doctor_id, full_name, specialization
        FROM doctors
        WHERE LOWER(specialization) = LOWER(:specialization)
    """), {"specialization": specialization}).fetchall()

    doctors = [dict(row._mapping) for row in result]

    if not doctors:
        return {
            "status": "success",
            "message": f"No doctors found for specialization '{specialization}'",
            "data": []
        }

    return {
        "status": "success",
        "count": len(doctors),
        "data": doctors
    }

@router.get("/patients_by_doctor")
def get_patients_by_doctor(
    doctor_name: str,
    db: Session = Depends(get_db)
):
    result = db.execute(text("""
        SELECT DISTINCT p.patient_id, p.full_name, p.age
        FROM patients p
        JOIN appointments a ON p.patient_id = a.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE LOWER(d.full_name) = LOWER(:doctor_name)
    """), {"doctor_name": doctor_name}).fetchall()

    patients = [dict(row._mapping) for row in result]

    if not patients:
        return {
            "status": "success",
            "message": f"No patients found for doctor '{doctor_name}'",
            "data": []
        }

    return {
        "status": "success",
        "count": len(patients),
        "data": patients
    }

@router.get("/available_slots")
def get_available_slots(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT 
            s.slot_id,
            s.start_time,
            s.end_time,
            d.full_name AS doctor_name
        FROM schedule_slots s
        JOIN doctors d ON s.doctor_id = d.doctor_id
        WHERE s.is_locked = FALSE
        ORDER BY s.start_time
    """)).fetchall()

    slots = [dict(row._mapping) for row in result]

    if not slots:
        return {
            "status": "success",
            "message": "No available slots",
            "data": []
        }

    return {
        "status": "success",
        "count": len(slots),
        "data": slots
    }


