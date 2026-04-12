# =========================
# DOCTOR DATA
# =========================
doctors = [
    {
        "id": 1,
        "name": "Dr. Kashan",
        "speciality": ["Cardiologist","General Physician","General Practitioner"],
        "available_days": ["Monday", "Wednesday"],
        "time_slots": ["10:00 AM - 11:00 AM", "2:00 PM - 3:00 PM"]
    },
    {
        "id": 2,
        "name": "Dr. Sara",
        "speciality": ["Dermatologist","General Physician","General Practitioner"],
        "available_days": ["Tuesday", "Thursday"],
        "time_slots": ["11:00 AM - 12:00 PM", "3:00 PM - 4:00 PM"]
    },
    {
        "id": 3,
        "name": "Dr. Adnan",
        "speciality": ["Neurologist","General Physician","General Practitioner"],
        "available_days": ["Monday", "Friday"],
        "time_slots": ["9:00 AM - 10:00 AM", "1:00 PM - 2:00 PM"]
    },
    {
        "id": 4,
        "name": "Dr. Ayan",
        "speciality": ["General Physician""General Practitioner"],
        "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_slots": ["10:00 AM - 11:00 AM", "12:00 PM - 1:00 PM", "4:00 PM - 5:00 PM"]
    }
]

def find_available_doctor(speciality, day, time_slot):

    for doctor in doctors:
        if speciality in doctor["speciality"]:
            if day in doctor["available_days"] and time_slot in doctor["time_slots"]:
                return doctor

    # fallback
    for doctor in doctors:
        if "General Physician" in doctor["speciality"]:
            if day in doctor["available_days"] and time_slot in doctor["time_slots"]:
                return doctor

    return None
