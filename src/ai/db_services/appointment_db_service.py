from sqlalchemy import text
from src.backend.database.db_connection import get_db
from src.backend.database.models import AppointmentStatus, CaseType


def create_appointment(patient_id, doctor_id, slot_id):
    db = get_db()
    try:
        query = text("""
            INSERT INTO appointments 
            (patient_id, doctor_id, slot_id, status, case_type)
            VALUES (:patient_id, :doctor_id, :slot_id, :status, :case_type)
            RETURNING appointment_id;
        """)

        result = db.execute(query, {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "slot_id": slot_id,
            "status": AppointmentStatus.CONFIRMED.name,
            "case_type": CaseType.CONSULTATION.name,
        })

        appointment_id = result.fetchone()[0]

        db.commit()
        return appointment_id

    finally:
        db.close()