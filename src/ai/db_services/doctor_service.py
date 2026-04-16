from sqlalchemy import text
from src.backend.database.db_connection import get_db


def get_doctors_by_speciality_and_day(speciality, day):
    db = get_db()
    try:
        query = text("""
        SELECT 
            d.doctor_id AS id,
            d.name,
            d.specialization AS speciality,
            ss.available_days,
            CONCAT(
                TO_CHAR(ss.start_time, 'HH12:MI AM'),
                ' - ',
                TO_CHAR(ss.end_time, 'HH12:MI AM')
            ) AS time_slot,
            ss.slot_id
        FROM doctors d
        JOIN schedule_slots ss ON ss.doctor_id = d.doctor_id
        WHERE
            LOWER(d.specialization) = LOWER(:speciality)
            AND :day = ANY(ss.available_days)
            AND ss.is_locked = FALSE
        ORDER BY ss.start_time;
        """)

        rows = db.execute(query, {
            "speciality": speciality,
            "day": day
        }).fetchall()

        doctor_map = {}

        for row in rows:
            doc_id = row[0]

            if doc_id not in doctor_map:
                doctor_map[doc_id] = {
                    "id": row[0],
                    "name": row[1],
                    "speciality": row[2],
                    "available_days": row[3],   
                    "time_slots": [],
                    "slot_ids": []
                }

            doctor_map[doc_id]["time_slots"].append(row[4])
            doctor_map[doc_id]["slot_ids"].append(row[5])

        return list(doctor_map.values())

    finally:
        db.close()