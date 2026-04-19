from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database.models import Appointment, ScheduleSlot, AppointmentStatus

# =========================
# UTIL: CAN BOOK APPOINTMENT
# =========================

def can_book_appointment(db, slot_id, target_date):
    # 1. Get the max capacity for this slot
    slot = db.query(ScheduleSlot).filter(ScheduleSlot.slot_id == slot_id).first()
    
    # 2. Count existing appointments for this slot on this specific date
    booked_count = db.query(Appointment).filter(
        Appointment.slot_id == slot_id,
        Appointment.appointment_date == target_date,
        Appointment.status != AppointmentStatus.CANCELLED # Don't count cancelled ones
    ).count()
    
    return booked_count < slot.max_appointments


def create_appointment(patient_id, doctor_id, slot_id, target_date):

    db = get_db()
    if not can_book_appointment(db, slot_id, target_date):
        return "Slot is already full"
    try:
        query = text("""
            INSERT INTO appointments 
            (patient_id, doctor_id, slot_id, appointment_date, status, case_type)
            VALUES (:patient_id, :doctor_id, :slot_id, :appointment_date, :status, :case_type)
            RETURNING appointment_id;
        """)

        result = db.execute(query, {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "slot_id": slot_id,
            "appointment_date": target_date,
            "status": "CONFIRMED",
            "case_type": "CONSULTATION"
        })

        appointment_id = result.fetchone()[0]

        db.commit()
        return appointment_id

    finally:
        db.close()

def get_appointments_by_patient_id(patient_id):
    db = get_db()
    try:
        query = text("""
            SELECT 
                a.appointment_id,
                a.status,
                a.case_type,
                a.appointment_date,
                ss.start_time,     
                d.name AS doctor_name,
                d.specialization AS doctor_specialization,
                p.full_name AS patient_name
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN schedule_slots ss ON a.slot_id = ss.slot_id
            WHERE a.patient_id = :patient_id
            ORDER BY a.appointment_id DESC ;
        """)
        result = db.execute(query, {"patient_id": patient_id}).fetchall()
        return [dict(row._mapping) for row in result] 
        #QLAlchemy returns the rows as special "Row" tuple objects, and FastAPI doesn't know how to turn those raw tuples into JSON when they're wrapped in your custom dictionary
        # DID THIS AS I WAS RETURNING THIS EXACT THING IN RESPONSE 
    finally:
        db.close()  