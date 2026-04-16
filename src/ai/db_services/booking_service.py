from src.ai.utils.session_store import get_session, update_appointment
from datetime import datetime, timedelta
import json, re

from src.ai.db_services.appointment_db_service import create_appointment
from src.ai.db_services.doctor_service import get_doctors_by_speciality_and_day


# =========================
# UTIL: DATE FROM DAY
# =========================
def get_next_date_for_day(day_name: str):
    days_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    today = datetime.now()
    target_day = days_map[day_name]

    days_ahead = target_day - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    return (today + timedelta(days=days_ahead)).date()


# =========================
# UTIL: PARSE INSIGHT
# =========================
def parse_insight(insight):
    if isinstance(insight, str):
        try:
            match = re.search(r"```(?:json)?\n?(.*?)```", insight, re.DOTALL)
            raw = match.group(1) if match else insight
            return json.loads(raw)
        except:
            return {}
    return insight if isinstance(insight, dict) else {}


# =========================
# NORMALIZE SPECIALITY
# =========================
def normalize_speciality(text):
    if not text:
        return "General Physician"

    text = text.lower().replace("-", " ").strip()
    return text.split("/")[0].title()


# =========================
# MAIN BOOKING FUNCTION
# =========================
def book_appointment(session_id, insight):

    session = get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    insight = parse_insight(insight)

    speciality = normalize_speciality(
        insight.get("primary_specialist")
        or insight.get("recommended_specialist")
        or insight.get("specialist")
        or "General Physician"
    )

    print(f"\n🩺 Recommended Specialist: {speciality}")

    next_days = [
        (datetime.now() + timedelta(days=i)).strftime("%A")
        for i in range(7)
    ]

    # Precompute dates (optimization)
    day_date_map = {
        day: get_next_date_for_day(day)
        for day in next_days
    }

    slot_map = []
    print("\n📅 Available Slots (Next 7 Days):\n")

    count = 1

    for day in next_days:


        available_doctors = get_doctors_by_speciality_and_day(speciality, day)


        for doc in available_doctors:
            date = day_date_map[day]

            # IMPORTANT FIX: use DB arrays directly (safe loop)
            for i in range(len(doc["time_slots"])):
                slot_id = doc["slot_ids"][i]
                time_slot = doc["time_slots"][i]

                slot_map.append({
                    "doctor": doc,
                    "day": day,
                    "date": date,
                    "time_slot": time_slot,
                    "slot_id": slot_id
                })

                print(
                    f"{count}. {day} ({date}) - {time_slot} - {doc['name']}"
                )
                count += 1

    if not slot_map:
        return {"error": f"No slots available for {speciality}"}

    # =========================
    # USER SELECTION
    # =========================
    choice = input("\n👉 Select slot number: ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(slot_map)):
        return {"error": "Invalid slot selection"}

    selected = slot_map[int(choice) - 1]

    doctor = selected["doctor"]
    day = selected["day"]
    date = selected["date"]
    time_slot = selected["time_slot"]
    slot_id = selected["slot_id"]

    print("\n👨‍⚕️ Appointment Details:")
    print(f"Doctor: {doctor['name']}")
    print(f"Speciality: {speciality}")
    print(f"Day: {day}")
    print(f"Date: {date}")
    print(f"Time: {time_slot}")
    print(f"Slot ID: {slot_id}")

    confirm = input("\n✅ Confirm appointment? (yes/no): ").lower()

    if confirm not in ["yes", "y"]:
        return {"error": "Appointment cancelled"}

    # =========================
    # FINAL VALIDATION
    # =========================
    patient_id = session.get("patient_id")

    if not patient_id:
        return {"error": "Patient ID not found in session"}

    # =========================
    # CREATE APPOINTMENT
    # =========================
    appointment_id = create_appointment(
        patient_id=patient_id,
        doctor_id=doctor["id"],
        slot_id=slot_id
    )

    appointment_data = {
        "appointment_id": appointment_id,
        "doctor": doctor["name"],
        "speciality": speciality,
        "day": day,
        "date": str(date),
        "time_slot": time_slot,
        "status": "confirmed"
    }

    update_appointment(session_id, appointment_data)

    return appointment_data