from datetime import date as DateType, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database.models import Doctor, Gender, SlotException, ExceptionType

from src.backend.schemas.all_schema import DoctorUpdateSchema

from src.backend.core.middleware import (
    get_current_admin,
    get_current_user,
)
from datetime import date



router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("/dashboard")
def dashboard():
    return {"message": "Doctor dashboard"}


@router.patch("/update_doctor")
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdateSchema,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()

    if not doctor:
        raise HTTPException(
            status_code=404, detail=f"Doctor with id {doctor_id} not found"
        )

    updated_fields = payload.model_dump(exclude_none=True)

    if not updated_fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    for field, value in updated_fields.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)

    return {
        "status": "success",
        "message": f"Doctor {doctor_id} updated successfully",
        "data": {
            "doctor_id": doctor.doctor_id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "contact_number": doctor.contact_number,
            "gender": doctor.gender,
            "specialization": doctor.specialization,
            "on_duty_status": doctor.on_duty_status,
        },
    }


@router.delete("/delete_doctor")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()

    if not doctor:
        raise HTTPException(
            status_code=404, detail=f"Doctor with id {doctor_id} not found"
        )

    db.delete(doctor)
    db.commit()

    return {
        "status": "success",
        "message": f"Doctor {doctor_id} deleted successfully",
    }


@router.get("/get_doctor")
def get_doctor_by_id(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=404, detail=f"Doctor with id {doctor_id} not found"
        )

    return {
        "status": "success",
        "data": {
            "doctor_id": doctor.doctor_id,
            "full_name": doctor.full_name,
            "email": doctor.email,
            "contact_number": doctor.contact_number,
            "gender": doctor.gender,
            "specialization": doctor.specialization,
            "on_duty_status": doctor.on_duty_status,
            "created_at": doctor.created_at,
        },
    }


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

@router.get("/schedule")
def get_schedule(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = """
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.expected_time,
            a.status,
            a.case_type,
            p.full_name AS patient_name,
            d.full_name AS doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
    """

    params = {}

    if target_date:
        query += " WHERE DATE(a.appointment_date) = :target_date"
        params["target_date"] = target_date

    query += " ORDER BY a.appointment_date"

    result = db.execute(text(query), params).fetchall()

    schedule = [dict(row._mapping) for row in result]

    if not schedule:
        return {
            "status": "success",
            "message": "No appointments found",
            "data": [],
        }

    return {
        "status": "success",
        "count": len(schedule),
        "data": schedule
    }

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
def get_available_slots_range(
    start_date: DateType = None,
    end_date: DateType = None,
    doctor_id: int = None,   
    db: Session = Depends(get_db),
):

    if not start_date:
        start_date = DateType.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    if start_date > end_date:
        return {
            "status": "error",
            "message": "start_date cannot be greater than end_date"
        }

    result = db.execute(
        text(
            """
        WITH date_series AS (
            SELECT generate_series(:start_date, :end_date, INTERVAL '1 day')::date AS slot_date
        )

        SELECT
            ds.slot_date,
            s.slot_id,
            s.start_time,
            s.end_time,
            s.max_appointments,

            COALESCE(sb.booked_count, 0) AS booked_count,
            (s.max_appointments - COALESCE(sb.booked_count, 0)) AS remaining_slots,

            d.doctor_id,
            d.full_name AS doctor_name,
            d.specialization

        FROM date_series ds

        JOIN slots s
            ON TO_CHAR(ds.slot_date, 'FMDay') = ANY (s.available_days::TEXT[])

        JOIN doctors d
            ON s.doctor_id = d.doctor_id

        LEFT JOIN slot_bookings sb
            ON s.slot_id = sb.slot_id
            AND sb.booking_date = ds.slot_date

        WHERE NOT EXISTS (
            SELECT 1
            FROM slot_exceptions se
            WHERE se.slot_id = s.slot_id
              AND se.exception_date = ds.slot_date
        )

        AND (s.max_appointments - COALESCE(sb.booked_count, 0)) > 0

        -- ✅ optional doctor filter
        AND (:doctor_id IS NULL OR s.doctor_id = :doctor_id)

        ORDER BY ds.slot_date, s.start_time
        """
        ),
        {
            "start_date": start_date,
            "end_date": end_date,
            "doctor_id": doctor_id,   # ✅ pass param
        },
    ).fetchall()

    slots = []
    for row in result:
        r = dict(row._mapping)
        # Ensure date and time are strings for consistent frontend matching
        slots.append({
            **r,
            "slot_date": r["slot_date"].strftime("%Y-%m-%d") if hasattr(r["slot_date"], "strftime") else str(r["slot_date"]),
            "start_time": r["start_time"].strftime("%H:%M") if hasattr(r["start_time"], "strftime") else str(r["start_time"])[:5],
            "end_time": r["end_time"].strftime("%H:%M") if hasattr(r["end_time"], "strftime") else str(r["end_time"])[:5]
        })

    if not slots:
        return {
            "status": "success",
            "message": "No available slots in this range",
            "data": [],
        }

    return {
        "status": "success",
        "range": {
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
        "count": len(slots),
        "data": slots,
    }

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

@router.get("/appointments_by_doctor")
def get_appointments_by_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    result = db.execute(text("""
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.patient_id,
            a.status,
            a.expected_time AS time_slot
        FROM appointments a
        WHERE a.doctor_id = :doctor_id
        ORDER BY a.appointment_date
    """), {"doctor_id": doctor_id}).fetchall()

    appointments = [dict(row._mapping) for row in result]


    if not appointments:
        return {
            "status": "success",
            "message": "No appointments found",
            "data": []
        }

    return {
        "status": "success",
        "count": len(appointments),
        "data": appointments
    }
