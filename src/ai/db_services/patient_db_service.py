from sqlalchemy import text
from src.backend.database.db_connection import get_db

def get_patient_by_user_id(user_id):
    """
    Fetch patient record by user_id from patients table
    """
    db = get_db()

    try:
        query = text("""
            SELECT patient_id, full_name, email, age, gender, contact_number 
            FROM patients 
            WHERE user_id = :user_id
        """)

        result = db.execute(query, {"user_id": user_id}).fetchone()

        if result:
            return {
                "id": result[0],
                "name": result[1],
                "email": result[2],
                "age": result[3],
                "gender": result[4],
                "phone": result[5]
            }

        return None

    except Exception as e:
        print(f"Error fetching patient: {str(e)}")
        return None

    finally:
        db.close()

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

