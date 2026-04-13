from sqlalchemy import text
from src.backend.database.db_connection import get_db

def create_patient_if_not_exists(patient):
    db = get_db()

    try:
        # 1️⃣ Try insert
        insert_query = text("""
            INSERT INTO patients (full_name, email, contact_number, age, gender)
            VALUES (:full_name, :email, :contact_number, :age, :gender)
            ON CONFLICT (email) DO NOTHING
            RETURNING patient_id;
        """)

        result = db.execute(insert_query, {
            "full_name": patient.name,
            "email": patient.email,
            "contact_number": patient.phone,
            "age": patient.age,
            "gender": patient.gender
        })

        row = result.fetchone()

        if row:
            db.commit()
            return row[0]

        # 2️⃣ If already exists → fetch it
        select_query = text("""
            SELECT patient_id FROM patients WHERE email = :email
        """)

        existing = db.execute(select_query, {
            "email": patient.email
        }).fetchone()

        db.commit()

        return existing[0] if existing else None

    finally:
        db.close()

