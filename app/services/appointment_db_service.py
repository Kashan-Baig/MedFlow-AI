from sqlalchemy import text
from app.database.db_connection import get_db


def create_appointment(patient_id, doctor_id, slot_id):

    db = get_db()   # ✅ FIXED

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
            "status": "confirmed",
            "case_type": "CONSULTATION"
        })

        appointment_id = result.fetchone()[0]

        db.commit()
        return appointment_id

    finally:
        db.close()