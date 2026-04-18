from sqlalchemy import text
from src.backend.database.db_connection import get_db


def get_doctors_by_speciality(speciality, from_doctor_router=False):
    db = get_db()
    try:
        query = text(
            """
        SELECT 
            d.doctor_id AS id,
            d.name,
            d.specialization AS speciality,
            ss.available_days::text[],
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
            AND ss.is_locked = FALSE
        ORDER BY ss.start_time;
        """
        )

        rows = db.execute(query, {"speciality": speciality}).fetchall()

        if from_doctor_router:
            doctors_map = {}
            for row in rows:
                doc_id = row[0]
                doc_name = row[1]
                doc_speciality = row[2]
                available_days = row[3]

                if isinstance(available_days, str):
                    _stripped = available_days.strip("{}[] ")
                    available_days = [
                        d.strip("\"' ") for d in _stripped.split(",") if d.strip("\"' ")
                    ]

                time_slot = row[4]
                slot_id = row[5]

                if doc_id not in doctors_map:
                    doctors_map[doc_id] = {
                        "id": doc_id,
                        "name": doc_name,
                        "speciality": doc_speciality,
                        "available_days": available_days,
                        "time_slots": [],
                        "slot_ids": [],
                    }

                doctors_map[doc_id]["time_slots"].append(time_slot)
                doctors_map[doc_id]["slot_ids"].append(slot_id)

            return list(doctors_map.values())
        else:
            days = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            daily_map = {day: {} for day in days}

            for row in rows:
                doc_id = row[0]
                doc_name = row[1]
                doc_speciality = row[2]
                available_days = row[3]

                if isinstance(available_days, str):
                    _stripped = available_days.strip("{}[] ")
                    available_days = [
                        d.strip("\"' ") for d in _stripped.split(",") if d.strip("\"' ")
                    ]

                time_slot = row[4]
                slot_id = row[5]

                for day in available_days:
                    if day in daily_map:
                        if doc_id not in daily_map[day]:
                            daily_map[day][doc_id] = {
                                "id": doc_id,
                                "name": doc_name,
                                "speciality": doc_speciality,
                                "available_days": available_days,
                                "time_slots": [],
                                "slot_ids": [],
                            }

                        daily_map[day][doc_id]["time_slots"].append(time_slot)
                        daily_map[day][doc_id]["slot_ids"].append(slot_id)

            for day in daily_map:
                daily_map[day] = list(daily_map[day].values())

            return daily_map

    finally:
        db.close()


def get_patients_by_doctor_id(doctor_id):
    db = get_db()
    try:
        query = text(
            """
            SELECT 
                p.patient_id,
                p.full_name,
                p.email,
                p.contact_number as phone,
                p.gender,
                p.age,
                a.appointment_id,
                a.appointment_date,
                ss.start_time as appointment_time,
                a.status,
                mp.patient_symptoms as symptoms,
                cr.diagnosis as diagnosis,
                cr.prescribed_actions as prescription
            FROM appointments a
            JOIN patients p ON p.patient_id = a.patient_id
            JOIN schedule_slots ss ON a.slot_id = ss.slot_id
            LEFT JOIN medical_prechecks mp ON a.appointment_id = mp.appointment_id
            LEFT JOIN consultation_records cr ON a.appointment_id = cr.appointment_id
            WHERE a.doctor_id = :doctor_id
            ORDER BY a.appointment_date DESC;
        """
        )
        result = db.execute(query, {"doctor_id": doctor_id}).fetchall()
        print(type(result))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()
