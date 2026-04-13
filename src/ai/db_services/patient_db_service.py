from sqlalchemy import text
from src.backend.database.db_connection import get_db

def create_patient_if_not_exists(patient):
    db = get_db()

    query = text("""
        INSERT INTO patients (full_name, email, contact_number, age, gender)
        VALUES (:full_name, :email, :contact_number, :age, :gender)
        ON CONFLICT (email) DO NOTHING
        RETURNING patient_id;
    """)

    result = db.execute(query, {
        "full_name": patient.name,
        "email": patient.email,
        "contact_number": patient.phone,
        "age": patient.age,
        "gender": patient.gender
    })

    db.commit()

    row = result.fetchone()
    return row[0] if row else None