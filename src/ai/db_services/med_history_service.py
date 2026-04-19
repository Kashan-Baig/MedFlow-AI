from sqlalchemy import text
from src.backend.database.db_connection import get_db


def get_medical_history(patient_id: int):
    db = get_db()

    try:
        query = text("""
            SELECT 
                allergies,
                blood_group,
                chronic_conditions,
                current_medications,
                last_updated
            FROM medical_history
            WHERE patient_id = :patient_id
        """)

        result = db.execute(query, {"patient_id": patient_id}).fetchone()

        if not result:
            return {
                "patient_id": patient_id,
                "allergies": [],
                "blood_group": None,
                "chronic_conditions": [],
                "current_medications": [],
                "last_updated": None
            }

        return {
            "patient_id": patient_id,
            "allergies": result[0] or [],
            "blood_group": result[1],
            "chronic_conditions": result[2] or [],
            "current_medications": result[3] or [],
            "last_updated": str(result[4]) if result[4] else None
        }

    except Exception as e:
        print(f"❌ Error fetching medical history: {str(e)}")
        return {}

    finally:
        db.close()