from app.utils.doctor_store import doctors

def get_doctors_by_speciality_and_day(speciality, day):
    available_doctors = [
        d for d in doctors
        if any(s.lower() == speciality.lower() for s in d.get("speciality", []))
        and any(dy.lower() == day.lower() for dy in d.get("available_days", []))
    ]
    return available_doctors