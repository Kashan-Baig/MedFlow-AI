from sqlalchemy import text
from src.backend.database.db_connection import get_db
import json


def save_consultation_record(appointment_id, insight, response):

    db = get_db()   # ✅ FIXED

    try:
        query = text("""
            INSERT INTO consultation_records
            (appointment_id, observations, diagnosis, prescribed_actions)
            VALUES (:appointment_id, :observations, :diagnosis, :actions)
            RETURNING record_id;
        """)

        result = db.execute(query, {
            "appointment_id": appointment_id,
            "observations": response,
            "diagnosis": json.dumps(insight),  # ✅ store JSON safely
            "actions": "Follow AI advice and consult doctor"
        })

        record_id = result.fetchone()[0]

        db.commit()
        return record_id

    finally:
        db.close()