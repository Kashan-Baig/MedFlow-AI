from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

# from workflows.patient_flow import run_patient_flow
import src.ai.db_services.db_services as db_service
import src.backend.core.middleware as security
from src.backend.database.models import AppointmentStatus
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
    appointment_date: str,
    db: Session = Depends(get_db),
):
    try:
        # 1. Get the slot to check max_appointments and start_time
        slot_data = db.execute(
            text("SELECT max_appointments, start_time FROM slots WHERE slot_id = :slot_id"),
            {"slot_id": slot_id}
        ).fetchone()
        
        if not slot_data:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        max_apps, start_time = slot_data

        # 2. Manage slot_bookings for this date
        booking = db.execute(
            text("SELECT booking_id, booked_count FROM slot_bookings WHERE slot_id = :slot_id AND booking_date = :appointment_date"),
            {"slot_id": slot_id, "appointment_date": appointment_date}
        ).fetchone()

        if booking:
            booking_id, current_count = booking
            if current_count >= max_apps:
                raise HTTPException(status_code=400, detail="Slot fully booked for this date")
            
            # Increment count
            db.execute(
                text("UPDATE slot_bookings SET booked_count = booked_count + 1 WHERE booking_id = :booking_id"),
                {"booking_id": booking_id}
            )
            new_queue_num = current_count + 1
        else:
            # Create new booking record
            result = db.execute(
                text("INSERT INTO slot_bookings (slot_id, booking_date, booked_count) VALUES (:slot_id, :appointment_date, 1) RETURNING booking_id"),
                {"slot_id": slot_id, "appointment_date": appointment_date}
            )
            booking_id = result.fetchone()[0]
            new_queue_num = 1

        # 3. Create the appointment
        insert_query = text(
            """
            INSERT INTO appointments (patient_id, doctor_id, slot_id, status, appointment_date, slot_booking_id, queue_number, expected_time)
            VALUES (:patient_id, :doctor_id, :slot_id, :status, :appointment_date, :booking_id, :queue_num, :exp_time)
            RETURNING appointment_id
        """
        )

        result = db.execute(
            insert_query,
            {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "slot_id": slot_id,
                "status": AppointmentStatus.PENDING,
                "appointment_date": appointment_date,
                "booking_id": booking_id,
                "queue_num": new_queue_num,
                "exp_time": start_time,
            },
        )

        appointment_id = result.fetchone()[0]
        db.commit()

        return {
            "status": "success",
            "appointment_id": appointment_id,
            "message": "Appointment booked successfully",
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patient_history")
def get_patient_history(patient_id: int, db: Session = Depends(get_db)):
    medical = db.execute(
        text(
            """
        SELECT 
            allergies,
            blood_group,
            chronic_conditions,
            current_medications,
            last_updated
        FROM medical_history
        WHERE patient_id = :patient_id
    """
        ),
        {"patient_id": patient_id},
    ).fetchone()

    medical_history = dict(medical._mapping) if medical else {}

    visits = db.execute(
        text(
            """
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.status,
            d.full_name AS doctor_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = :patient_id
        ORDER BY a.appointment_date DESC
    """
        ),
        {"patient_id": patient_id},
    ).fetchall()

    visiting_history = [dict(row._mapping) for row in visits]

    return {
        "status": "success",
        "medical_history": medical_history,
        "visiting_history": visiting_history,
        "total_visits": len(visiting_history),
    }

@router.get("/patient_full_data")
def get_patient_full_data(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = db.execute(text("""
        SELECT * FROM patients
        WHERE patient_id = :patient_id
    """), {"patient_id": patient_id}).fetchone()

    if not patient:
        return {"status": "error", "message": "Patient not found"}

    patient_info = dict(patient._mapping)

    medical_history = db.execute(text("""
        SELECT * FROM medical_history
        WHERE patient_id = :patient_id
    """), {"patient_id": patient_id}).fetchone()

    medical_history = dict(medical_history._mapping) if medical_history else {}

    appointments = db.execute(text("""
        SELECT 
            a.*,
            d.full_name AS doctor_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = :patient_id
        ORDER BY a.appointment_date DESC
    """), {"patient_id": patient_id}).fetchall()

    appointments_list = [dict(row._mapping) for row in appointments]

    consultations = db.execute(text("""
        SELECT c.*
        FROM consultation_records c
        JOIN appointments a ON c.appointment_id = a.appointment_id
        WHERE a.patient_id = :patient_id
        ORDER BY c.record_id DESC
    """), {"patient_id": patient_id}).fetchall()

    consultations_list = [dict(row._mapping) for row in consultations]

    prechecks = db.execute(text("""
        SELECT m.*
        FROM medical_prechecks m
        JOIN appointments a ON m.appointment_id = a.appointment_id
        WHERE a.patient_id = :patient_id
        ORDER BY m.check_id DESC
    """), {"patient_id": patient_id}).fetchall()

    prechecks_list = [dict(row._mapping) for row in prechecks]

    return {
        "status": "success",
        "patient": patient_info,
        "medical_history": medical_history,
        "appointments": appointments_list,
        "consultations": consultations_list,
        "prechecks": prechecks_list
    }