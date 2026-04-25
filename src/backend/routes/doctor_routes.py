from datetime import date as DateType
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database.models import SlotException, ExceptionType

router = APIRouter()


@router.get("/dashboard")
def dashboard():
    return {"message": "Doctor dashboard"}


@router.get("/all_doctors")
def get_all_doctors(db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT 
                doctor_id, full_name, specialization,email,contact_number
        FROM doctors
    """
        )
    ).fetchall()

    doctors = [dict(row._mapping) for row in result]

    return {"status": "success", "count": len(doctors), "data": doctors}


@router.get("/all_specializations")
def get_all_specializations(db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT DISTINCT specialization
        FROM doctors
    """
        )
    ).fetchall()

    specializations = [row._mapping["specialization"] for row in result]

    return {"status": "success", "count": len(specializations), "data": specializations}


@router.get("/today_schedule")
def get_today_schedule(db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
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
    """
        )
    ).fetchall()

    schedule = [dict(row._mapping) for row in result]

    if not schedule:
        return {
            "status": "success",
            "message": "No appointments scheduled for today",
            "data": [],
        }

    return {"status": "success", "count": len(schedule), "data": schedule}


@router.get("/doctors_by_specialization")
def get_doctors_by_specialization(specialization: str, db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT doctor_id, full_name, specialization
        FROM doctors
        WHERE LOWER(specialization) = LOWER(:specialization)
    """
        ),
        {"specialization": specialization},
    ).fetchall()

    doctors = [dict(row._mapping) for row in result]

    if not doctors:
        return {
            "status": "success",
            "message": f"No doctors found for specialization '{specialization}'",
            "data": [],
        }

    return {"status": "success", "count": len(doctors), "data": doctors}


@router.get("/patients_by_doctor")
def get_patients_by_doctor(doctor_name: str, db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
        SELECT DISTINCT p.patient_id, p.full_name, p.age
        FROM patients p
        JOIN appointments a ON p.patient_id = a.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE LOWER(d.full_name) = LOWER(:doctor_name)
    """
        ),
        {"doctor_name": doctor_name},
    ).fetchall()

    patients = [dict(row._mapping) for row in result]

    if not patients:
        return {
            "status": "success",
            "message": f"No patients found for doctor '{doctor_name}'",
            "data": [],
        }

    return {"status": "success", "count": len(patients), "data": patients}


@router.get("/available_slots")
def get_available_slots(
    target_date: DateType,  # e.g. ?target_date=2025-04-19
    db: Session = Depends(get_db),
):
    """
    Returns slots that are available for a given date:
      1. The date's weekday must be in the slot's available_days array.
      2. No SlotException exists for (slot_id, target_date).
      3. booked_count < max_appointments for (slot_id, target_date).
    """
    day_name = target_date.strftime("%A")  # e.g. "Wednesday"

    result = db.execute(
        text(
            """
        SELECT
            s.slot_id,
            s.start_time,
            s.end_time,
            s.max_appointments,
            COALESCE(sb.booked_count, 0)                        AS booked_count,
            s.max_appointments - COALESCE(sb.booked_count, 0)   AS remaining_slots,
            d.doctor_id,
            d.full_name   AS doctor_name,
            d.specialization
        FROM slots s
        JOIN doctors d ON s.doctor_id = d.doctor_id
        LEFT JOIN slot_bookings sb ON s.slot_id = sb.slot_id AND sb.booking_date = :target_date
        WHERE CAST(:day_name AS VARCHAR) = ANY(s.available_days::VARCHAR[])
          AND NOT EXISTS (
              SELECT 1 FROM slot_exceptions se 
              WHERE se.slot_id = s.slot_id AND se.exception_date = :target_date
          )
          AND (s.max_appointments - COALESCE(sb.booked_count, 0)) > 0
        ORDER BY s.start_time
    """
        ),
        {"target_date": target_date, "day_name": day_name},
    ).fetchall()

    slots = [dict(row._mapping) for row in result]

    if not slots:
        return {"status": "success", "message": "No available slots for this date", "data": []}

    return {"status": "success", "count": len(slots), "data": slots}


# ── Mark doctor leave / holiday ────────────────────────────────────────────────
@router.post("/mark_leave")
def mark_leave(
    slot_id: int,
    exception_date: DateType,
    reason: ExceptionType,
    note: str = None,
    db: Session = Depends(get_db),
):
    """
    Marks a specific date as unavailable for a slot (leave, holiday, emergency).
    After this, patients will not be able to book that slot on that date.
    """
    # Prevent duplicate entries
    existing = (
        db.query(SlotException)
        .filter(
            SlotException.slot_id == slot_id,
            SlotException.exception_date == exception_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"An exception already exists for slot {slot_id} on {exception_date}",
        )

    exception = SlotException(
        slot_id=slot_id,
        exception_date=exception_date,
        reason=reason,
        note=note,
    )
    db.add(exception)
    db.commit()
    db.refresh(exception)

    return {
        "status": "success",
        "message": f"Slot {slot_id} marked as unavailable on {exception_date} ({reason.value})",
        "exception_id": exception.exception_id,
    }
